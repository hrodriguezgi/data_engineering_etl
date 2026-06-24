# %% [markdown]
# # Module 4 - Lesson 3: ETL with Complex Transformations
#
# In production pipelines, transformations go beyond simple cleaning.
# This lesson demonstrates advanced transformation patterns:
#
# - **Data normalization** — Making data consistent (casing, ranges, formats)
# - **Data enrichment** — Joining with reference/lookup tables
# - **Derived columns** — Calculated fields from multiple sources
# - **Aggregation** — Creating summary/dimension tables
# - **Business rules** — Applying domain logic (discounts, bonuses, etc.)
#
# **What You'll Learn:**
# - How to compose transformation functions safely
# - Lookup table patterns with pandas merge
# - Computing financial metrics correctly
# - Creating aggregated summaries for reporting
# - Handling date/time derivations

import logging
import numpy as np
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine

MODULE_DIR = Path(__file__).parent
DATA_DIR = MODULE_DIR / "data"
DB_PATH = MODULE_DIR / "etl_transformations_output.db"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("etl_transformations")


# %% [markdown]
# ## Reference Data (Lookup Tables)
#
# In real pipelines, this comes from a database or API.
# Here it's constants for simplicity.

# %%
REGION_METADATA = {
    "North": {"zone": "AMER-N", "currency": "USD", "tax_rate": 0.08},
    "South": {"zone": "AMER-S", "currency": "USD", "tax_rate": 0.07},
    "East": {"zone": "AMER-E", "currency": "USD", "tax_rate": 0.09},
    "West": {"zone": "AMER-W", "currency": "USD", "tax_rate": 0.085},
}

PRODUCT_CATEGORIES = {
    "Laptop Pro": "Laptops",
    "Wireless Mouse": "Peripherals",
    "Office Chair": "Furniture",
    "USB-C Hub": "Accessories",
    "Standing Desk": "Furniture",
    "Monitor 27": "Monitors",
    "Keyboard": "Peripherals",
    "Webcam HD": "Peripherals",
}

CUSTOMER_TIERS = {
    "C001": "vip",
    "C002": "member",
    "C003": "standard",
    "C004": "bulk",
    "C005": "member",
    "C006": "standard",
    "C007": "vip",
}


# %% [markdown]
# ## Problem 1: Lookup Joins That Lose Data
#
# **Scenario:** You join with a lookup table using `.map()` and all your
# unmatched products get NaN. You don't know which products are missing
# from the lookup, so you can't fix the data quality issue.
#
# **The Cost:** Silent data loss, downstream analytics with missing categories,
# inability to detect source data changes.

# %%
# WRONG: Using map() without visibility into missing keys
test_df = pd.DataFrame({"product": ["Laptop Pro", "Unknown Product", "Monitor 27"], "price": [999, 49, 399]})

print("WRONG: Using .map() without checking for NaN:")
test_df["category"] = test_df["product"].map(PRODUCT_CATEGORIES)
print(test_df)
print("  'Unknown Product' → NaN. You won't know it's missing!\n")

# %%
# RIGHT: Use merge() or map() with explicit handling
test_df_2 = pd.DataFrame({"product": ["Laptop Pro", "Unknown Product", "Monitor 27"], "price": [999, 49, 399]})

print("CORRECT: Handle missing lookups explicitly:")
test_df_2["category"] = test_df_2["product"].map(PRODUCT_CATEGORIES).fillna("Other")
print(test_df_2)
print("  'Unknown Product' → 'Other'. Visible and controllable!\n")


# %% [markdown]
# ## Problem 2: Composed Transformations Breaking the Chain
#
# **Scenario:** You have a transformation pipeline:
# normalize() → enrich() → derive_columns()
#
# But enrich() requires columns that normalize() was supposed to create.
# If normalize() fails silently, derive_columns() breaks mysteriously.

# %%
# WRONG: Assuming previous step created expected columns
test_sales = pd.DataFrame(
    {
        "product_name": ["  Laptop Pro  ", "MONITOR 27"],
        "region": ["  north  ", "SOUTH"],
    }
)


# normalize() doesn't return, just modifies in place (bad)
def bad_normalize(df):
    """Doesn't return anything."""
    df = df.copy()
    df["product_name"] = df["product_name"].str.strip().str.title()
    # BUG: forgot to return!


result = bad_normalize(test_sales)
print("WRONG: Transform doesn't return:")
print(f"  Result: {result}")
print("  It's None! Next step will crash!\n")


# %%
# RIGHT: Always return the modified DataFrame
def good_normalize(df: pd.DataFrame) -> pd.DataFrame:
    """✓ Always returns the transformed DataFrame."""
    df = df.copy()
    df["product_name"] = df["product_name"].str.strip().str.title()
    df["region"] = df["region"].str.strip().str.title()
    return df


result = good_normalize(test_sales)
print("CORRECT: Transform returns modified DataFrame:")
print(result)
print()


