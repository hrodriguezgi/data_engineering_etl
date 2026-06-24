# %% [markdown]
# # Module 4 - Lesson 2: A Simple End-to-End ETL Pipeline
#
# This lesson builds a complete, working ETL pipeline:
# - **EXTRACT** → Read raw sales data from CSV
# - **TRANSFORM** → Clean, validate, and calculate derived fields
# - **LOAD** → Write clean data to a SQLite database
#
# The real data has intentional messiness:
# - Non-numeric quantities ("abc")
# - Negative prices (business rule violation)
# - Missing customer IDs
# - Missing or out-of-range discounts
# - Outlier prices
#
# **What You'll Learn:**
# - Reading CSV files safely (avoiding silent type conversions)
# - Handling missing data strategically
# - Computing derived fields
# - Writing to databases with SQLite
# - Idempotent loading patterns

import logging
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import create_engine

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("simple_etl")

# File paths
MODULE_DIR = Path(__file__).parent
DATA_DIR = MODULE_DIR / "data"
DB_PATH = MODULE_DIR / "etl_output.db"


# %% [markdown]
# ## Problem 1: Silent Type Conversions Break Pipelines
#
# **Scenario:** You read a CSV file and pandas silently converts "abc" to NaN.
# You don't notice. Later, you aggregate revenue and get wrong numbers because
# qty="abc" was silently dropped.
#
# **The Cost:** Silent data loss, wrong analytics, undetected errors.

# %%
# WRONG: Using default pandas read_csv
import io

bad_csv = """id,product,qty,price
1,Laptop,5,999
2,Monitor,abc,299
3,Keyboard,2,49
"""

# Bad: Default behavior auto-converts bad values to NaN
bad_df = pd.read_csv(io.StringIO(bad_csv))
print("WRONG: Using default read_csv (silent conversions):")
print(bad_df)
print(f"  Note: qty is {bad_df['qty'].dtype} — 'abc' became NaN silently!\n")

# %%
# RIGHT: Read everything as strings, then validate
good_df = pd.read_csv(
    io.StringIO(bad_csv),
    dtype=str,  # Read ALL columns as strings first
    keep_default_na=False,  # Don't auto-convert empty strings to NaN
)
print("CORRECT: Using dtype=str to prevent silent conversions:")
print(good_df)
print("  Note: qty='abc' is preserved as string. We can detect and reject it!\n")


# %% [markdown]
# ## Problem 2: Modifying DataFrames During Transform
#
# **Scenario:** You transform a DataFrame column and forget it's modifying the original.
# Later, you try to reload and get duplicates or corrupted data.

# %%
# WRONG: In-place modifications without copies
test_df = pd.DataFrame({"id": [1, 2, 3], "price": [10.0, 20.0, 30.0]})
print("WRONG: In-place modifications:")
print(f"Before: {test_df['price'].tolist()}")

# This modifies the original!
test_df["price"] = test_df["price"] * 1.1  # Apply 10% markup

print(f"After: {test_df['price'].tolist()}")
print("  If you reload the source, you'll process modified data!\n")

# %%
# RIGHT: Always work on copies during transform
test_df_2 = pd.DataFrame({"id": [1, 2, 3], "price": [10.0, 20.0, 30.0]})
print("CORRECT: Always use .copy():")

df_transform = test_df_2.copy()  # Copy first
print(f"Before: {test_df_2['price'].tolist()}")

df_transform["price"] = df_transform["price"] * 1.1
print(f"After transform: {df_transform['price'].tolist()}")
print(f"Original unchanged: {test_df_2['price'].tolist()}")
print()


# %% [markdown]
# ## EXTRACT Phase: Reading CSV Safely


