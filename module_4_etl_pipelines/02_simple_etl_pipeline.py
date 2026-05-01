"""
Module 4 - Lesson 2: A Simple End-to-End ETL Pipeline
======================================================
This lesson builds a complete, working ETL pipeline:
  EXTRACT  → Read raw sales data from CSV
  TRANSFORM → Clean, validate, and calculate derived fields
  LOAD     → Write clean data to a SQLite database

This pipeline handles the real-world messiness in data/raw_sales.csv:
  - Non-numeric quantities ("abc")
  - Negative prices (business rule violation)
  - Missing customer IDs
  - Missing or out-of-range discounts
  - Outlier prices

By the end, the clean data is in a queryable SQLite database.
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import create_engine, text

# File paths
MODULE_DIR = Path(__file__).parent
DATA_DIR = MODULE_DIR / "data"
DB_PATH = MODULE_DIR / "etl_output.db"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("simple_etl")


# =============================================================================
# EXTRACT PHASE
# =============================================================================

def extract(filepath: Path) -> pd.DataFrame:
    """
    Extract raw sales data from CSV.

    Minimal processing here — we read the data as-is and let
    the Transform phase handle cleaning. The only exception is
    keeping all values as their raw types so we can inspect them.

    Args:
        filepath: Path to the raw CSV file.

    Returns:
        Raw DataFrame with all rows and original values.

    Raises:
        FileNotFoundError: If the CSV file doesn't exist.
    """
    logger.info(f"[EXTRACT] Reading from {filepath.name}")

    if not filepath.exists():
        raise FileNotFoundError(f"Source file not found: {filepath}")

    # dtype=str keeps EVERYTHING as strings — we'll parse types in Transform
    # This prevents pandas from silently converting bad values
    df = pd.read_csv(
        filepath,
        dtype=str,          # read all columns as strings to avoid auto-conversion issues
        keep_default_na=False,  # don't auto-convert empty strings to NaN yet
    )

    logger.info(f"[EXTRACT] Loaded {len(df)} rows, {df.shape[1]} columns")
    logger.debug(f"[EXTRACT] Columns: {list(df.columns)}")

    return df


# =============================================================================
# TRANSFORM PHASE
# =============================================================================

def transform(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Transform and clean raw sales data.

    Cleaning rules applied:
      1. Strip whitespace from all string columns
      2. Parse 'id' as integer
      3. Parse 'sale_date' as date
      4. Parse 'qty' as integer — reject rows where conversion fails
      5. Parse 'price' as float — reject rows where conversion fails
      6. Fill missing 'discount' with 0.0
      7. Fill missing 'customer_id' with 'UNKNOWN'
      8. Reject rows with negative prices (business rule)
      9. Flag outlier prices (> 2000) for review
      10. Calculate 'net_amount' = qty * price * (1 - discount)

    Args:
        df: Raw DataFrame from Extract phase.

    Returns:
        Tuple of (clean_df, rejected_df).
    """
    logger.info(f"[TRANSFORM] Starting transformation of {len(df)} rows")

    # Work on a copy — never mutate the input
    df = df.copy()

    # --- Step 1: Strip whitespace from all string columns ---
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()

    # Replace empty strings with None/NaN so we can use isnull() checks
    df = df.replace("", None)

    # --- Step 2: Track which rows should be rejected ---
    # We use a mask to accumulate rejection reasons
    rejected_rows = []

    # --- Step 3: Parse 'id' column ---
    df["id"] = pd.to_numeric(df["id"], errors="coerce")

    # --- Step 4: Parse 'sale_date' ---
    df["sale_date"] = pd.to_datetime(df["sale_date"], errors="coerce")

    # --- Step 5: Parse 'qty' — reject non-numeric ---
    df["qty_parsed"] = pd.to_numeric(df["qty"], errors="coerce")

    invalid_qty_mask = df["qty_parsed"].isnull() & df["qty"].notna()
    for idx in df[invalid_qty_mask].index:
        rejected_rows.append({
            **df.loc[idx].to_dict(),
            "_rejection_reason": f"invalid_qty: '{df.loc[idx, 'qty']}'"
        })
    logger.warning(f"[TRANSFORM] {invalid_qty_mask.sum()} rows with invalid qty")

    df["qty"] = df["qty_parsed"].fillna(1).astype(int)  # default qty=1 if null
    df = df.drop(columns=["qty_parsed"])

    # --- Step 6: Parse 'price' — reject non-numeric ---
    df["price"] = pd.to_numeric(df["price"], errors="coerce")

    invalid_price_mask = df["price"].isnull()
    for idx in df[invalid_price_mask].index:
        if df.loc[idx, "id"] not in [r.get("id") for r in rejected_rows]:
            rejected_rows.append({
                **df.loc[idx].to_dict(),
                "_rejection_reason": "missing_price"
            })

    # --- Step 7: Parse 'discount' — fill missing with 0.0 ---
    df["discount"] = pd.to_numeric(df["discount"], errors="coerce").fillna(0.0)
    # Clip discount to valid range [0, 1]
    df["discount"] = df["discount"].clip(lower=0.0, upper=1.0)

    # --- Step 8: Fill missing customer_id ---
    df["customer_id"] = df["customer_id"].fillna("UNKNOWN")

    # --- Step 9: Business rule — reject negative prices ---
    negative_price_mask = df["price"] < 0
    for idx in df[negative_price_mask].index:
        rejected_rows.append({
            **df.loc[idx].to_dict(),
            "_rejection_reason": f"negative_price: {df.loc[idx, 'price']}"
        })
    logger.warning(f"[TRANSFORM] {negative_price_mask.sum()} rows with negative prices")

    # --- Step 10: Flag outlier prices (price > 2000) ---
    df["is_price_outlier"] = df["price"] > 2000
    outlier_count = df["is_price_outlier"].sum()
    if outlier_count > 0:
        logger.warning(f"[TRANSFORM] {outlier_count} rows with outlier prices (>2000)")

    # --- Build the rejection index ---
    rejected_ids = {r.get("id") for r in rejected_rows}
    rejection_mask = df["id"].isin(rejected_ids) | negative_price_mask

    rejected_df = df[rejection_mask].copy()
    rejected_df["_rejection_reason"] = [
        next((r["_rejection_reason"] for r in rejected_rows
              if r.get("id") == row_id), "negative_price")
        for row_id in rejected_df["id"]
    ]

    clean_df = df[~rejection_mask].copy()
    clean_df = clean_df.dropna(subset=["price"])  # drop rows with no price

    # --- Step 11: Calculate net_amount ---
    clean_df["net_amount"] = (
        clean_df["qty"] * clean_df["price"] * (1 - clean_df["discount"])
    ).round(2)

    # --- Step 12: Add ETL metadata ---
    clean_df["_etl_loaded_at"] = datetime.now(timezone.utc).isoformat()

    # --- Step 13: Normalize text columns ---
    clean_df["region"] = clean_df["region"].str.title()
    clean_df["product_name"] = clean_df["product_name"].str.strip()

    logger.info(
        f"[TRANSFORM] Complete: {len(clean_df)} valid, "
        f"{len(rejected_df)} rejected from {len(df)} total"
    )

    return clean_df, rejected_df


