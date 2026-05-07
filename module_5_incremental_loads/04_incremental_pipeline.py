"""
Module 5 - Lesson 4: Full Incremental Pipeline
================================================
This lesson ties together everything from the module into one cohesive,
production-style incremental pipeline:

  Extract  → Watermark-based extraction (only new/changed rows)
  Transform → Basic cleansing and enrichment
  Load     → Staged MERGE upsert into the target table
  State    → Watermark updated in pipeline_state after successful load
  Audit    → Every run is recorded in a pipeline_run_log table

The pipeline is designed to be:
  - Idempotent:     safe to re-run without duplicating data
  - Restartable:    a failed run leaves the watermark unchanged;
                    the next run will re-process the same batch
  - Observable:     every run writes a row to pipeline_run_log with
                    start time, end time, rows extracted, rows loaded,
                    watermark before/after, and status

Topics covered:
  1. Assembling extract → transform → load into a single pipeline function
  2. Transactional watermark update (only advances on success)
  3. Audit log table and run recording
  4. Simulating multiple pipeline runs with new data arriving between runs
  5. Querying the audit log to review pipeline history
"""

import logging
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
MODULE_DIR = Path(__file__).parent
DATA_DIR   = MODULE_DIR / "data"
DB_PATH    = MODULE_DIR / "incremental_pipeline.db"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("etl.incremental_pipeline")

# Pipeline identity
PIPELINE_NAME  = "orders_incremental_pipeline"
WATERMARK_COL  = "updated_at"
SOURCE_TABLE   = "source_orders"
TARGET_TABLE   = "target_orders"
LOOKBACK_SECS  = 5   # safety buffer for late-arriving rows


# =============================================================================
# 1. DATABASE SETUP
# =============================================================================

def get_engine(db_path: Path = DB_PATH):
    return create_engine(f"sqlite:///{db_path}", echo=False)


