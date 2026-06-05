"""
Module 5 - Lesson 1: Watermark-Based Incremental Extraction
=============================================================
Full-load ETL reads ALL source data on every run — expensive and slow at scale.
Watermark-based extraction solves this by remembering the highest value seen
in a monotonically increasing column (usually a timestamp or auto-increment ID)
and only fetching rows that are NEWER than that value on subsequent runs.

This is the most common incremental pattern in real production pipelines.

Core concepts:
  - Watermark column: a column guaranteed to increase over time (updated_at, id)
  - Watermark state: the last known maximum value, persisted across runs
  - High-water mark: extract WHERE watermark_col > last_watermark
  - State table: a dedicated SQLite table to persist watermark values per pipeline

Topics covered:
  1. Creating and seeding a source database from CSV
  2. A pipeline_state table to persist watermarks
  3. First run — full extraction (no prior watermark)
  4. Subsequent runs — incremental extraction using the stored watermark
  5. Simulating new/updated records arriving in the source
  6. Safety margin: using a small lookback buffer to avoid missing late-arriving rows
"""

import logging
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
MODULE_DIR = Path(__file__).parent
DATA_DIR   = MODULE_DIR / "data"
DB_PATH    = MODULE_DIR / "watermark_demo.db"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("etl.watermark")


# =============================================================================
# 1. DATABASE SETUP HELPERS
# =============================================================================

def get_engine(db_path: Path = DB_PATH):
    """Return a SQLAlchemy engine for the demo SQLite database."""
    return create_engine(f"sqlite:///{db_path}", echo=False)


def setup_source_table(engine) -> None:
    """
    Create and populate the source orders table from the CSV file.
    Dropped and recreated each run so the demo is self-contained.
    """
    df = pd.read_csv(DATA_DIR / "source_orders.csv", parse_dates=["created_at", "updated_at"])
    df.to_sql("source_orders", con=engine, if_exists="replace", index=False)
    logger.info("Source table created with %d rows.", len(df))


def setup_state_table(engine) -> None:
    """
    Create the pipeline_state table if it doesn't already exist.

    Schema:
        pipeline_name  TEXT PRIMARY KEY  -- unique identifier for the pipeline
        watermark_col  TEXT              -- which column is the watermark
        watermark_val  TEXT              -- last extracted value (stored as ISO string)
        last_run_at    TEXT              -- when the pipeline last ran successfully
        rows_extracted INTEGER           -- how many rows were extracted last run
    """
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS pipeline_state (
                pipeline_name  TEXT PRIMARY KEY,
                watermark_col  TEXT NOT NULL,
                watermark_val  TEXT,
                last_run_at    TEXT,
                rows_extracted INTEGER DEFAULT 0
            )
        """))
    logger.info("pipeline_state table ready.")


# =============================================================================
# 2. WATERMARK HELPERS
# =============================================================================

def get_watermark(engine, pipeline_name: str) -> str | None:
    """
    Read the current watermark for a given pipeline.

    Returns:
        ISO-format timestamp string, or None if this is the first run.
    """
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT watermark_val FROM pipeline_state WHERE pipeline_name = :name"),
            {"name": pipeline_name},
        ).fetchone()
    return row[0] if row else None


def save_watermark(
    engine,
    pipeline_name: str,
    watermark_col: str,
    watermark_val: str,
    rows_extracted: int,
) -> None:
    """
    Persist the new watermark value after a successful extraction.

    Uses INSERT OR REPLACE so it works for both first run and subsequent runs.
    """
    now = datetime.now(timezone.utc).isoformat()
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO pipeline_state
                    (pipeline_name, watermark_col, watermark_val, last_run_at, rows_extracted)
                VALUES
                    (:name, :col, :val, :now, :rows)
                ON CONFLICT(pipeline_name) DO UPDATE SET
                    watermark_col  = excluded.watermark_col,
                    watermark_val  = excluded.watermark_val,
                    last_run_at    = excluded.last_run_at,
                    rows_extracted = excluded.rows_extracted
            """),
            {
                "name": pipeline_name,
                "col":  watermark_col,
                "val":  watermark_val,
                "now":  now,
                "rows": rows_extracted,
            },
        )
    logger.info(
        "Watermark saved: pipeline=%s  col=%s  val=%s  rows=%d",
        pipeline_name, watermark_col, watermark_val, rows_extracted,
    )


# =============================================================================
# 3. INCREMENTAL EXTRACTION
# =============================================================================

LOOKBACK_SECONDS = 5  # safety buffer to catch late-arriving rows