# =============================================================================
# LOAD PHASE
# =============================================================================

def load(clean_df: pd.DataFrame, rejected_df: pd.DataFrame, engine) -> dict:
    """
    Load clean and rejected records to SQLite.

    Two tables are written:
      - 'sales': clean, validated records
      - 'sales_rejected': rejected records with rejection reasons

    Args:
        clean_df: DataFrame of valid records.
        rejected_df: DataFrame of rejected records.
        engine: SQLAlchemy engine.

    Returns:
        Dict with load statistics.
    """
    logger.info(f"[LOAD] Writing to database")

    # Columns to write for the clean table
    clean_cols = [
        "id", "sale_date", "customer_id", "product_name",
        "qty", "price", "discount", "region", "net_amount",
        "is_price_outlier", "_etl_loaded_at"
    ]
    clean_to_write = clean_df[[c for c in clean_cols if c in clean_df.columns]]

    # Write clean records
    clean_to_write.to_sql(
        "sales",
        con=engine,
        if_exists="replace",  # truncate and reload on each run (idempotent)
        index=False,
    )
    logger.info(f"[LOAD] Wrote {len(clean_to_write)} rows to 'sales' table")

    # Write rejected records (for audit/debugging)
    if len(rejected_df) > 0:
        rejected_df.to_sql(
            "sales_rejected",
            con=engine,
            if_exists="replace",
            index=False,
        )
        logger.info(f"[LOAD] Wrote {len(rejected_df)} rows to 'sales_rejected' table")

    return {
        "loaded_clean": len(clean_to_write),
        "loaded_rejected": len(rejected_df),
    }


