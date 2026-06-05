"""
Module 5 - Lesson 2: Upsert Patterns
======================================
An "upsert" (update + insert) is the operation of inserting a row if it doesn't
exist, or updating it if it does — based on a unique key. This is the cornerstone
of idempotent pipelines: running the load step twice produces the same result.

Without upserts, re-running a pipeline duplicates data. With upserts, re-running
is safe and pipelines become restartable after failures.

This lesson demonstrates three strategies, each with different trade-offs:

  Strategy 1 — INSERT OR IGNORE (append-only, no overwrites)
    Use when: you only want new rows and NEVER want to overwrite existing data.
    Risk:     silently drops updates to existing records.

  Strategy 2 — INSERT OR REPLACE (full overwrite on conflict)
    Use when: source always has the full, current version of a record.
    Risk:     loses any columns not present in the source (deletes and re-inserts).

  Strategy 3 — Staged MERGE (most flexible and production-grade)
    Load new data into a staging table, then apply changes row-by-row:
      - New rows  → INSERT
      - Changed rows → UPDATE (only modified columns)
      - Deleted rows → optional DELETE or soft-delete
    Use when: you need fine-grained control over what gets updated.

Topics covered:
  1. Setting up target and staging tables
  2. INSERT OR IGNORE demo + idempotency proof
  3. INSERT OR REPLACE demo + idempotency proof
  4. Staged MERGE demo + idempotency proof
  5. Comparing the three strategies side-by-side
"""

import logging
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
MODULE_DIR = Path(__file__).parent
DATA_DIR   = MODULE_DIR / "data"
DB_PATH    = MODULE_DIR / "upsert_demo.db"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("etl.upsert")


# =============================================================================
# SETUP HELPERS
# =============================================================================

def get_engine(db_path: Path = DB_PATH):
    return create_engine(f"sqlite:///{db_path}", echo=False)


def create_orders_table(engine, table_name: str) -> None:
    """Create a clean target orders table."""
    with engine.begin() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
        conn.execute(text(f"""
            CREATE TABLE {table_name} (
                order_id    INTEGER PRIMARY KEY,
                customer_id TEXT    NOT NULL,
                product     TEXT    NOT NULL,
                amount      REAL    NOT NULL,
                status      TEXT    NOT NULL,
                updated_at  TEXT    NOT NULL
            )
        """))
    logger.info("Table '%s' created.", table_name)


def seed_target(engine, table_name: str, rows: list[dict]) -> None:
    """Insert a set of initial rows into the target table."""
    df = pd.DataFrame(rows)
    df.to_sql(table_name, con=engine, if_exists="append", index=False)
    logger.info("Seeded %d rows into '%s'.", len(rows), table_name)


def show_table(engine, table_name: str, label: str = "") -> None:
    df = pd.read_sql(f"SELECT * FROM {table_name} ORDER BY order_id", con=engine)
    header = f"  {label or table_name}  ({len(df)} rows)"
    print(f"\n{'─' * 60}")
    print(header)
    print(f"{'─' * 60}")
    print(df.to_string(index=False))


# =============================================================================
# SHARED SAMPLE DATA
# =============================================================================

# Existing rows already in the target
EXISTING_ROWS = [
    {"order_id": 1, "customer_id": "C001", "product": "Laptop",   "amount": 1200.0, "status": "pending",   "updated_at": "2024-01-01 08:00:00"},
    {"order_id": 2, "customer_id": "C002", "product": "Mouse",    "amount":   25.0, "status": "completed", "updated_at": "2024-01-01 09:00:00"},
    {"order_id": 3, "customer_id": "C003", "product": "Keyboard", "amount":   75.0, "status": "pending",   "updated_at": "2024-01-02 10:00:00"},
]

# Incoming batch: order 2 is unchanged, order 3 has a status update, order 4 is new
INCOMING_BATCH = [
    {"order_id": 2, "customer_id": "C002", "product": "Mouse",    "amount":   25.0, "status": "completed", "updated_at": "2024-01-01 09:00:00"},  # unchanged
    {"order_id": 3, "customer_id": "C003", "product": "Keyboard", "amount":   75.0, "status": "completed", "updated_at": "2024-01-03 14:00:00"},  # updated status
    {"order_id": 4, "customer_id": "C004", "product": "Monitor",  "amount":  350.0, "status": "pending",   "updated_at": "2024-01-03 11:00:00"},  # new
]


# =============================================================================
# STRATEGY 1: INSERT OR IGNORE
# =============================================================================

def load_insert_or_ignore(engine, table_name: str, df: pd.DataFrame) -> int:
    """
    Insert rows only if the primary key does not already exist.
    Existing rows are left completely unchanged.

    When to use:
      - Append-only event logs where records are never updated.
      - Sources where a record, once written, never changes.

    Trade-off:
      - Safe against duplicates.
      - Will MISS updates to existing records.

    Returns:
        Number of rows actually inserted.
    """
    inserted = 0
    with engine.begin() as conn:
        for _, row in df.iterrows():
            result = conn.execute(
                text(f"""
                    INSERT OR IGNORE INTO {table_name}
                        (order_id, customer_id, product, amount, status, updated_at)
                    VALUES
                        (:order_id, :customer_id, :product, :amount, :status, :updated_at)
                """),
                row.to_dict(),
            )
            inserted += result.rowcount
    logger.info("INSERT OR IGNORE: %d/%d rows inserted.", inserted, len(df))
    return inserted


# =============================================================================
# STRATEGY 2: INSERT OR REPLACE
# =============================================================================