def extract_incremental(
    engine,
    pipeline_name: str,
    watermark_col: str = "updated_at",
    table: str = "source_orders",
) -> pd.DataFrame:
    """
    Extract only the rows that are newer than the stored watermark.

    On first run (no watermark) — reads ALL rows.
    On subsequent runs    — reads only rows where watermark_col > last_watermark
                            minus a small lookback buffer.

    Args:
        engine:         SQLAlchemy engine connected to the source DB.
        pipeline_name:  Unique name for this pipeline (used to look up state).
        watermark_col:  Column used as the watermark (must be monotonically increasing).
        table:          Source table name.

    Returns:
        DataFrame containing only the new/changed rows.
    """
    last_watermark = get_watermark(engine, pipeline_name)

    if last_watermark is None:
        # ── First run: full extraction ──────────────────────────────────────
        logger.info("No watermark found — performing full extraction.")
        query = f"SELECT * FROM {table} ORDER BY {watermark_col}"
        df = pd.read_sql(query, con=engine, parse_dates=[watermark_col])
    else:
        # ── Incremental run ──────────────────────────────────────────────────
        # Apply a lookback buffer to catch rows that arrived slightly late
        # (e.g., clock skew between source systems).
        watermark_dt = datetime.fromisoformat(last_watermark)
        safe_watermark = (watermark_dt - timedelta(seconds=LOOKBACK_SECONDS)).isoformat()

        logger.info(
            "Watermark found: %s — extracting rows where %s > '%s'",
            last_watermark, watermark_col, safe_watermark,
        )
        query = f"""
            SELECT * FROM {table}
            WHERE {watermark_col} > :wm
            ORDER BY {watermark_col}
        """
        df = pd.read_sql(
            text(query),
            con=engine,
            params={"wm": safe_watermark},
            parse_dates=[watermark_col],
        )

    logger.info("Extracted %d rows.", len(df))
    return df


# =============================================================================
# 4. DEMO: RUNNING THE PIPELINE MULTIPLE TIMES
# =============================================================================

PIPELINE_NAME   = "orders_incremental"
WATERMARK_COL   = "updated_at"

def run_extraction_pipeline(engine, label: str) -> pd.DataFrame:
    """Run one extraction cycle and update the watermark on success."""
    print(f"\n{'=' * 60}")
    print(f"  {label}")
    print(f"{'=' * 60}")

    df = extract_incremental(engine, PIPELINE_NAME, WATERMARK_COL)

    if df.empty:
        logger.info("Nothing new to extract.")
        return df

    # Update the watermark to the maximum value seen in this batch
    new_watermark = df[WATERMARK_COL].max().isoformat()
    save_watermark(engine, PIPELINE_NAME, WATERMARK_COL, new_watermark, len(df))

    print(df[["order_id", "customer_id", "product", "amount", "status", WATERMARK_COL]].to_string(index=False))
    return df


def simulate_new_orders(engine, new_rows: list[dict]) -> None:
    """
    Insert new/updated rows into the source table to simulate an
    active source system generating data between pipeline runs.
    """
    df_new = pd.DataFrame(new_rows)
    df_new.to_sql("source_orders", con=engine, if_exists="append", index=False)
    logger.info("Simulated %d new/updated rows in source.", len(new_rows))


# ---------------------------------------------------------------------------
# Main execution
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Clean slate for the demo
    if DB_PATH.exists():
        DB_PATH.unlink()

    engine = get_engine()
    setup_source_table(engine)
    setup_state_table(engine)

    # ── Run 1: First run — no watermark, full extraction ────────────────────
    run_extraction_pipeline(engine, "RUN 1: First run (full extraction)")

    # ── Simulate new orders arriving in the source system ───────────────────
    simulate_new_orders(engine, [
        {
            "order_id":    51,
            "customer_id": "C011",
            "product":     "Tablet",
            "amount":      499.00,
            "status":      "pending",
            "created_at":  "2024-01-26 08:00:00",
            "updated_at":  "2024-01-26 08:00:00",
        },
        {
            "order_id":    52,
            "customer_id": "C012",
            "product":     "SSD",
            "amount":      120.00,
            "status":      "completed",
            "created_at":  "2024-01-26 09:00:00",
            "updated_at":  "2024-01-26 09:00:00",
        },
    ])

    # ── Run 2: Incremental — should only pick up 2 new rows ─────────────────
    run_extraction_pipeline(engine, "RUN 2: Incremental (only new rows)")

    # ── Run 3: No new data — should extract 0 rows ──────────────────────────
    run_extraction_pipeline(engine, "RUN 3: No new data (0 rows expected)")

    # ── Simulate a status update on an existing order ───────────────────────
    # In a real system, updated_at changes whenever a record is modified.
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE source_orders SET status='completed', updated_at='2024-01-27 10:00:00' WHERE order_id=51")
        )
    logger.info("Simulated update: order_id=51 status → completed")

    # ── Run 4: Should pick up the 1 updated row ──────────────────────────────
    run_extraction_pipeline(engine, "RUN 4: Updated row detected")

    # ── Show final pipeline state ─────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print("  FINAL PIPELINE STATE")
    print(f"{'=' * 60}")
    state_df = pd.read_sql("SELECT * FROM pipeline_state", con=engine)
    print(state_df.to_string(index=False))

    print("\nDone. Database saved to:", DB_PATH)
