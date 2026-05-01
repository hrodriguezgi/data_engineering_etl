"""
Module 2 - Lesson 3: Data Transformation with Pandas
======================================================
After cleaning, we transform data into the shape needed for analysis or
loading into a target database. Transformations include:
  - Computing new columns
  - Applying custom functions row-by-row or element-by-element
  - Binning/bucketing continuous values
  - Reshaping: wide to long (melt) and long to wide (pivot)

Topics covered:
  - apply() — apply a function to rows or columns
  - map() — element-wise mapping on a Series
  - Vectorized operations (fast, Pythonic)
  - pd.cut() and pd.qcut() — binning
  - pivot_table() — reshape long to wide
  - melt() — reshape wide to long
  - stack() and unstack()
"""

import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

# Load and clean data first (reuse cleaning steps from lesson 2)
def load_clean_sales() -> pd.DataFrame:
    """Load and minimally clean the sales dataset."""
    df = pd.read_csv(DATA_DIR / "sales.csv")
    df = df.drop_duplicates(subset=["order_id"], keep="first").copy()
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(1).astype(int)
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    df["unit_price"] = df["unit_price"].fillna(df["unit_price"].median())
    df["region"] = df["region"].fillna("Unknown")
    df["customer_name"] = df["customer_name"].fillna("Anonymous")
    df["date"] = pd.to_datetime(df["date"])
    return df

df = load_clean_sales()
print(f"Loaded {len(df)} rows")


# =============================================================================
# 1. VECTORIZED OPERATIONS
# =============================================================================

print("=" * 60)
print("1. VECTORIZED OPERATIONS (preferred approach)")
print("=" * 60)

# Vectorized operations work on the entire column at once — they are
# implemented in C under the hood and are much faster than Python loops.

# Simple arithmetic
df["total_amount"] = df["quantity"] * df["unit_price"]
df["discounted_amount"] = df["total_amount"] * 0.9   # 10% discount
df["tax_amount"] = df["total_amount"] * 0.08          # 8% tax

# Round to 2 decimal places
df[["total_amount", "discounted_amount", "tax_amount"]] = (
    df[["total_amount", "discounted_amount", "tax_amount"]].round(2)
)

print("Computed financial columns:")
print(df[["order_id", "quantity", "unit_price", "total_amount", "tax_amount"]].head(8))

# Conditional column using np.where (vectorized if-else)
# np.where(condition, value_if_true, value_if_false)
df["is_high_value"] = np.where(df["total_amount"] > 500, "High", "Standard")
print(f"\nHigh-value orders: {(df['is_high_value'] == 'High').sum()}")

# np.select for multiple conditions (vectorized elif chain)
conditions = [
    df["total_amount"] >= 1000,
    df["total_amount"] >= 500,
    df["total_amount"] >= 200,
]
choices = ["Platinum", "Gold", "Silver"]
df["tier"] = np.select(conditions, choices, default="Bronze")
print(f"\nOrder tier distribution:\n{df['tier'].value_counts()}")


# =============================================================================
# 2. APPLY() — CUSTOM TRANSFORMATIONS
# =============================================================================

print("\n" + "=" * 60)
print("2. APPLY()")
print("=" * 60)

# apply() lets you run a custom Python function on each element (element-wise),
# each row, or each column.
# Use it when vectorized operations aren't possible. It's slower than vectorized ops.

# --- apply() on a Series (element-wise) ---
def categorize_price(price: float) -> str:
    """Categorize a unit price into Budget/Mid/Premium."""
    if price < 50:
        return "Budget"
    elif price < 300:
        return "Mid-Range"
    else:
        return "Premium"

df["price_category"] = df["unit_price"].apply(categorize_price)
print("Price categories:")
print(df[["product", "unit_price", "price_category"]].head(8))

# Lambda with apply — for simple one-liner transformations
df["price_formatted"] = df["unit_price"].apply(lambda p: f"${p:,.2f}")
print(f"\nFormatted prices: {df['price_formatted'].head(5).tolist()}")