# %%
def extract(filepath: Path) -> pd.DataFrame:
    """
    Extract raw sales data from CSV.

    Key decisions:
    - Read all columns as strings (no auto-conversions)
    - Keep empty strings as-is (don't convert to NaN)
    - This gives us control over type parsing in Transform

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

    # Key: Read all as strings to avoid silent conversions
    df = pd.read_csv(
        filepath,
        dtype=str,  # Preserve everything as-is
        keep_default_na=False,  # Don't convert empty strings to NaN yet
    )

    logger.info(f"[EXTRACT] Loaded {len(df)} rows, {df.shape[1]} columns")
    logger.debug(f"[EXTRACT] Columns: {list(df.columns)}")

    return df


# %% [markdown]
# ## TRANSFORM Phase: Clean, Validate, Reshape


# %%
def transform(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Transform and clean raw sales data.

    Steps:
    1. Strip whitespace from all strings
    2. Parse numeric fields with explicit error handling
    3. Reject rows that fail validation
    4. Calculate derived fields
    5. Add metadata

    Args:
        df: Raw DataFrame from Extract phase.

    Returns:
        Tuple of (clean_df, rejected_df).
    """
    logger.info(f"[TRANSFORM] Starting transformation of {len(df)} rows")

    # Always copy — never mutate input
    df = df.copy()

    # --- Step 1: Strip whitespace from all string columns ---
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()

    # Replace empty strings with None for consistent null handling
    df = df.replace("", None)

    # --- Step 2: Track which rows should be rejected ---
    rejected_rows = []

    # --- Step 3: Parse 'id' column ---
    df["id"] = pd.to_numeric(df["id"], errors="coerce")

    # --- Step 4: Parse 'sale_date' ---
    df["sale_date"] = pd.to_datetime(df["sale_date"], errors="coerce")

    # --- Step 5: Parse 'qty' — reject non-numeric ---
    df["qty_parsed"] = pd.to_numeric(df["qty"], errors="coerce")

    invalid_qty_mask = df["qty_parsed"].isnull() & df["qty"].notna()
    for idx in df[invalid_qty_mask].index:
        rejected_rows.append({**df.loc[idx].to_dict(), "_rejection_reason": f"invalid_qty: '{df.loc[idx, 'qty']}'"})
    logger.warning(f"[TRANSFORM] {invalid_qty_mask.sum()} rows with invalid qty")

    df["qty"] = df["qty_parsed"].fillna(1).astype(int)  # Default qty=1 if null
    df = df.drop(columns=["qty_parsed"])

    # --- Step 6: Parse 'price' — reject if missing ---
    df["price"] = pd.to_numeric(df["price"], errors="coerce")

    invalid_price_mask = df["price"].isnull()
    for idx in df[invalid_price_mask].index:
        if df.loc[idx, "id"] not in [r.get("id") for r in rejected_rows]:
            rejected_rows.append({**df.loc[idx].to_dict(), "_rejection_reason": "missing_price"})

    # --- Step 7: Parse 'discount' — fill missing with 0.0 ---
    df["discount"] = pd.to_numeric(df["discount"], errors="coerce").fillna(0.0)
    # Clip discount to valid range [0, 1]
    df["discount"] = df["discount"].clip(lower=0.0, upper=1.0)

    # --- Step 8: Fill missing customer_id ---
    df["customer_id"] = df["customer_id"].fillna("UNKNOWN")

    # --- Step 9: Business rule — reject negative prices ---
    negative_price_mask = df["price"] < 0
    for idx in df[negative_price_mask].index:
        rejected_rows.append({**df.loc[idx].to_dict(), "_rejection_reason": f"negative_price: {df.loc[idx, 'price']}"})
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
        next((r["_rejection_reason"] for r in rejected_rows if r.get("id") == row_id), "negative_price")
        for row_id in rejected_df["id"]
    ]

    clean_df = df[~rejection_mask].copy()
    clean_df = clean_df.dropna(subset=["price"])  # Drop rows with no price

    # --- Step 11: Calculate net_amount (derived field) ---
    clean_df["net_amount"] = (clean_df["qty"] * clean_df["price"] * (1 - clean_df["discount"])).round(2)

    # --- Step 12: Add ETL metadata ---
    clean_df["_etl_loaded_at"] = datetime.now(timezone.utc).isoformat()

    # --- Step 13: Normalize text columns ---
    clean_df["region"] = clean_df["region"].str.title()
    clean_df["product_name"] = clean_df["product_name"].str.strip()

    logger.info(f"[TRANSFORM] Complete: {len(clean_df)} valid, {len(rejected_df)} rejected from {len(df)} total")

    return clean_df, rejected_df


# %% [markdown]
# ## LOAD Phase: Write to Database (Idempotently)


# %%
def load(clean_df: pd.DataFrame, rejected_df: pd.DataFrame, engine) -> dict:
    """
    Load clean and rejected records to SQLite.

    Two tables:
    - 'sales': clean, validated records
    - 'sales_rejected': rejected records with reasons

    Args:
        clean_df: DataFrame of valid records.
        rejected_df: DataFrame of rejected records.
        engine: SQLAlchemy engine.

    Returns:
        Dict with load statistics.
    """
    logger.info("[LOAD] Writing to database")

    # Columns to write for the clean table
    clean_cols = [
        "id",
        "sale_date",
        "customer_id",
        "product_name",
        "qty",
        "price",
        "discount",
        "region",
        "net_amount",
        "is_price_outlier",
        "_etl_loaded_at",
    ]
    clean_to_write = clean_df[[c for c in clean_cols if c in clean_df.columns]]

    # Write clean records (replace = idempotent)
    clean_to_write.to_sql(
        "sales",
        con=engine,
        if_exists="replace",  # Truncate and reload (idempotent)
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


# %% [markdown]
# ## Run the Pipeline


# %%
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


# %% [markdown]
# ## Verify Results with Queries

# %%
if __name__ == "__main__":
    # Run the pipeline
    stats = run_pipeline(DATA_DIR / "raw_sales.csv", DB_PATH)

    print("\n" + "=" * 60)
    print("VERIFICATION QUERIES")
    print("=" * 60)

    engine = create_engine(f"sqlite:///{DB_PATH}")

    # Show the clean sales table
    print("\n[Clean Sales Table]")
    clean = pd.read_sql("SELECT * FROM sales ORDER BY id", con=engine)
    print(f"  {len(clean)} rows loaded")
    print(clean.to_string())

    # Show rejected records
    print("\n[Rejected Records]")
    try:
        rejected = pd.read_sql("SELECT id, product_name, qty, price, _rejection_reason FROM sales_rejected", con=engine)
        print(f"  {len(rejected)} rows rejected")
        print(rejected.to_string())
    except Exception:
        print("  No rejected records found")

    # Summary by region
    print("\n[Revenue by Region]")
    region_summary = pd.read_sql(
        """
        SELECT region, COUNT(*) AS orders, ROUND(SUM(net_amount), 2) AS total_revenue
        FROM sales
        GROUP BY region
        ORDER BY total_revenue DESC
    """,
        con=engine,
    )
    print(region_summary.to_string())

    # Outlier detection
    print("\n[Outlier Prices (>2000)]")
    outliers = pd.read_sql(
        """
        SELECT id, product_name, price FROM sales
        WHERE is_price_outlier = 1
    """,
        con=engine,
    )
    if len(outliers) > 0:
        print(outliers.to_string())
    else:
        print("  No outliers found")

    # Clean up
    engine.dispose()
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"\n✓ Cleaned up {DB_PATH.name}")
