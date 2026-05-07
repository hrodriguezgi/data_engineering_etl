"""
watermark_helpers.py
--------------------
Importable helper functions for watermark-based incremental extraction.
Used by 01_watermark_based_extraction.py and tests/test_module_5_incremental.py.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

logger = logging.getLogger("etl.watermark")

LOOKBACK_SECONDS = 5


def get_engine(db_path: Path):
    return create_engine(f"sqlite:///{db_path}", echo=False)


def setup_source_table_from_df(engine, df: pd.DataFrame, table: str = "source_orders") -> None:
    df.to_sql(table, con=engine, if_exists="replace", index=False)


def setup_state_table(engine) -> None:
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


def get_watermark(engine, pipeline_name: str) -> str | None:
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
    from datetime import timezone
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
            {"name": pipeline_name, "col": watermark_col, "val": watermark_val,
             "now": now, "rows": rows_extracted},
        )


def extract_incremental(
    engine,
    pipeline_name: str,
    watermark_col: str = "updated_at",
    table: str = "source_orders",
) -> pd.DataFrame:
    last_watermark = get_watermark(engine, pipeline_name)

    if last_watermark is None:
        query = f"SELECT * FROM {table} ORDER BY {watermark_col}"
        df = pd.read_sql(query, con=engine)
    else:
        watermark_dt   = datetime.fromisoformat(last_watermark)
        safe_watermark = (watermark_dt - timedelta(seconds=LOOKBACK_SECONDS)).isoformat()
        query = f"SELECT * FROM {table} WHERE {watermark_col} > :wm ORDER BY {watermark_col}"
        df = pd.read_sql(text(query), con=engine, params={"wm": safe_watermark})

    return df
