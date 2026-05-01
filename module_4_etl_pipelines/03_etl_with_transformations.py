"""
Module 4 - Lesson 3: ETL with Complex Transformations
======================================================
In production pipelines, transformations go beyond simple cleaning.
This lesson demonstrates advanced transformation patterns:
  - Data normalization (consistent formats and scales)
  - Data enrichment (joining with reference/lookup tables)
  - Aggregation to create summary records
  - Derived columns (calculated from multiple fields)
  - Applying business rules as transformations

We build on the cleaned sales data from lesson 2.
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import create_engine, text

MODULE_DIR = Path(__file__).parent
DATA_DIR = MODULE_DIR / "data"
DB_PATH = MODULE_DIR / "etl_transformations_output.db"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("etl_transformations")


# =============================================================================
# LOOKUP / REFERENCE DATA
# =============================================================================

# In real pipelines, this might come from a database or API.
# Here we define it as constants for simplicity.

REGION_METADATA = {
    "North": {"zone": "AMER-N", "currency": "USD", "tax_rate": 0.08},
    "South": {"zone": "AMER-S", "currency": "USD", "tax_rate": 0.07},
    "East":  {"zone": "AMER-E", "currency": "USD", "tax_rate": 0.09},
    "West":  {"zone": "AMER-W", "currency": "USD", "tax_rate": 0.085},
}

PRODUCT_CATEGORIES = {
    "Laptop Pro":     "Laptops",
    "Wireless Mouse": "Peripherals",
    "Office Chair":   "Furniture",
    "USB-C Hub":      "Accessories",
    "Standing Desk":  "Furniture",
    "Monitor 27":     "Monitors",
    "Keyboard":       "Peripherals",
    "Webcam HD":      "Peripherals",
}

DISCOUNT_TIERS = {
    "standard": 0.0,
    "member":   0.05,
    "vip":      0.10,
    "bulk":     0.15,
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


# =============================================================================
# EXTRACT
# =============================================================================

def extract(filepath: Path) -> pd.DataFrame:
    """Extract raw sales data."""
    logger.info(f"[EXTRACT] {filepath.name}")
    df = pd.read_csv(filepath, dtype=str, keep_default_na=False).replace("", None)

    # Quick type parsing (minimal transform in extract)
    df["qty"] = pd.to_numeric(df["qty"], errors="coerce").fillna(1).astype(int)
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["discount"] = pd.to_numeric(df["discount"], errors="coerce").fillna(0.0)
    df["sale_date"] = pd.to_datetime(df["sale_date"], errors="coerce")
    df["customer_id"] = df["customer_id"].fillna("UNKNOWN")
    df = df.dropna(subset=["price"])
    df = df[df["price"] > 0]  # drop negative prices

    logger.info(f"[EXTRACT] {len(df)} usable rows")
    return df


# =============================================================================
# TRANSFORMATION 1: NORMALIZATION
# =============================================================================

def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize data for consistency:
      - Standardize text casing
      - Clip discount to [0, 1]
      - Normalize region names to title case
      - Fill missing regions

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
    df["qty"] = df["qty"].clip(lower=1)  # minimum qty is 1

    return df


# =============================================================================
# TRANSFORMATION 2: ENRICHMENT (LOOKUPS)
# =============================================================================

def enrich(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enrich records by joining with reference data:
      - Add product category from PRODUCT_CATEGORIES lookup
      - Add region metadata (zone, tax_rate) from REGION_METADATA
      - Add customer tier from CUSTOMER_TIERS

    This pattern is the pandas equivalent of a SQL JOIN with a lookup table.

    Args:
        df: Normalized DataFrame.

    Returns:
        Enriched DataFrame with additional columns.
    """
    logger.info("[TRANSFORM] Enriching with reference data")
    df = df.copy()

    # Enrich with product category
    df["category"] = df["product_name"].map(PRODUCT_CATEGORIES).fillna("Other")

    # Enrich with region metadata — expand the nested dict to flat columns
    region_df = pd.DataFrame.from_dict(REGION_METADATA, orient="index").reset_index()
    region_df.columns = ["region", "zone", "currency", "tax_rate"]

    df = df.merge(region_df, on="region", how="left")
    df["zone"] = df["zone"].fillna("UNKNOWN")
    df["tax_rate"] = df["tax_rate"].fillna(0.08)  # default tax rate

    # Enrich with customer tier
    df["customer_tier"] = df["customer_id"].map(CUSTOMER_TIERS).fillna("standard")

    return df


# =============================================================================
# TRANSFORMATION 3: DERIVED COLUMNS
# =============================================================================