# --- apply() on a DataFrame row (axis=1) ---
# axis=0: apply function to each COLUMN
# axis=1: apply function to each ROW

def build_order_label(row) -> str:
    """Build a human-readable label from multiple columns in a row."""
    return f"{row['order_id']}: {row['customer_name']} bought {row['quantity']}x {row['product']}"

df["order_label"] = df.apply(build_order_label, axis=1)
print(f"\nOrder labels:")
for label in df["order_label"].head(5):
    print(f"  {label}")

# --- apply() on columns (axis=0) ---
# Compute stats for each numeric column at once
numeric_cols = ["quantity", "unit_price", "total_amount"]
col_stats = df[numeric_cols].apply(["mean", "std", "min", "max"])
print(f"\nColumn statistics:\n{col_stats.round(2)}")


# =============================================================================
# 3. MAP() — ELEMENT-WISE SERIES MAPPING
# =============================================================================

print("\n" + "=" * 60)
print("3. MAP() — Element-Wise Mapping")
print("=" * 60)

# map() applies a function or dictionary lookup to each element of a Series.
# It's similar to apply() on a Series but cannot handle NaN well by default.

# Using a dict — perfect for category/value lookups
region_full_names = {
    "North": "Northern Region",
    "South": "Southern Region",
    "East":  "Eastern Region",
    "West":  "Western Region",
    "Unknown": "Unspecified",
}
df["region_full"] = df["region"].map(region_full_names)
print(f"Region mapping:\n{df[['region', 'region_full']].drop_duplicates()}")

# Using a function
df["quantity_word"] = df["quantity"].map(
    lambda q: "single" if q == 1 else "multiple"
)
print(f"\nQuantity words: {df['quantity_word'].value_counts().to_dict()}")


# =============================================================================
# 4. BINNING — pd.cut() AND pd.qcut()
# =============================================================================

print("\n" + "=" * 60)
print("4. BINNING (pd.cut and pd.qcut)")
print("=" * 60)

# pd.cut() — divide values into FIXED-WIDTH bins (you define the boundaries)
# Useful when you have meaningful thresholds (e.g., age groups, price ranges)

price_bins = [0, 50, 200, 500, float("inf")]
price_labels = ["<$50", "$50-$200", "$200-$500", ">$500"]

df["price_bin"] = pd.cut(
    df["unit_price"],
    bins=price_bins,
    labels=price_labels,
    include_lowest=True
)
print("Price bins (pd.cut — fixed boundaries):")
print(df["price_bin"].value_counts().sort_index())

# pd.qcut() — divide values into QUANTILE bins (equal frequency)
# Useful when you want equal-sized groups regardless of value distribution
df["amount_quartile"] = pd.qcut(
    df["total_amount"],
    q=4,                          # 4 quartiles
    labels=["Q1", "Q2", "Q3", "Q4"],
    duplicates="drop"
)
print(f"\nAmount quartiles (pd.qcut — equal frequency):")
print(df["amount_quartile"].value_counts().sort_index())


# =============================================================================
# 5. PIVOT TABLES
# =============================================================================

print("\n" + "=" * 60)
print("5. PIVOT TABLES")
print("=" * 60)

# pivot_table() reshapes data from "long" to "wide" format.
# It's the pandas equivalent of Excel pivot tables.
# Great for creating summary views and reports.

# Total amount by category and region (crosstab-style)
pivot_sum = df.pivot_table(
    values="total_amount",
    index="category",       # rows
    columns="region",       # columns
    aggfunc="sum",          # aggregation function
    fill_value=0,           # fill missing combinations with 0
    margins=True,           # add row/column totals (labeled "All")
    margins_name="TOTAL"
)
print("Total amount by category and region:")
print(pivot_sum.round(2))