def setup_all_tables(engine) -> None:
    """Create source, target, state, and audit tables."""
    with engine.begin() as conn:

        # ── Source table (simulates an upstream system) ──────────────────────
        conn.execute(text(f"DROP TABLE IF EXISTS {SOURCE_TABLE}"))
        conn.execute(text(f"""
            CREATE TABLE {SOURCE_TABLE} (
                order_id    INTEGER PRIMARY KEY,
                customer_id TEXT    NOT NULL,
                product     TEXT    NOT NULL,
                amount      REAL    NOT NULL,
                status      TEXT    NOT NULL,
                created_at  TEXT    NOT NULL,
                updated_at  TEXT    NOT NULL
            )
        """))

        # ── Target table (our curated analytical store) ───────────────────────
        conn.execute(text(f"DROP TABLE IF EXISTS {TARGET_TABLE}"))
        conn.execute(text(f"""
            CREATE TABLE {TARGET_TABLE} (
                order_id          INTEGER PRIMARY KEY,
                customer_id       TEXT    NOT NULL,
                product           TEXT    NOT NULL,
                amount            REAL    NOT NULL,
                status            TEXT    NOT NULL,
                amount_category   TEXT,          -- derived column added in Transform
                created_at        TEXT    NOT NULL,
                updated_at        TEXT    NOT NULL,
                _pipeline_loaded  TEXT    NOT NULL  -- audit: when ETL wrote this row
            )
        """))

        # ── Pipeline state table ──────────────────────────────────────────────
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS pipeline_state (
                pipeline_name  TEXT PRIMARY KEY,
                watermark_col  TEXT NOT NULL,
                watermark_val  TEXT,
                last_run_at    TEXT,
                rows_extracted INTEGER DEFAULT 0
            )
        """))

        # ── Audit / run log table ─────────────────────────────────────────────
        conn.execute(text("DROP TABLE IF EXISTS pipeline_run_log"))
        conn.execute(text("""
            CREATE TABLE pipeline_run_log (
                run_id            INTEGER PRIMARY KEY AUTOINCREMENT,
                pipeline_name     TEXT    NOT NULL,
                started_at        TEXT    NOT NULL,
                finished_at       TEXT,
                status            TEXT    NOT NULL DEFAULT 'running',  -- running | success | failed
                watermark_before  TEXT,
                watermark_after   TEXT,
                rows_extracted    INTEGER DEFAULT 0,
                rows_loaded       INTEGER DEFAULT 0,
                error_message     TEXT
            )
        """))

    logger.info("All tables created.")


def seed_source(engine) -> None:
    """Populate the source table from the CSV file."""
    df = pd.read_csv(DATA_DIR / "source_orders.csv", parse_dates=["created_at", "updated_at"])
    df.to_sql(SOURCE_TABLE, con=engine, if_exists="append", index=False)
    logger.info("Source seeded with %d rows.", len(df))


# =============================================================================
# 2. EXTRACT (watermark-based)
# =============================================================================

def extract(engine, watermark_before: str | None) -> pd.DataFrame:
    """
    Extract rows from source that are newer than the current watermark.

    Returns an empty DataFrame if nothing is new.
    """
    if watermark_before is None:
        logger.info("EXTRACT: No watermark — full extraction.")
        query = f"SELECT * FROM {SOURCE_TABLE} ORDER BY {WATERMARK_COL}"
        df = pd.read_sql(query, con=engine, parse_dates=[WATERMARK_COL, "created_at"])
    else:
        watermark_dt  = datetime.fromisoformat(watermark_before)
        safe_watermark = (watermark_dt - timedelta(seconds=LOOKBACK_SECS)).isoformat()
        logger.info("EXTRACT: Fetching rows where %s > '%s'", WATERMARK_COL, safe_watermark)
        query = f"SELECT * FROM {SOURCE_TABLE} WHERE {WATERMARK_COL} > :wm ORDER BY {WATERMARK_COL}"
        df = pd.read_sql(
            text(query),
            con=engine,
            params={"wm": safe_watermark},
            parse_dates=[WATERMARK_COL, "created_at"],
        )

    logger.info("EXTRACT: %d rows extracted.", len(df))
    return df


# =============================================================================
# 3. TRANSFORM
# =============================================================================

def transform(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply cleansing and enrichment rules to the extracted data.

    Transformations:
      - Normalise status to lowercase
      - Derive amount_category from amount value
      - Add _pipeline_loaded timestamp (when this ETL run processed the record)
    """
    if df.empty:
        return df

    df = df.copy()

    # Normalise status
    df["status"] = df["status"].str.lower().str.strip()

    # Derived column: amount category
    df["amount_category"] = pd.cut(
        df["amount"],
        bins=[0, 50, 200, 600, float("inf")],
        labels=["low", "medium", "high", "premium"],
        right=True,
    ).astype(str)

    # Audit column
    df["_pipeline_loaded"] = datetime.now(timezone.utc).isoformat()

    logger.info("TRANSFORM: %d rows transformed.", len(df))
    return df


# =============================================================================
# 4. LOAD (staged merge upsert)
# =============================================================================

def load(engine, df: pd.DataFrame) -> int:
    """
    Upsert transformed rows into the target table using a staging table.

    Uses the same STAGED MERGE pattern from Lesson 2:
      - UPDATE changed rows
      - INSERT new rows
      - Never delete (append-only target for analytical queries)

    Returns:
        Total rows affected (inserted + updated).
    """
    if df.empty:
        return 0

    staging = f"{TARGET_TABLE}_staging"
    df.to_sql(staging, con=engine, if_exists="replace", index=False)

    with engine.begin() as conn:
        result_upd = conn.execute(text(f"""
            UPDATE {TARGET_TABLE}
            SET customer_id      = s.customer_id,
                product          = s.product,
                amount           = s.amount,
                status           = s.status,
                amount_category  = s.amount_category,
                updated_at       = s.updated_at,
                _pipeline_loaded = s._pipeline_loaded
            FROM {staging} AS s
            WHERE {TARGET_TABLE}.order_id = s.order_id
              AND (
                  {TARGET_TABLE}.status     <> s.status     OR
                  {TARGET_TABLE}.amount     <> s.amount     OR
                  {TARGET_TABLE}.updated_at <> s.updated_at
              )
        """))

        result_ins = conn.execute(text(f"""
            INSERT INTO {TARGET_TABLE}
                (order_id, customer_id, product, amount, status,
                 amount_category, created_at, updated_at, _pipeline_loaded)
            SELECT s.order_id, s.customer_id, s.product, s.amount, s.status,
                   s.amount_category, s.created_at, s.updated_at, s._pipeline_loaded
            FROM {staging} AS s
            WHERE NOT EXISTS (
                SELECT 1 FROM {TARGET_TABLE} t WHERE t.order_id = s.order_id
            )
        """))

        conn.execute(text(f"DROP TABLE IF EXISTS {staging}"))

    affected = result_upd.rowcount + result_ins.rowcount
    logger.info(
        "LOAD: %d rows affected (%d updated, %d inserted).",
        affected, result_upd.rowcount, result_ins.rowcount,
    )
    return affected


