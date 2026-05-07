"""
upsert_helpers.py
-----------------
Importable upsert functions.
Used by 02_upsert_patterns.py and tests/test_module_5_incremental.py.
"""

import logging

import pandas as pd
from sqlalchemy import text

logger = logging.getLogger("etl.upsert")


def load_insert_or_ignore(engine, table_name: str, df: pd.DataFrame) -> int:
    inserted = 0
    cols = list(df.columns)
    col_list  = ", ".join(cols)
    val_list  = ", ".join(f":{c}" for c in cols)
    with engine.begin() as conn:
        for _, row in df.iterrows():
            result = conn.execute(
                text(f"INSERT OR IGNORE INTO {table_name} ({col_list}) VALUES ({val_list})"),
                row.to_dict(),
            )
            inserted += result.rowcount
    return inserted


def load_insert_or_replace(engine, table_name: str, df: pd.DataFrame) -> int:
    affected = 0
    cols     = list(df.columns)
    col_list = ", ".join(cols)
    val_list = ", ".join(f":{c}" for c in cols)
    with engine.begin() as conn:
        for _, row in df.iterrows():
            result = conn.execute(
                text(f"INSERT OR REPLACE INTO {table_name} ({col_list}) VALUES ({val_list})"),
                row.to_dict(),
            )
            affected += result.rowcount
    return affected


def load_staged_merge(engine, target_table: str, df: pd.DataFrame) -> dict:
    staging = f"{target_table}_staging"
    df.to_sql(staging, con=engine, if_exists="replace", index=False)

    # Build dynamic SET clause from non-PK columns
    non_pk_cols = [c for c in df.columns if c != "order_id"]
    set_clause  = ", ".join(f"{c} = s.{c}" for c in non_pk_cols)
    change_check = " OR ".join(f"{target_table}.{c} <> s.{c}" for c in non_pk_cols)

    insert_cols = ", ".join(df.columns)
    select_cols = ", ".join(f"s.{c}" for c in df.columns)

    with engine.begin() as conn:
        result_upd = conn.execute(text(f"""
            UPDATE {target_table}
            SET {set_clause}
            FROM {staging} AS s
            WHERE {target_table}.order_id = s.order_id
              AND ({change_check})
        """))
        result_ins = conn.execute(text(f"""
            INSERT INTO {target_table} ({insert_cols})
            SELECT {select_cols}
            FROM {staging} AS s
            WHERE NOT EXISTS (
                SELECT 1 FROM {target_table} t WHERE t.order_id = s.order_id
            )
        """))
        conn.execute(text(f"DROP TABLE IF EXISTS {staging}"))

    return {"inserted": result_ins.rowcount, "updated": result_upd.rowcount}