def derive_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute derived/calculated columns:
      - subtotal: qty * price
      - discount_amount: subtotal * discount
      - net_amount: subtotal - discount_amount
      - tax_amount: net_amount * tax_rate
      - total_with_tax: net_amount + tax_amount
      - Date parts: year, month, quarter, day_of_week
      - is_weekend: True if sale was on Saturday/Sunday
      - loyalty_bonus: extra discount for VIP customers
      - profit_margin_pct: simulated margin based on category

    Args:
        df: Enriched DataFrame.

    Returns:
        DataFrame with all derived columns added.
    """
    logger.info("[TRANSFORM] Computing derived columns")
    df = df.copy()

    # Financial calculations
    df["subtotal"] = (df["qty"] * df["price"]).round(2)
    df["discount_amount"] = (df["subtotal"] * df["discount"]).round(2)
    df["net_amount"] = (df["subtotal"] - df["discount_amount"]).round(2)
    df["tax_amount"] = (df["net_amount"] * df["tax_rate"]).round(2)
    df["total_with_tax"] = (df["net_amount"] + df["tax_amount"]).round(2)

    # Loyalty bonus: VIP customers get an extra 5% discount on top
    df["loyalty_bonus"] = np.where(
        df["customer_tier"] == "vip",
        (df["net_amount"] * 0.05).round(2),
        0.0
    )
    df["final_amount"] = (df["total_with_tax"] - df["loyalty_bonus"]).round(2)

    # Date derivations
    df["year"] = df["sale_date"].dt.year
    df["month"] = df["sale_date"].dt.month
    df["month_name"] = df["sale_date"].dt.strftime("%B")
    df["quarter"] = df["sale_date"].dt.quarter.map({1: "Q1", 2: "Q2", 3: "Q3", 4: "Q4"})
    df["day_of_week"] = df["sale_date"].dt.day_name()
    df["is_weekend"] = df["sale_date"].dt.dayofweek >= 5  # 5=Sat, 6=Sun

    # Simulated profit margin by category
    margin_by_category = {
        "Laptops": 0.15, "Peripherals": 0.40, "Accessories": 0.55,
        "Monitors": 0.25, "Furniture": 0.35, "Audio": 0.30, "Other": 0.20
    }
    df["margin_pct"] = df["category"].map(margin_by_category).fillna(0.25)
    df["estimated_profit"] = (df["net_amount"] * df["margin_pct"]).round(2)

    return df


# =============================================================================
# TRANSFORMATION 4: AGGREGATION
# =============================================================================

def aggregate_by_product(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a product-level summary for the data warehouse dimension table.

    Args:
        df: Fully derived DataFrame.

    Returns:
        Product summary DataFrame.
    """
    logger.info("[TRANSFORM] Aggregating product summary")
    summary = df.groupby(["product_name", "category"]).agg(
        total_orders=("id", "count"),
        total_units_sold=("qty", "sum"),
        total_revenue=("net_amount", "sum"),
        avg_unit_price=("price", "mean"),
        total_profit=("estimated_profit", "sum"),
    ).reset_index()

    summary[["total_revenue", "avg_unit_price", "total_profit"]] = \
        summary[["total_revenue", "avg_unit_price", "total_profit"]].round(2)

    return summary.sort_values("total_revenue", ascending=False)


# =============================================================================
# LOAD
# =============================================================================

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


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("ETL WITH TRANSFORMATIONS PIPELINE")
    logger.info("=" * 50)

    # Extract
    raw_df = extract(DATA_DIR / "raw_sales.csv")

    # Transform pipeline (function composition)
    df = raw_df.copy()
    df = normalize(df)
    df = enrich(df)
    df = derive_columns(df)
    product_summary = aggregate_by_product(df)

    # Select final columns for the main table
    fact_cols = [
        "id", "sale_date", "year", "month", "month_name", "quarter", "day_of_week", "is_weekend",
        "customer_id", "customer_tier", "product_name", "category",
        "region", "zone", "qty", "price",
        "subtotal", "discount", "discount_amount", "net_amount",
        "tax_rate", "tax_amount", "total_with_tax",
        "loyalty_bonus", "final_amount",
        "margin_pct", "estimated_profit",
    ]
    fact_df = df[[c for c in fact_cols if c in df.columns]].copy()

    print(f"\nTransformed sales fact table ({len(fact_df)} rows):")
    print(fact_df.head(5).to_string())

    print(f"\nProduct summary ({len(product_summary)} rows):")
    print(product_summary.to_string())

    # Load
    engine = create_engine(f"sqlite:///{DB_PATH}")
    load_stats = load(
        {"fact_sales": fact_df, "dim_product_summary": product_summary},
        engine
    )
    print(f"\nLoad stats: {load_stats}")

    # Quick analytics
    print("\n" + "=" * 50)
    print("POST-LOAD ANALYTICS")
    print("=" * 50)

    total_revenue = pd.read_sql(
        "SELECT SUM(final_amount) AS total FROM fact_sales", con=engine
    )["total"].iloc[0]
    print(f"Total revenue (after all deductions): ${total_revenue:,.2f}")

    region_rev = pd.read_sql("""
        SELECT region, COUNT(*) orders, ROUND(SUM(final_amount),2) revenue
        FROM fact_sales GROUP BY region ORDER BY revenue DESC
    """, con=engine)
    print(f"\nRevenue by region:\n{region_rev}")

    tier_rev = pd.read_sql("""
        SELECT customer_tier, COUNT(*) orders,
               ROUND(AVG(final_amount),2) avg_order,
               ROUND(SUM(loyalty_bonus),2) total_bonus
        FROM fact_sales GROUP BY customer_tier
    """, con=engine)
    print(f"\nBy customer tier:\n{tier_rev}")

    # Cleanup
    engine.dispose()
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"\nCleaned up {DB_PATH.name}")
