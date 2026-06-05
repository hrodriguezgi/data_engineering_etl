"""
pipeline_helpers.py
--------------------
Importable pipeline functions for the full incremental pipeline.
Used by 04_incremental_pipeline.py and tests/test_module_5_incremental.py.
"""

import logging
import traceback
from datetime import datetime, timedelta, timezone

import pandas as pd
from sqlalchemy import text

logger = logging.getLogger("etl.incremental_pipeline")

PIPELINE_NAME  = "orders_incremental_pipeline"
WATERMARK_COL  = "updated_at"
SOURCE_TABLE   = "source_orders"
TARGET_TABLE   = "target_orders"
LOOKBACK_SECS  = 5


def setup_all_tables(engine) -> None:
    with engine.begin() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS {SOURCE_TABLE}"))
        conn.execute(text(f"""
            CREATE TABLE {SOURCE_TABLE} (
                order_id    INTEGER PRIMARY KEY,
                customer_id TEXT NOT NULL,
                product     TEXT NOT NULL,
                amount      REAL NOT NULL,
                status      TEXT NOT NULL,
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL
            )
        """))
        conn.execute(text(f"DROP TABLE IF EXISTS {TARGET_TABLE}"))
        conn.execute(text(f"""
            CREATE TABLE {TARGET_TABLE} (
                order_id          INTEGER PRIMARY KEY,
                customer_id       TEXT NOT NULL,
                product           TEXT NOT NULL,
                amount            REAL NOT NULL,
                status            TEXT NOT NULL,
                amount_category   TEXT,
                created_at        TEXT NOT NULL,
                updated_at        TEXT NOT NULL,
                _pipeline_loaded  TEXT NOT NULL
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS pipeline_state (
                pipeline_name  TEXT PRIMARY KEY,
                watermark_col  TEXT NOT NULL,
                watermark_val  TEXT,
                last_run_at    TEXT,
                rows_extracted INTEGER DEFAULT 0
            )
        """))
        conn.execute(text("DROP TABLE IF EXISTS pipeline_run_log"))
        conn.execute(text("""
            CREATE TABLE pipeline_run_log (
                run_id            INTEGER PRIMARY KEY AUTOINCREMENT,
                pipeline_name     TEXT NOT NULL,
                started_at        TEXT NOT NULL,
                finished_at       TEXT,
                status            TEXT NOT NULL DEFAULT 'running',
                watermark_before  TEXT,
                watermark_after   TEXT,
                rows_extracted    INTEGER DEFAULT 0,
                rows_loaded       INTEGER DEFAULT 0,
                error_message     TEXT
            )
        """))


def seed_source_from_df(engine, df: pd.DataFrame) -> None:
    df.to_sql(SOURCE_TABLE, con=engine, if_exists="append", index=False)


def get_watermark(engine) -> str | None:
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT watermark_val FROM pipeline_state WHERE pipeline_name = :name"),
            {"name": PIPELINE_NAME},
        ).fetchone()
    return row[0] if row else None


def _save_watermark(engine, watermark_val: str, rows_extracted: int) -> None:
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
            {"name": PIPELINE_NAME, "col": WATERMARK_COL, "val": watermark_val,
             "now": now, "rows": rows_extracted},
        )


def _start_run_log(engine, watermark_before: str | None) -> int:
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


def _finish_run_log(engine, run_id, status, watermark_after, rows_extracted, rows_loaded, error=None):
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
            {"now": now, "status": status, "wm_after": watermark_after,
             "extracted": rows_extracted, "loaded": rows_loaded,
             "error": error, "run_id": run_id},
        )


def _extract(engine, watermark_before: str | None) -> pd.DataFrame:
    if watermark_before is None:
        return pd.read_sql(f"SELECT * FROM {SOURCE_TABLE} ORDER BY {WATERMARK_COL}", con=engine)
    watermark_dt   = datetime.fromisoformat(watermark_before)
    safe_watermark = (watermark_dt - timedelta(seconds=LOOKBACK_SECS)).isoformat()
    return pd.read_sql(
        text(f"SELECT * FROM {SOURCE_TABLE} WHERE {WATERMARK_COL} > :wm ORDER BY {WATERMARK_COL}"),
        con=engine,
        params={"wm": safe_watermark},
    )


def _transform(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    df["status"] = df["status"].str.lower().str.strip()
    df["amount_category"] = pd.cut(
        df["amount"],
        bins=[0, 50, 200, 600, float("inf")],
        labels=["low", "medium", "high", "premium"],
        right=True,
    ).astype(str)
    df["_pipeline_loaded"] = datetime.now(timezone.utc).isoformat()
    return df


def _load(engine, df: pd.DataFrame) -> int:
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

    return result_upd.rowcount + result_ins.rowcount


def run_pipeline(engine) -> dict:
    watermark_before = get_watermark(engine)
    run_id = _start_run_log(engine, watermark_before)
    rows_extracted = 0
    rows_loaded    = 0

    try:
        df_raw   = _extract(engine, watermark_before)
        rows_extracted = len(df_raw)

        if df_raw.empty:
            _finish_run_log(engine, run_id, "success", watermark_before, 0, 0)
            return {"run_id": run_id, "status": "success", "rows_extracted": 0, "rows_loaded": 0}

        df_clean   = _transform(df_raw)
        rows_loaded = _load(engine, df_clean)

        watermark_after = df_raw[WATERMARK_COL].max()
        if hasattr(watermark_after, "isoformat"):
            watermark_after = watermark_after.isoformat()
        else:
            watermark_after = str(watermark_after)

        _save_watermark(engine, watermark_after, rows_extracted)
        _finish_run_log(engine, run_id, "success", watermark_after, rows_extracted, rows_loaded)

        return {
            "run_id": run_id, "status": "success",
            "rows_extracted": rows_extracted, "rows_loaded": rows_loaded,
            "watermark_before": watermark_before, "watermark_after": watermark_after,
        }

    except Exception as exc:
        _finish_run_log(engine, run_id, "failed", watermark_before, rows_extracted, rows_loaded, traceback.format_exc())
        return {"run_id": run_id, "status": "failed", "error": str(exc)}