# %% [markdown]
# ## EXTRACT Phase


# %%
def extract(filepath: Path) -> pd.DataFrame:
    """Extract raw sales data."""
    logger.info(f"[EXTRACT] {filepath.name}")
    df = pd.read_csv(filepath, dtype=str, keep_default_na=False).replace("", None)

    # Quick type parsing
    df["qty"] = pd.to_numeric(df["qty"], errors="coerce").fillna(1).astype(int)
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["discount"] = pd.to_numeric(df["discount"], errors="coerce").fillna(0.0)
    df["sale_date"] = pd.to_datetime(df["sale_date"], errors="coerce")
    df["customer_id"] = df["customer_id"].fillna("UNKNOWN")
    df = df.dropna(subset=["price"])
    df = df[df["price"] > 0]

    logger.info(f"[EXTRACT] {len(df)} usable rows")
    return df


# %% [markdown]
# ## TRANSFORMATION 1: Normalization
#
# Make all data consistent: casing, ranges, formats.


# %%
def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize data for consistency.

    Args:
        df: Input DataFrame.

    Returns:
        Normalized DataFrame.
    """
    logger.info("[TRANSFORM] Normalizing data")
    df = df.copy()

    # Text normalization
    df["product_name"] = df["product_name"].str.strip().str.title()
    df["region"] = df["region"].str.strip().str.title().fillna("Unknown")
    df["customer_id"] = df["customer_id"].str.strip().str.upper()

    # Numeric normalization
    df["discount"] = df["discount"].clip(0.0, 1.0)
    df["price"] = df["price"].round(2)
    df["qty"] = df["qty"].clip(lower=1)

    return df


# %% [markdown]
# ## TRANSFORMATION 2: Enrichment (Lookups)
#
# Join with reference data to add context.


# %%
def enrich(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enrich records by joining with reference data.

    Adds:
    - product category from PRODUCT_CATEGORIES lookup
    - region metadata (zone, tax_rate) from REGION_METADATA
    - customer tier from CUSTOMER_TIERS

    Args:
        df: Normalized DataFrame.

    Returns:
        Enriched DataFrame.
    """
    logger.info("[TRANSFORM] Enriching with reference data")
    df = df.copy()

    # Enrich with product category
    df["category"] = df["product_name"].map(PRODUCT_CATEGORIES).fillna("Other")

    # Enrich with region metadata — expand nested dict to flat columns
    region_df = pd.DataFrame.from_dict(REGION_METADATA, orient="index").reset_index()
    region_df.columns = ["region", "zone", "currency", "tax_rate"]

    df = df.merge(region_df, on="region", how="left")
    df["zone"] = df["zone"].fillna("UNKNOWN")
    df["tax_rate"] = df["tax_rate"].fillna(0.08)

    # Enrich with customer tier
    df["customer_tier"] = df["customer_id"].map(CUSTOMER_TIERS).fillna("standard")

    return df


# %% [markdown]
# ## TRANSFORMATION 3: Derived Columns
#
# Compute calculated fields. Keep them separate for clarity and testability.


# %%
def derive_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute derived/calculated columns.

    Financial:
    - subtotal: qty * price
    - discount_amount: subtotal * discount
    - net_amount: subtotal - discount_amount
    - tax_amount: net_amount * tax_rate
    - loyalty_bonus: extra discount for VIP customers
    - final_amount: total after all adjustments

    Date/Time:
    - year, month, quarter from sale_date
    - is_weekend: True for Sat/Sun

    Business:
    - estimated_profit: based on category margins

    Args:
        df: Enriched DataFrame.

    Returns:
        DataFrame with derived columns.
    """
    logger.info("[TRANSFORM] Computing derived columns")
    df = df.copy()

    # Financial calculations
    df["subtotal"] = (df["qty"] * df["price"]).round(2)
    df["discount_amount"] = (df["subtotal"] * df["discount"]).round(2)
    df["net_amount"] = (df["subtotal"] - df["discount_amount"]).round(2)
    df["tax_amount"] = (df["net_amount"] * df["tax_rate"]).round(2)
    df["total_with_tax"] = (df["net_amount"] + df["tax_amount"]).round(2)

    # Loyalty bonus: VIP customers get an extra 5% discount
    df["loyalty_bonus"] = np.where(df["customer_tier"] == "vip", (df["net_amount"] * 0.05).round(2), 0.0)
    df["final_amount"] = (df["total_with_tax"] - df["loyalty_bonus"]).round(2)

    # Date derivations
    df["year"] = df["sale_date"].dt.year
    df["month"] = df["sale_date"].dt.month
    df["month_name"] = df["sale_date"].dt.strftime("%B")
    df["quarter"] = df["sale_date"].dt.quarter.map({1: "Q1", 2: "Q2", 3: "Q3", 4: "Q4"})
    df["day_of_week"] = df["sale_date"].dt.day_name()
    df["is_weekend"] = df["sale_date"].dt.dayofweek >= 5

    # Profit margin by category
    margin_by_category = {
        "Laptops": 0.15,
        "Peripherals": 0.40,
        "Accessories": 0.55,
        "Monitors": 0.25,
        "Furniture": 0.35,
        "Audio": 0.30,
        "Other": 0.20,
    }
    df["margin_pct"] = df["category"].map(margin_by_category).fillna(0.25)
    df["estimated_profit"] = (df["net_amount"] * df["margin_pct"]).round(2)

    return df


# %% [markdown]
# ## TRANSFORMATION 4: Aggregation
#
# Create summary tables for reporting/data warehouse.


# %%
def aggregate_by_product(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create product-level summary for dimension table.

    Args:
        df: Fully transformed DataFrame.

    Returns:
        Product summary by category.
    """
    logger.info("[TRANSFORM] Aggregating product summary")
    summary = (
        df.groupby(["product_name", "category"])
        .agg(
            total_orders=("id", "count"),
            total_units_sold=("qty", "sum"),
            total_revenue=("net_amount", "sum"),
            avg_unit_price=("price", "mean"),
            total_profit=("estimated_profit", "sum"),
        )
        .reset_index()
    )

    summary[["total_revenue", "avg_unit_price", "total_profit"]] = summary[
        ["total_revenue", "avg_unit_price", "total_profit"]
    ].round(2)

    return summary.sort_values("total_revenue", ascending=False)


