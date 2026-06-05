"""
Module 5 - Lesson 3: Slowly Changing Dimensions (SCD) — Type 1 and Type 2
===========================================================================
In any data warehouse or analytical store, dimension tables describe the
"who, what, where" of your data: customers, products, employees, locations.
These attributes change over time, and HOW you handle those changes is called
Slowly Changing Dimension (SCD) management.

Two strategies are most common in practice:

  SCD Type 1 — Overwrite
    Simply UPDATE the existing record with the new value.
    No history is kept. Easy to implement.
    Use when: history is irrelevant (e.g., fixing a typo in a name).

  SCD Type 2 — Track full history
    When an attribute changes, CLOSE the current record by setting its
    valid_to date, then INSERT a new record as the current version.
    A record is "current" when valid_to IS NULL (or a far-future sentinel date).
    Use when: you need to reproduce historical states
              (e.g., "what was the customer's loyalty tier when they placed this order?")

This lesson implements both strategies from scratch using SQLite so you can
observe exactly what happens in the database at each step.

Topics covered:
  1. Dimension table schemas for Type 1 and Type 2
  2. Type 1: apply_scd1() — UPDATE in place
  3. Type 2: apply_scd2() — close old row, insert new row, never delete
  4. Helper: get_current_record() — fetch the currently active Type 2 row
  5. A demo that evolves a set of customer records through multiple changes
  6. Querying history — "point-in-time" lookups using valid_from / valid_to
"""

import logging
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
MODULE_DIR = Path(__file__).parent
DB_PATH    = MODULE_DIR / "scd_demo.db"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("etl.scd")

# Sentinel value for "this record is currently active" in Type 2
SCD2_OPEN_DATE = "9999-12-31"


# =============================================================================
# DATABASE SETUP
# =============================================================================

def get_engine(db_path: Path = DB_PATH):
    return create_engine(f"sqlite:///{db_path}", echo=False)


def setup_scd1_table(engine) -> None:
    """
    SCD Type 1 dimension table.

    Simple: one row per customer, no history columns.
    The row is updated in-place whenever an attribute changes.
    """
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS dim_customers_scd1"))
        conn.execute(text("""
            CREATE TABLE dim_customers_scd1 (
                customer_id   TEXT PRIMARY KEY,
                full_name     TEXT NOT NULL,
                email         TEXT,
                loyalty_tier  TEXT NOT NULL DEFAULT 'bronze',
                country       TEXT,
                last_updated  TEXT NOT NULL
            )
        """))
    logger.info("SCD1 table created.")


def setup_scd2_table(engine) -> None:
    """
    SCD Type 2 dimension table.

    One customer can have MULTIPLE rows — one per version of their attributes.
    Each row tracks the time window during which those attributes were active.

    Key columns:
        surrogate_key  — auto-increment PK (never reuse natural keys in SCD2 joins)
        customer_id    — the natural/business key from the source system
        valid_from     — date this version became active
        valid_to       — date this version was superseded (NULL or '9999-12-31' = current)
        is_current     — convenience boolean: 1 = active row, 0 = historical
    """
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS dim_customers_scd2"))
        conn.execute(text("""
            CREATE TABLE dim_customers_scd2 (
                surrogate_key  INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id    TEXT    NOT NULL,
                full_name      TEXT    NOT NULL,
                email          TEXT,
                loyalty_tier   TEXT    NOT NULL DEFAULT 'bronze',
                country        TEXT,
                valid_from     TEXT    NOT NULL,
                valid_to       TEXT    NOT NULL DEFAULT '9999-12-31',
                is_current     INTEGER NOT NULL DEFAULT 1
            )
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_scd2_customer
            ON dim_customers_scd2(customer_id, is_current)
        """))
    logger.info("SCD2 table created.")


# =============================================================================
# SCD TYPE 1: OVERWRITE
# =============================================================================

def apply_scd1(engine, record: dict) -> str:
    """
    Apply a Type 1 (overwrite) change for a single customer record.

    Logic:
      - If the customer_id does NOT exist → INSERT new row.
      - If the customer_id DOES exist     → UPDATE all columns in place.
        History is lost; only the current state is stored.

    Args:
        engine: SQLAlchemy engine.
        record: dict with keys matching dim_customers_scd1 columns.

    Returns:
        "inserted" or "updated"
    """
    record["last_updated"] = datetime.now(timezone.utc).isoformat()
    with engine.begin() as conn:
        existing = conn.execute(
            text("SELECT 1 FROM dim_customers_scd1 WHERE customer_id = :id"),
            {"id": record["customer_id"]},
        ).fetchone()

        if existing is None:
            conn.execute(
                text("""
                    INSERT INTO dim_customers_scd1
                        (customer_id, full_name, email, loyalty_tier, country, last_updated)
                    VALUES
                        (:customer_id, :full_name, :email, :loyalty_tier, :country, :last_updated)
                """),
                record,
            )
            action = "inserted"
        else:
            conn.execute(
                text("""
                    UPDATE dim_customers_scd1
                    SET full_name    = :full_name,
                        email        = :email,
                        loyalty_tier = :loyalty_tier,
                        country      = :country,
                        last_updated = :last_updated
                    WHERE customer_id = :customer_id
                """),
                record,
            )
            action = "updated"

    logger.info("SCD1 %s: customer_id=%s", action, record["customer_id"])
    return action