# =============================================================================
# PIPELINE RUNNER
# =============================================================================

def run_pipeline(source_file: Path, db_path: Path) -> dict:
    """
    Run the full ETL pipeline.

    Args:
        source_file: Path to the raw CSV file.
        db_path: Path to the output SQLite database.

    Returns:
        Pipeline run statistics.
    """
    start = datetime.now(timezone.utc)
    logger.info("=" * 50)
    logger.info("PIPELINE STARTED: simple_etl")
    logger.info("=" * 50)

    stats = {}

    try:
        # Create database engine
        engine = create_engine(f"sqlite:///{db_path}")

        # EXTRACT
        raw_df = extract(source_file)
        stats["extracted"] = len(raw_df)

        # TRANSFORM
        clean_df, rejected_df = transform(raw_df)
        stats["transformed_valid"] = len(clean_df)
        stats["transformed_rejected"] = len(rejected_df)

        # LOAD
        load_stats = load(clean_df, rejected_df, engine)
        stats.update(load_stats)
        stats["status"] = "success"

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        stats["status"] = "failed"
        stats["error"] = str(e)
        raise

    finally:
        duration = (datetime.now(timezone.utc) - start).total_seconds()
        stats["duration_seconds"] = round(duration, 3)
        logger.info("=" * 50)
        logger.info(f"PIPELINE FINISHED: {stats['status']}")
        logger.info(f"Stats: {stats}")
        logger.info("=" * 50)

    return stats


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    # Run the pipeline
    stats = run_pipeline(DATA_DIR / "raw_sales.csv", DB_PATH)

    # Query the results to verify
    print("\n" + "=" * 60)
    print("VERIFICATION QUERIES")
    print("=" * 60)

    engine = create_engine(f"sqlite:///{DB_PATH}")

    # Show the clean sales table
    clean = pd.read_sql("SELECT * FROM sales ORDER BY id", con=engine)
    print(f"\nClean sales table ({len(clean)} rows):")
    print(clean.to_string())

    # Show rejected records
    try:
        rejected = pd.read_sql("SELECT id, product_name, qty, price, _rejection_reason FROM sales_rejected", con=engine)
        print(f"\nRejected records ({len(rejected)} rows):")
        print(rejected.to_string())
    except Exception:
        print("\nNo rejected records table found")

    # Summary by region
    print("\nRevenue by region:")
    region_summary = pd.read_sql("""
        SELECT region, COUNT(*) AS orders, ROUND(SUM(net_amount), 2) AS total_revenue
        FROM sales
        GROUP BY region
        ORDER BY total_revenue DESC
    """, con=engine)
    print(region_summary.to_string())

    # Clean up
    engine.dispose()
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"\nCleaned up {DB_PATH.name}")