# Count of orders by tier and region
pivot_count = df.pivot_table(
    values="order_id",
    index="tier",
    columns="region",
    aggfunc="count",
    fill_value=0
)
print(f"\nOrder count by tier and region:")
print(pivot_count)

# Multiple aggregation functions
pivot_multi = df.pivot_table(
    values="total_amount",
    index="category",
    aggfunc={"total_amount": ["sum", "mean", "count"]}
)
print(f"\nMultiple aggs by category:")
print(pivot_multi.round(2))


# =============================================================================
# 6. MELT() — WIDE TO LONG FORMAT
# =============================================================================

print("\n" + "=" * 60)
print("6. MELT() — Wide to Long Transformation")
print("=" * 60)

# melt() is the inverse of pivot_table().
# It converts "wide" format (one column per metric) to
# "long" format (one row per metric). This is often required for databases.

# Create a wide-format summary to demonstrate
wide_df = pd.DataFrame({
    "product": ["Laptop", "Mouse", "Monitor"],
    "Q1_sales": [15000, 450, 8000],
    "Q2_sales": [18000, 600, 9500],
    "Q3_sales": [12000, 500, 7000],
    "Q4_sales": [20000, 750, 11000],
})
print("Wide format (one column per quarter):")
print(wide_df)

# melt into long format
long_df = wide_df.melt(
    id_vars=["product"],        # columns to keep as identifiers
    value_vars=["Q1_sales", "Q2_sales", "Q3_sales", "Q4_sales"],  # cols to unpivot
    var_name="quarter",         # name for the new variable column
    value_name="sales_amount"   # name for the new value column
)
print(f"\nLong format after melt ({len(long_df)} rows):")
print(long_df)

# Clean up the quarter names
long_df["quarter"] = long_df["quarter"].str.replace("_sales", "")
print(f"\nCleaned quarter column: {long_df['quarter'].unique()}")


# =============================================================================
# 7. STACK AND UNSTACK
# =============================================================================

print("\n" + "=" * 60)
print("7. STACK AND UNSTACK")
print("=" * 60)

# stack() — move column labels to row index (columns → rows)
# unstack() — move row index to column labels (rows → columns)
# These are particularly useful with MultiIndex DataFrames.

# Create a small MultiIndex example
data = {
    ("Electronics", "Q1"): 15000,
    ("Electronics", "Q2"): 18000,
    ("Furniture",   "Q1"): 8000,
    ("Furniture",   "Q2"): 9500,
}
mi_series = pd.Series(data)
print("MultiIndex Series:")
print(mi_series)

# unstack() — move the last level of the index to columns
unstacked = mi_series.unstack()
print(f"\nUnstacked (quarter as columns):")
print(unstacked)

# stack() — reverse of unstack
restacked = unstacked.stack()
print(f"\nRestacked (back to long format):")
print(restacked)


# =============================================================================
# MAIN DEMO
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("PRACTICAL DEMO: Full Transformation Pipeline")
    print("=" * 60)

    df = load_clean_sales()

    # Step 1: Compute financial columns
    df["total_amount"] = (df["quantity"] * df["unit_price"]).round(2)
    df["tier"] = np.select(
        [df["total_amount"] >= 1000, df["total_amount"] >= 500, df["total_amount"] >= 200],
        ["Platinum", "Gold", "Silver"],
        default="Bronze"
    )

    # Step 2: Extract time features
    df["year_month"] = df["date"].dt.to_period("M").astype(str)

    # Step 3: Create a pivot report
    print("\nMonthly revenue by category:")
    monthly_pivot = df.pivot_table(
        values="total_amount",
        index="year_month",
        columns="category",
        aggfunc="sum",
        fill_value=0
    )
    print(monthly_pivot.round(2))

    # Step 4: Melt to long format for loading
    long_report = monthly_pivot.reset_index().melt(
        id_vars="year_month",
        var_name="category",
        value_name="revenue"
    )
    print(f"\nLong format report ({len(long_report)} rows):")
    print(long_report.to_string())