# =============================================================================
# 5. WATERMARK & AUDIT HELPERS
# =============================================================================

def get_watermark(engine) -> str | None:
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT watermark_val FROM pipeline_state WHERE pipeline_name = :name"),
            {"name": PIPELINE_NAME},
        ).fetchone()
    return row[0] if row else None


def save_watermark(engine, watermark_val: str, rows_extracted: int) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO pipeline_state
                    (pipeline_name, watermark_col, watermark_val, last_run_at, rows_extracted)
                VALUES (:name, :col, :val, :now, :rows)
                ON CONFLICT(pipeline_name) DO UPDATE SET
                    watermark_col  = excluded.watermark_col,
                    watermark_val  = excluded.watermark_val,
                    last_run_at    = excluded.last_run_at,
                    rows_extracted = excluded.rows_extracted
            """),
            {"name": PIPELINE_NAME, "col": WATERMARK_COL, "val": watermark_val, "now": now, "rows": rows_extracted},
        )


def start_run_log(engine, watermark_before: str | None) -> int:
    """Insert a 'running' entry in the audit log and return the new run_id."""
    now = datetime.now(timezone.utc).isoformat()
    with engine.begin() as conn:
        result = conn.execute(
            text("""
                INSERT INTO pipeline_run_log
                    (pipeline_name, started_at, status, watermark_before)
                VALUES (:name, :now, 'running', :wm)
            """),
            {"name": PIPELINE_NAME, "now": now, "wm": watermark_before},
        )
        return result.lastrowid


def finish_run_log(
    engine,
    run_id: int,
    status: str,
    watermark_after: str | None,
    rows_extracted: int,
    rows_loaded: int,
    error_message: str | None = None,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE pipeline_run_log
                SET finished_at    = :now,
                    status         = :status,
                    watermark_after= :wm_after,
                    rows_extracted = :extracted,
                    rows_loaded    = :loaded,
                    error_message  = :error
                WHERE run_id = :run_id
            """),
            {
                "now": now, "status": status, "wm_after": watermark_after,
                "extracted": rows_extracted, "loaded": rows_loaded,
                "error": error_message, "run_id": run_id,
            },
        )


# =============================================================================
# 6. PIPELINE ORCHESTRATION
# =============================================================================

def run_pipeline(engine) -> dict:
    """
    Execute one full pipeline run: Extract → Transform → Load → Update state.

    Watermark is only advanced AFTER a successful load. If any step raises
    an exception, the watermark stays at its previous value so the next run
    will retry the same batch.

    Returns:
        Summary dict with run metadata.
    """
    watermark_before = get_watermark(engine)
    run_id = start_run_log(engine, watermark_before)

    logger.info("=" * 55)
    logger.info("Pipeline run #%d started.  Watermark: %s", run_id, watermark_before or "None (first run)")
    logger.info("=" * 55)

    rows_extracted = 0
    rows_loaded    = 0
    watermark_after = watermark_before

    try:
        # EXTRACT
        df_raw = extract(engine, watermark_before)
        rows_extracted = len(df_raw)

        if df_raw.empty:
            logger.info("Nothing new to process. Pipeline run complete.")
            finish_run_log(engine, run_id, "success", watermark_before, 0, 0)
            return {"run_id": run_id, "status": "success", "rows_extracted": 0, "rows_loaded": 0}

        # TRANSFORM
        df_clean = transform(df_raw)

        # LOAD
        rows_loaded = load(engine, df_clean)

        # Update watermark — ONLY on success
        watermark_after = df_raw[WATERMARK_COL].max().isoformat()
        save_watermark(engine, watermark_after, rows_extracted)

        finish_run_log(engine, run_id, "success", watermark_after, rows_extracted, rows_loaded)
        logger.info(
            "Pipeline run #%d SUCCESS. Extracted=%d  Loaded=%d  New watermark=%s",
            run_id, rows_extracted, rows_loaded, watermark_after,
        )
        return {
            "run_id": run_id, "status": "success",
            "rows_extracted": rows_extracted, "rows_loaded": rows_loaded,
            "watermark_before": watermark_before, "watermark_after": watermark_after,
        }

    except Exception as exc:
        error_msg = traceback.format_exc()
        logger.error("Pipeline run #%d FAILED: %s", run_id, exc)
        finish_run_log(engine, run_id, "failed", watermark_before, rows_extracted, rows_loaded, error_msg)
        return {"run_id": run_id, "status": "failed", "error": str(exc)}


