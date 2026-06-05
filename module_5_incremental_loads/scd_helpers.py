"""
scd_helpers.py
--------------
Importable SCD Type 1 and Type 2 functions.
Used by 03_scd_type1_type2.py and tests/test_module_5_incremental.py.
"""

import logging
from datetime import datetime, timezone

import pandas as pd
from sqlalchemy import text

logger = logging.getLogger("etl.scd")

SCD2_OPEN_DATE = "9999-12-31"


def setup_scd1_table(engine) -> None:
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


def setup_scd2_table(engine) -> None:
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


def apply_scd1(engine, record: dict) -> str:
    record = {**record, "last_updated": datetime.now(timezone.utc).isoformat()}
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
            return "inserted"
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
            return "updated"


def get_current_scd2_record(engine, customer_id: str) -> dict | None:
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM dim_customers_scd2 WHERE customer_id = :id AND is_current = 1"),
            {"id": customer_id},
        ).mappings().fetchone()
    return dict(row) if row else None


def apply_scd2(
    engine,
    record: dict,
    effective_date: str | None = None,
    tracked_cols: list[str] | None = None,
) -> str:
    from datetime import date
    if effective_date is None:
        effective_date = date.today().isoformat()
    if tracked_cols is None:
        tracked_cols = ["full_name", "email", "loyalty_tier", "country"]

    current = get_current_scd2_record(engine, record["customer_id"])

    if current is None:
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
        return "inserted"

    if not any(current.get(c) != record.get(c) for c in tracked_cols):
        return "no_change"

    close_date = (
        pd.Timestamp(effective_date) - pd.Timedelta(days=1)
    ).strftime("%Y-%m-%d")

    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE dim_customers_scd2
                SET valid_to = :close_date, is_current = 0
                WHERE customer_id = :id AND is_current = 1
            """),
            {"close_date": close_date, "id": record["customer_id"]},
        )
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

    return "versioned"


def get_record_at_date(engine, customer_id: str, as_of_date: str) -> dict | None:
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