def load_insert_or_replace(engine, table_name: str, df: pd.DataFrame) -> int:
    """
    Insert the row; if the primary key conflicts, DELETE the old row and
    INSERT the new one. This is SQLite's equivalent of REPLACE INTO.

    When to use:
      - Source always delivers the complete, authoritative version of a record.
      - You want the target to be an exact mirror of the source.

    Trade-off:
      - Handles updates correctly.
      - Replaces the ENTIRE row — any columns absent from the source are lost.
      - The DELETE+INSERT sequence increments the rowid (matters for some engines).

    Returns:
        Number of rows affected (inserts + replacements).
    """
    affected = 0
    with engine.begin() as conn:
        for _, row in df.iterrows():
            result = conn.execute(
                text(f"""
                    INSERT OR REPLACE INTO {table_name}
                        (order_id, customer_id, product, amount, status, updated_at)
                    VALUES
                        (:order_id, :customer_id, :product, :amount, :status, :updated_at)
                """),
                row.to_dict(),
            )
            affected += result.rowcount
    logger.info("INSERT OR REPLACE: %d/%d rows affected.", affected, len(df))
    return affected


# =============================================================================
# STRATEGY 3: STAGED MERGE
# =============================================================================

def load_staged_merge(engine, target_table: str, df: pd.DataFrame) -> dict:
    """
    Production-grade upsert using a staging table:
      1. Load incoming data into a temporary staging table.
      2. UPDATE existing rows where the key matches and data has changed.
      3. INSERT new rows whose key does not yet exist in the target.

    When to use:
      - You want partial updates (only changed columns, not full row replace).
      - You need separate INSERT vs UPDATE counts for auditing.
      - You want to extend to support soft-deletes or change tracking.

    Returns:
        dict with keys "inserted" and "updated".
    """
    staging_table = f"{target_table}_staging"

    # Step 1: Load into staging (replace each time)
    df.to_sql(staging_table, con=engine, if_exists="replace", index=False)
    logger.info("Staged %d rows into '%s'.", len(df), staging_table)

    with engine.begin() as conn:
        # Step 2: UPDATE rows that already exist in target and have changed data
        result_update = conn.execute(text(f"""
            UPDATE {target_table}
            SET
                customer_id = s.customer_id,
                product     = s.product,
                amount      = s.amount,
                status      = s.status,
                updated_at  = s.updated_at
            FROM {staging_table} AS s
            WHERE {target_table}.order_id = s.order_id
              AND (
                  {target_table}.status     <> s.status     OR
                  {target_table}.amount     <> s.amount     OR
                  {target_table}.updated_at <> s.updated_at
              )
        """))
        updated = result_update.rowcount

        # Step 3: INSERT rows that do not yet exist in target
        result_insert = conn.execute(text(f"""
            INSERT INTO {target_table} (order_id, customer_id, product, amount, status, updated_at)
            SELECT s.order_id, s.customer_id, s.product, s.amount, s.status, s.updated_at
            FROM {staging_table} AS s
            WHERE NOT EXISTS (
                SELECT 1 FROM {target_table} t WHERE t.order_id = s.order_id
            )
        """))
        inserted = result_insert.rowcount

        # Step 4: Clean up staging table
        conn.execute(text(f"DROP TABLE IF EXISTS {staging_table}"))

    logger.info("STAGED MERGE: %d inserted, %d updated.", inserted, updated)
    return {"inserted": inserted, "updated": updated}


# =============================================================================
# DEMO: RUN ALL THREE STRATEGIES AND COMPARE
# =============================================================================

def demo_strategy(label: str, strategy_fn, table_name: str, engine) -> None:
    """Helper to run and display a strategy demo."""
    print(f"\n{'=' * 60}")
    print(f"  STRATEGY: {label}")
    print(f"{'=' * 60}")

    create_orders_table(engine, table_name)
    seed_target(engine, table_name, EXISTING_ROWS)
    show_table(engine, table_name, "BEFORE (existing rows)")

    df_incoming = pd.DataFrame(INCOMING_BATCH)
    strategy_fn(engine, table_name, df_incoming)
    show_table(engine, table_name, "AFTER (first load)")

    # Idempotency check: run the same load a second time
    logger.info("--- Idempotency check: running the same load again ---")
    strategy_fn(engine, table_name, df_incoming)
    show_table(engine, table_name, "AFTER (second load — must be identical)")


if __name__ == "__main__":
    if DB_PATH.exists():
        DB_PATH.unlink()

    engine = get_engine()

    demo_strategy("INSERT OR IGNORE",   load_insert_or_ignore,  "orders_ignore",  engine)
    demo_strategy("INSERT OR REPLACE",  load_insert_or_replace, "orders_replace", engine)
    demo_strategy("STAGED MERGE",       load_staged_merge,      "orders_merge",   engine)

    # ── Side-by-side comparison ───────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print("  COMPARISON: order_id=3 (should be 'completed' after update)")
    print(f"{'=' * 60}")
    for tbl, strategy in [
        ("orders_ignore",  "INSERT OR IGNORE  "),
        ("orders_replace", "INSERT OR REPLACE "),
        ("orders_merge",   "STAGED MERGE      "),
    ]:
        row = pd.read_sql(
            f"SELECT order_id, status, updated_at FROM {tbl} WHERE order_id=3",
            con=engine,
        )
        status = row["status"].iloc[0]
        mark = "✓" if status == "completed" else "✗"
        print(f"  {mark}  {strategy}  status={status}")

    print(f"\n{'=' * 60}")
    print("  KEY TAKEAWAYS")
    print(f"{'=' * 60}")
    print("""
  INSERT OR IGNORE  — safe for append-only; misses updates
  INSERT OR REPLACE — easy full overwrite; loses partial-column control
  STAGED MERGE      — most flexible; use in production pipelines
    """)

    print("Done. Database saved to:", DB_PATH)