# %% [markdown]
# ## LOAD Phase


# %%
def load(dfs: dict, engine) -> dict:
    """
    Load all DataFrames to the database.

    Args:
        dfs: Dict of table_name → DataFrame.
        engine: SQLAlchemy engine.

    Returns:
        Dict with row counts per table.
    """
    stats = {}
    for table_name, df in dfs.items():
        df.to_sql(table_name, con=engine, if_exists="replace", index=False)
        logger.info(f"[LOAD] {len(df)} rows → '{table_name}'")
        stats[table_name] = len(df)
    return stats


# %% [markdown]
# ## Run the Full Transformation Pipeline

# %%
if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("ETL WITH TRANSFORMATIONS PIPELINE")
    logger.info("=" * 50)

    # Extract
    raw_df = extract(DATA_DIR / "raw_sales.csv")

    # Transform pipeline: function composition
    df = raw_df.copy()
    df = normalize(df)
    df = enrich(df)
    df = derive_columns(df)
    product_summary = aggregate_by_product(df)

    # Select final columns for fact table
    fact_cols = [
        "id",
        "sale_date",
        "year",
        "month",
        "month_name",
        "quarter",
        "day_of_week",
        "is_weekend",
        "customer_id",
        "customer_tier",
        "product_name",
        "category",
        "region",
        "zone",
        "qty",
        "price",
        "subtotal",
        "discount",
        "discount_amount",
        "net_amount",
        "tax_rate",
        "tax_amount",
        "total_with_tax",
        "loyalty_bonus",
        "final_amount",
        "margin_pct",
        "estimated_profit",
    ]
    fact_df = df[[c for c in fact_cols if c in df.columns]].copy()

    # %% [markdown]
    # ## Verify Results

    # %%
    print("\n[Fact Sales Table]")
    print(f"  {len(fact_df)} rows")
    print(fact_df.head(5).to_string())

    print("\n[Product Summary]")
    print(f"  {len(product_summary)} rows")
    print(product_summary.to_string())

    # Load
    engine = create_engine(f"sqlite:///{DB_PATH}")
    load_stats = load({"fact_sales": fact_df, "dim_product_summary": product_summary}, engine)
    print(f"\n[Load Stats]: {load_stats}")

    # %% [markdown]
    # ## Post-Load Analytics

    # %%
    print("\n" + "=" * 50)
    print("POST-LOAD ANALYTICS")
    print("=" * 50)

    total_revenue = pd.read_sql("SELECT SUM(final_amount) AS total FROM fact_sales", con=engine)["total"].iloc[0]
    print(f"\nTotal revenue (after all deductions): ${total_revenue:,.2f}")

    region_rev = pd.read_sql(
        """
        SELECT region, COUNT(*) orders, ROUND(SUM(final_amount),2) revenue
        FROM fact_sales GROUP BY region ORDER BY revenue DESC
    """,
        con=engine,
    )
    print("\n[Revenue by Region]")
    print(region_rev.to_string(index=False))

    tier_rev = pd.read_sql(
        """
        SELECT customer_tier, COUNT(*) orders,
               ROUND(AVG(final_amount),2) avg_order,
               ROUND(SUM(loyalty_bonus),2) total_bonus
        FROM fact_sales GROUP BY customer_tier
    """,
        con=engine,
    )
    print("\n[By Customer Tier]")
    print(tier_rev.to_string(index=False))

    # Cleanup
    engine.dispose()
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"\n✓ Cleaned up {DB_PATH.name}")
