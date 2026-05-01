"""
Module 2 - Lesson 4: Aggregations with Pandas
===============================================
Aggregations summarize large datasets into meaningful metrics.
In data engineering, aggregations are used to:
  - Build summary reports
  - Create data mart tables (fact tables, aggregated dimensions)
  - Compute KPIs
  - Detect anomalies (e.g., using rolling averages)

Topics covered:
  - groupby() — split-apply-combine pattern
  - agg() — multiple aggregations at once
  - Named aggregations (clean, explicit syntax)
  - transform() — group stats without collapsing rows
  - Rolling windows (rolling mean, sum, etc.)
  - Expanding windows (cumulative operations)
  - cumsum(), cumprod(), cummax(), cummin()
"""

import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

def load_clean_sales() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "sales.csv")
    df = df.drop_duplicates(subset=["order_id"], keep="first").copy()
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(1).astype(int)
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    df["unit_price"] = df["unit_price"].fillna(df["unit_price"].median())
    df["region"] = df["region"].fillna("Unknown")
    df["customer_name"] = df["customer_name"].fillna("Anonymous")
    df["date"] = pd.to_datetime(df["date"])
    df["total_amount"] = (df["quantity"] * df["unit_price"]).round(2)
    return df

df = load_clean_sales()
print(f"Loaded {len(df)} rows")


# =============================================================================
# 1. BASIC GROUPBY
# =============================================================================

print("=" * 60)
print("1. BASIC GROUPBY")
print("=" * 60)

# groupby() implements the "split-apply-combine" pattern:
#   1. SPLIT data into groups based on a key
#   2. APPLY an aggregation function to each group
#   3. COMBINE results into a new DataFrame

# Total revenue per category
revenue_by_category = df.groupby("category")["total_amount"].sum()
print("Total revenue by category:")
print(revenue_by_category.round(2))

# Average unit price per category
avg_price = df.groupby("category")["unit_price"].mean()
print(f"\nAverage unit price by category:")
print(avg_price.round(2))

# Order count per region
orders_per_region = df.groupby("region")["order_id"].count()
print(f"\nOrder count per region:")
print(orders_per_region)

# Groupby multiple columns
revenue_by_cat_region = df.groupby(["category", "region"])["total_amount"].sum()
print(f"\nRevenue by category + region (MultiIndex):")
print(revenue_by_cat_region.round(2))

# Reset index to get a flat DataFrame
revenue_flat = revenue_by_cat_region.reset_index()
print(f"\nFlat DataFrame:\n{revenue_flat}")


# =============================================================================
# 2. AGG() — MULTIPLE AGGREGATIONS
# =============================================================================

print("\n" + "=" * 60)
print("2. AGG() — Multiple Aggregations")
print("=" * 60)

# agg() lets you apply multiple functions at once to one or more columns.
# Returns a DataFrame with the functions as column headers.

# Multiple functions on a single column
category_stats = df.groupby("category")["total_amount"].agg(["sum", "mean", "min", "max", "count"])
print("Amount stats by category:")
print(category_stats.round(2))

# Different functions for different columns
multi_col_agg = df.groupby("category").agg(
    total_revenue=("total_amount", "sum"),
    avg_price=("unit_price", "mean"),
    total_quantity=("quantity", "sum"),
    order_count=("order_id", "count"),
)
print(f"\nMulti-column aggregation (named):")
print(multi_col_agg.round(2))

# Custom aggregation function
def revenue_range(series):
    """Return the range (max - min) of a series."""
    return series.max() - series.min()

custom_agg = df.groupby("region")["total_amount"].agg(
    total="sum",
    average="mean",
    revenue_range=revenue_range,   # custom function
)
print(f"\nRevenue range by region:")
print(custom_agg.round(2))


# =============================================================================
# 3. NAMED AGGREGATIONS (Modern Syntax)
# =============================================================================

print("\n" + "=" * 60)
print("3. NAMED AGGREGATIONS")
print("=" * 60)

# The clearest syntax for multiple aggregations (pandas >= 0.25)
# Syntax: new_col_name=(source_column, aggregation_function)

customer_summary = df.groupby("customer_name").agg(
    total_orders=("order_id", "count"),
    total_spent=("total_amount", "sum"),
    avg_order_value=("total_amount", "mean"),
    first_order=("date", "min"),
    last_order=("date", "max"),
    favorite_category=("category", lambda x: x.mode()[0]),  # most common category
).reset_index()

# Sort by total spent
customer_summary = customer_summary.sort_values("total_spent", ascending=False)
customer_summary[["total_spent", "avg_order_value"]] = \
    customer_summary[["total_spent", "avg_order_value"]].round(2)

print("Customer summary:")
print(customer_summary.to_string())


# =============================================================================
# 4. TRANSFORM() — GROUP STATS WITHOUT COLLAPSING
# =============================================================================

print("\n" + "=" * 60)
print("4. TRANSFORM() — Group Stats on Original DataFrame")
print("=" * 60)

# transform() applies a function to each group and returns a result
# with the SAME INDEX as the original DataFrame.
# This is perfect for adding group-level statistics as new columns,
# e.g., "how does this row compare to its group average?"