# =============================================================================
# SCD TYPE 2: TRACK HISTORY
# =============================================================================

def get_current_scd2_record(engine, customer_id: str) -> dict | None:
    """
    Retrieve the currently active (is_current=1) row for a customer.

    Returns:
        Dict of column values, or None if the customer has no current record.
    """
    with engine.connect() as conn:
        row = conn.execute(
            text("""
                SELECT * FROM dim_customers_scd2
                WHERE customer_id = :id AND is_current = 1
            """),
            {"id": customer_id},
        ).mappings().fetchone()
    return dict(row) if row else None


def _has_scd2_changed(current: dict, incoming: dict, tracked_cols: list[str]) -> bool:
    """Return True if any tracked attribute differs between current and incoming."""
    return any(current.get(col) != incoming.get(col) for col in tracked_cols)


def apply_scd2(
    engine,
    record: dict,
    effective_date: str | None = None,
    tracked_cols: list[str] | None = None,
) -> str:
    """
    Apply a Type 2 (history-preserving) change for a single customer record.

    Logic:
      - If the customer_id does NOT exist → INSERT as new current record.
      - If the customer_id DOES exist AND tracked attributes have changed:
          1. Close the current record: set valid_to = effective_date - 1 day,
             set is_current = 0.
          2. Insert a new record with valid_from = effective_date, is_current = 1.
      - If tracked attributes are UNCHANGED → do nothing (idempotent).

    Args:
        engine:         SQLAlchemy engine.
        record:         dict with keys matching dim_customers_scd2 columns.
        effective_date: ISO date string for when this change takes effect.
                        Defaults to today (UTC).
        tracked_cols:   Which columns trigger a new SCD2 row when they change.
                        Defaults to ['full_name', 'email', 'loyalty_tier', 'country'].

    Returns:
        "inserted", "versioned", or "no_change"
    """
    if effective_date is None:
        effective_date = date.today().isoformat()
    if tracked_cols is None:
        tracked_cols = ["full_name", "email", "loyalty_tier", "country"]

    current = get_current_scd2_record(engine, record["customer_id"])

    if current is None:
        # ── New customer: insert first version ──────────────────────────────
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO dim_customers_scd2
                        (customer_id, full_name, email, loyalty_tier, country,
                         valid_from, valid_to, is_current)
                    VALUES
                        (:customer_id, :full_name, :email, :loyalty_tier, :country,
                         :valid_from, '9999-12-31', 1)
                """),
                {**record, "valid_from": effective_date},
            )
        logger.info("SCD2 inserted (new): customer_id=%s", record["customer_id"])
        return "inserted"

    if not _has_scd2_changed(current, record, tracked_cols):
        # ── No tracked attributes changed: skip ─────────────────────────────
        logger.info("SCD2 no_change: customer_id=%s", record["customer_id"])
        return "no_change"

    # ── Attribute changed: close current row, open new row ──────────────────
    # The closed row's valid_to is set to one day before the new version's
    # valid_from, so there are no gaps or overlaps in the timeline.
    close_date = (
        pd.Timestamp(effective_date) - pd.Timedelta(days=1)
    ).strftime("%Y-%m-%d")

    with engine.begin() as conn:
        # Step 1: Close the current row
        conn.execute(
            text("""
                UPDATE dim_customers_scd2
                SET valid_to   = :close_date,
                    is_current = 0
                WHERE customer_id = :id AND is_current = 1
            """),
            {"close_date": close_date, "id": record["customer_id"]},
        )
        # Step 2: Insert the new current row
        conn.execute(
            text("""
                INSERT INTO dim_customers_scd2
                    (customer_id, full_name, email, loyalty_tier, country,
                     valid_from, valid_to, is_current)
                VALUES
                    (:customer_id, :full_name, :email, :loyalty_tier, :country,
                     :valid_from, '9999-12-31', 1)
            """),
            {**record, "valid_from": effective_date},
        )

    logger.info(
        "SCD2 versioned: customer_id=%s  old valid_to=%s  new valid_from=%s",
        record["customer_id"], close_date, effective_date,
    )
    return "versioned"


# =============================================================================
# POINT-IN-TIME QUERY
# =============================================================================

def get_record_at_date(engine, customer_id: str, as_of_date: str) -> dict | None:
    """
    Retrieve the customer's attributes AS OF a specific date.

    This is the core value of SCD Type 2: you can reconstruct historical states.

    Example:
        "What loyalty tier did customer C001 have on 2024-02-15?"
    """
    with engine.connect() as conn:
        row = conn.execute(
            text("""
                SELECT * FROM dim_customers_scd2
                WHERE customer_id = :id
                  AND valid_from <= :dt
                  AND valid_to   >= :dt
                ORDER BY valid_from DESC
                LIMIT 1
            """),
            {"id": customer_id, "dt": as_of_date},
        ).mappings().fetchone()
    return dict(row) if row else None


# =============================================================================
# DEMO
# =============================================================================

def show_scd1(engine) -> None:
    df = pd.read_sql("SELECT * FROM dim_customers_scd1 ORDER BY customer_id", con=engine)
    print(df.to_string(index=False))


def show_scd2(engine) -> None:
    df = pd.read_sql(
        "SELECT surrogate_key, customer_id, full_name, loyalty_tier, valid_from, valid_to, is_current FROM dim_customers_scd2 ORDER BY customer_id, surrogate_key",
        con=engine,
    )
    print(df.to_string(index=False))


if __name__ == "__main__":
    if DB_PATH.exists():
        DB_PATH.unlink()

    engine = get_engine()
    setup_scd1_table(engine)
    setup_scd2_table(engine)

    # ── Initial load: three customers ────────────────────────────────────────
    initial_customers = [
        {"customer_id": "C001", "full_name": "Alice Johnson", "email": "alice@example.com", "loyalty_tier": "bronze",   "country": "US"},
        {"customer_id": "C002", "full_name": "Bob Smith",     "email": "bob@example.com",   "loyalty_tier": "silver",   "country": "US"},
        {"customer_id": "C003", "full_name": "Carol White",   "email": "carol@example.com", "loyalty_tier": "bronze",   "country": "CA"},
    ]

    print("\n" + "=" * 60)
    print("  INITIAL LOAD")
    print("=" * 60)
    for c in initial_customers:
        apply_scd1(engine, {**c})
        apply_scd2(engine, {**c}, effective_date="2024-01-01")

    print("\n  SCD1 after initial load:")
    show_scd1(engine)
    print("\n  SCD2 after initial load:")
    show_scd2(engine)

    # ── Change 1: Alice is promoted to gold tier ─────────────────────────────
    print("\n" + "=" * 60)
    print("  CHANGE 1: Alice promoted to gold tier (2024-03-01)")
    print("=" * 60)
    alice_v2 = {"customer_id": "C001", "full_name": "Alice Johnson", "email": "alice@example.com", "loyalty_tier": "gold", "country": "US"}
    apply_scd1(engine, {**alice_v2})
    apply_scd2(engine, {**alice_v2}, effective_date="2024-03-01")

    print("\n  SCD1 (history LOST — only current state):")
    show_scd1(engine)
    print("\n  SCD2 (history PRESERVED — 2 rows for Alice):")
    show_scd2(engine)

    # ── Change 2: Bob moves to Canada ────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  CHANGE 2: Bob moves to Canada (2024-06-15)")
    print("=" * 60)
    bob_v2 = {"customer_id": "C002", "full_name": "Bob Smith", "email": "bob@example.com", "loyalty_tier": "silver", "country": "CA"}
    apply_scd1(engine, {**bob_v2})
    apply_scd2(engine, {**bob_v2}, effective_date="2024-06-15")

    print("\n  SCD2 (now 5 total rows — 2 for Alice, 2 for Bob, 1 for Carol):")
    show_scd2(engine)

    # ── Idempotency check: apply the same change again ───────────────────────
    print("\n" + "=" * 60)
    print("  IDEMPOTENCY: Apply Bob's change again — should produce no_change")
    print("=" * 60)
    result = apply_scd2(engine, {**bob_v2}, effective_date="2024-06-15")
    print(f"  Result: {result}  (expected: no_change)")
    print("\n  SCD2 row count should still be 5:")
    count = pd.read_sql("SELECT COUNT(*) AS cnt FROM dim_customers_scd2", con=engine).iloc[0]["cnt"]
    print(f"  Row count: {count}")

    # ── Point-in-time query ──────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  POINT-IN-TIME QUERIES")
    print("=" * 60)
    for customer_id, as_of in [("C001", "2024-02-01"), ("C001", "2024-04-01"), ("C002", "2024-05-01"), ("C002", "2024-07-01")]:
        rec = get_record_at_date(engine, customer_id, as_of)
        if rec:
            print(f"  {customer_id} as of {as_of}: loyalty_tier={rec['loyalty_tier']}, country={rec['country']}")
        else:
            print(f"  {customer_id} as of {as_of}: no record found")

    print("\n  Final SCD2 table (full history — records are never deleted):")
    show_scd2(engine)
    print("\nDone. Database saved to:", DB_PATH)