# =============================================================================
# 7. DEMO
# =============================================================================

def show_run_log(engine) -> None:
    df = pd.read_sql(
        "SELECT run_id, status, started_at, rows_extracted, rows_loaded, watermark_before, watermark_after FROM pipeline_run_log",
        con=engine,
    )
    print(df.to_string(index=False))


def show_target_sample(engine, n: int = 5) -> None:
    df = pd.read_sql(
        f"SELECT order_id, customer_id, product, amount, amount_category, status, updated_at FROM {TARGET_TABLE} ORDER BY order_id LIMIT {n}",
        con=engine,
    )
    print(df.to_string(index=False))


if __name__ == "__main__":
    if DB_PATH.exists():
        DB_PATH.unlink()

    engine = get_engine()
    setup_all_tables(engine)
    seed_source(engine)

    # ── Run 1: First run — full load ─────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  RUN 1: First run (full load)")
    print("=" * 60)
    run_pipeline(engine)

    # ── Run 2: No new data ────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  RUN 2: No new data (0 rows expected)")
    print("=" * 60)
    run_pipeline(engine)

    # ── Simulate new orders ───────────────────────────────────────────────────
    new_rows = pd.DataFrame([
        {"order_id": 51, "customer_id": "C011", "product": "Tablet",    "amount": 499.0, "status": "PENDING",   "created_at": "2024-01-26 08:00:00", "updated_at": "2024-01-26 08:00:00"},
        {"order_id": 52, "customer_id": "C012", "product": "SSD",       "amount": 120.0, "status": "Completed", "created_at": "2024-01-26 09:00:00", "updated_at": "2024-01-26 09:00:00"},
        {"order_id": 53, "customer_id": "C013", "product": "USB Hub",   "amount":  35.0, "status": "pending",   "created_at": "2024-01-26 10:00:00", "updated_at": "2024-01-26 10:00:00"},
    ])
    new_rows.to_sql(SOURCE_TABLE, con=engine, if_exists="append", index=False)
    logger.info("Simulated 3 new source orders.")

    # ── Run 3: Incremental — 3 new rows ──────────────────────────────────────
    print("\n" + "=" * 60)
    print("  RUN 3: Incremental (3 new orders)")
    print("=" * 60)
    run_pipeline(engine)

    # ── Simulate an update on an existing order ───────────────────────────────
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE source_orders SET status='completed', updated_at='2024-01-27 10:00:00' WHERE order_id=51")
        )
    logger.info("Simulated update: order_id=51 → completed")

    # ── Run 4: Picks up the 1 updated row ─────────────────────────────────────
    print("\n" + "=" * 60)
    print("  RUN 4: Incremental (1 updated order)")
    print("=" * 60)
    run_pipeline(engine)

    # ── Run 5: Idempotency — same state, nothing new ──────────────────────────
    print("\n" + "=" * 60)
    print("  RUN 5: Idempotency check (0 rows expected)")
    print("=" * 60)
    run_pipeline(engine)

    # ── Results ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  PIPELINE RUN LOG (audit trail)")
    print("=" * 60)
    show_run_log(engine)

    print("\n" + "=" * 60)
    print("  TARGET TABLE SAMPLE (first 5 rows)")
    print("=" * 60)
    show_target_sample(engine)

    total = pd.read_sql(f"SELECT COUNT(*) AS cnt FROM {TARGET_TABLE}", con=engine).iloc[0]["cnt"]
    print(f"\n  Total rows in target: {total}  (expected: 53)")
    print("\nDone. Database saved to:", DB_PATH)