# Add group mean as a column (without collapsing rows)
df["category_avg_price"] = df.groupby("category")["unit_price"].transform("mean")
df["price_vs_category_avg"] = (df["unit_price"] - df["category_avg_price"]).round(2)

print("Unit price vs category average:")
print(df[["product", "category", "unit_price", "category_avg_price", "price_vs_category_avg"]].head(10))

# Add regional revenue share
df["region_total"] = df.groupby("region")["total_amount"].transform("sum")
df["pct_of_region"] = (df["total_amount"] / df["region_total"] * 100).round(1)

print(f"\nRegional revenue share:")
print(df[["order_id", "region", "total_amount", "region_total", "pct_of_region"]].head(8))


# =============================================================================
# 5. ROLLING WINDOWS
# =============================================================================

print("\n" + "=" * 60)
print("5. ROLLING WINDOWS")
print("=" * 60)

# Rolling windows compute statistics over a sliding window of rows.
# Common in time-series analysis: moving averages, rolling sums.

# Create a daily time series by resampling
daily_revenue = df.set_index("date")["total_amount"].resample("D").sum().fillna(0)
print(f"Daily revenue series ({len(daily_revenue)} days):")
print(daily_revenue.round(2))

# 3-day rolling mean (smooths out day-to-day noise)
daily_revenue_df = pd.DataFrame({"revenue": daily_revenue})
daily_revenue_df["rolling_3d_mean"] = daily_revenue_df["revenue"].rolling(window=3).mean()
daily_revenue_df["rolling_3d_sum"] = daily_revenue_df["revenue"].rolling(window=3).sum()

# min_periods=1 means: compute even if window is not full (for first rows)
daily_revenue_df["rolling_mean_partial"] = (
    daily_revenue_df["revenue"].rolling(window=3, min_periods=1).mean()
)

print(f"\nRolling window calculations:")
print(daily_revenue_df.round(2))


# =============================================================================
# 6. EXPANDING WINDOWS (CUMULATIVE OPERATIONS)
# =============================================================================

print("\n" + "=" * 60)
print("6. CUMULATIVE OPERATIONS")
print("=" * 60)

# Cumulative functions accumulate values from the beginning of the series.
# expanding() gives you the cumulative equivalent of rolling().

df_sorted = df.sort_values("date").copy()

# cumsum — running total of revenue
df_sorted["cumulative_revenue"] = df_sorted["total_amount"].cumsum()

# cumcount within groups — rank of order per customer
df_sorted["customer_order_number"] = (
    df_sorted.groupby("customer_name").cumcount() + 1  # 1-based
)

# expanding mean — average up to current row (stabilizes over time)
df_sorted["running_avg_order_value"] = (
    df_sorted["total_amount"].expanding().mean().round(2)
)

print("Cumulative statistics over time:")
print(df_sorted[["date", "customer_name", "total_amount",
                   "cumulative_revenue", "customer_order_number",
                   "running_avg_order_value"]].head(12).to_string())

# cummax and cummin
df_sorted["max_so_far"] = df_sorted["total_amount"].cummax()
print(f"\nRunning maximum order value:")
print(df_sorted[["date", "total_amount", "max_so_far"]].head(8))


# =============================================================================
# MAIN DEMO
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("PRACTICAL DEMO: Sales Analytics Dashboard")
    print("=" * 60)

    df = load_clean_sales()
    df["total_amount"] = (df["quantity"] * df["unit_price"]).round(2)

    # KPI 1: Overall metrics
    print("\n📊 Overall KPIs")
    print(f"   Total Revenue:      ${df['total_amount'].sum():>10,.2f}")
    print(f"   Total Orders:       {len(df):>10,}")
    print(f"   Avg Order Value:    ${df['total_amount'].mean():>10,.2f}")
    print(f"   Unique Customers:   {df['customer_name'].nunique():>10,}")

    # KPI 2: By category
    print("\n📦 Revenue by Category")
    cat_rev = df.groupby("category")["total_amount"].agg(
        revenue="sum", orders="count", avg="mean"
    ).sort_values("revenue", ascending=False)
    for cat, row in cat_rev.iterrows():
        print(f"   {cat:15s} Revenue=${row['revenue']:>8,.2f}  "
              f"Orders={row['orders']:>3}  Avg=${row['avg']:>7,.2f}")

    # KPI 3: Top customers
    print("\n👥 Top 5 Customers by Spend")
    top_customers = (
        df.groupby("customer_name")["total_amount"]
        .sum()
        .nlargest(5)
        .reset_index()
    )
    for _, row in top_customers.iterrows():
        print(f"   {row['customer_name']:20s} ${row['total_amount']:>8,.2f}")

    # KPI 4: Monthly trend
    print("\n📅 Monthly Revenue Trend")
    df["year_month"] = df["date"].dt.to_period("M")
    monthly = df.groupby("year_month")["total_amount"].sum()
    for period, revenue in monthly.items():
        bar = "█" * int(revenue / 200)
        print(f"   {str(period):8s} ${revenue:>7,.2f} {bar}")
