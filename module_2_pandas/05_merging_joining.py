"""
Module 2 - Lesson 5: Merging and Joining DataFrames
=====================================================
Real-world data is almost never in a single table. You'll need to combine
data from multiple sources — just like SQL JOINs.

Pandas provides several ways to combine DataFrames:
  - merge()  — database-style joins (inner, left, right, outer)
  - join()   — index-based joining
  - concat() — stacking DataFrames vertically or horizontally

Topics covered:
  - Inner join — only rows with matching keys in BOTH tables
  - Left join  — all rows from left, matched from right (NaN if no match)
  - Right join — all rows from right, matched from left (NaN if no match)
  - Outer join — all rows from both tables
  - Joining on multiple keys
  - Handling overlapping column names (suffixes)
  - concat() along axis 0 (rows) and axis 1 (columns)
  - The indicator column for debugging joins
"""

import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


# =============================================================================
# LOAD SAMPLE DATA
# =============================================================================

def load_sales() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "sales.csv")
    df = df.drop_duplicates(subset=["order_id"], keep="first").copy()
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(1).astype(int)
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    df["unit_price"] = df["unit_price"].fillna(df["unit_price"].median())
    df["region"] = df["region"].fillna("Unknown")
    df["customer_name"] = df["customer_name"].fillna("Anonymous").str.strip()
    df["date"] = pd.to_datetime(df["date"])
    df["total_amount"] = (df["quantity"] * df["unit_price"]).round(2)
    return df

def load_customers() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "customers.csv")

orders = load_sales()
customers = load_customers()

print(f"Orders: {orders.shape}")
print(orders[["order_id", "customer_name", "total_amount"]].head(5))

print(f"\nCustomers: {customers.shape}")
print(customers.head(5))


# =============================================================================
# 1. INNER JOIN
# =============================================================================

print("\n" + "=" * 60)
print("1. INNER JOIN — rows matching in BOTH tables")
print("=" * 60)

# INNER JOIN: keeps only rows where the key exists in BOTH DataFrames.
# If a customer in orders is not in customers table, the order is dropped.
# If a customer in customers has no orders, they are dropped.

# Join orders to customer details by customer name
# Note: the key columns have different names in each table
inner_join = pd.merge(
    orders,                         # left DataFrame
    customers,                      # right DataFrame
    left_on="customer_name",        # key in left DataFrame
    right_on="name",                # key in right DataFrame
    how="inner"                     # join type
)

print(f"Orders: {len(orders)} rows")
print(f"Customers: {len(customers)} rows")
print(f"Inner join result: {len(inner_join)} rows")
print(f"(Rows dropped because customer not in customers table: {len(orders) - len(inner_join)})")
print(f"\nInner join columns: {list(inner_join.columns)}")
print(inner_join[["order_id", "customer_name", "email", "city", "total_amount"]].head(8))


# =============================================================================
# 2. LEFT JOIN
# =============================================================================

print("\n" + "=" * 60)
print("2. LEFT JOIN — all rows from LEFT, matched from RIGHT")
print("=" * 60)

# LEFT JOIN: keeps all rows from the LEFT DataFrame.
# For rows without a match in the right, fills with NaN.
# Most common join in ETL: "keep all orders, add customer info where available"

left_join = pd.merge(
    orders,
    customers,
    left_on="customer_name",
    right_on="name",
    how="left"
)

print(f"Left join result: {len(left_join)} rows (same as left table)")
print(f"Orders without customer info: {left_join['email'].isnull().sum()}")

# Show orders where customer info is missing
no_customer_info = left_join[left_join["email"].isnull()]
print(f"\nOrders missing customer data:")
print(no_customer_info[["order_id", "customer_name", "email"]].to_string())

print(f"\nWith customer info:")
print(left_join[["order_id", "customer_name", "city", "country", "age"]].head(8))


# =============================================================================
# 3. RIGHT JOIN
# =============================================================================

print("\n" + "=" * 60)
print("3. RIGHT JOIN — all rows from RIGHT, matched from LEFT")
print("=" * 60)

# RIGHT JOIN: keeps all rows from the RIGHT DataFrame.
# Rarely used directly — equivalent to swapping tables and doing a LEFT JOIN.
# Useful to find "which customers have never placed an order?"

right_join = pd.merge(
    orders,
    customers,
    left_on="customer_name",
    right_on="name",
    how="right"
)

print(f"Right join result: {len(right_join)} rows")
print(f"Customers with no orders: {right_join['order_id'].isnull().sum()}")

no_orders = right_join[right_join["order_id"].isnull()]
print(f"\nCustomers with no orders:")
print(no_orders[["name", "email", "city"]].to_string())


# =============================================================================
# 4. OUTER (FULL) JOIN
# =============================================================================

print("\n" + "=" * 60)
print("4. OUTER JOIN — all rows from BOTH tables")
print("=" * 60)

# OUTER JOIN: keeps ALL rows from both tables.
# NaN is filled where there is no match.
# Useful for reconciliation: "what's in table A but not B, and vice versa?"

outer_join = pd.merge(
    orders,
    customers,
    left_on="customer_name",
    right_on="name",
    how="outer",
    indicator=True   # adds a '_merge' column showing where each row came from
)

print(f"Outer join result: {len(outer_join)} rows")
print(f"\nMerge indicator (where did each row come from?):")
print(outer_join["_merge"].value_counts())

# Rows only in left (orders with no matching customer)
only_in_orders = outer_join[outer_join["_merge"] == "left_only"]
print(f"\nOnly in orders (no matching customer): {len(only_in_orders)}")

# Rows only in right (customers with no orders)
only_in_customers = outer_join[outer_join["_merge"] == "right_only"]
print(f"Only in customers (no orders): {len(only_in_customers)}")
print(only_in_customers[["name", "email", "city"]].to_string())


# =============================================================================
# 5. JOINING ON MULTIPLE KEYS
# =============================================================================

print("\n" + "=" * 60)
print("5. JOINING ON MULTIPLE KEYS")
print("=" * 60)

# When a single column isn't enough to uniquely identify a match,
# join on multiple columns (composite key).

# Example: create a region-category revenue table and join to a budget table
actual_revenue = pd.DataFrame({
    "region": ["North", "North", "South", "East", "West"],
    "category": ["Electronics", "Furniture", "Electronics", "Electronics", "Furniture"],
    "actual_revenue": [3599.97, 349.99, 2029.93, 3149.96, 699.98],
})

budget_targets = pd.DataFrame({
    "region": ["North", "North", "South", "East", "West", "West"],
    "category": ["Electronics", "Furniture", "Electronics", "Electronics", "Electronics", "Furniture"],
    "budget_target": [4000, 500, 2500, 3000, 1500, 800],
})

combined = pd.merge(
    actual_revenue,
    budget_targets,
    on=["region", "category"],   # join on two columns simultaneously
    how="outer"
)
combined["vs_budget"] = (combined["actual_revenue"] - combined["budget_target"]).round(2)
combined["pct_achieved"] = (combined["actual_revenue"] / combined["budget_target"] * 100).round(1)

print("Revenue vs Budget (multi-key join):")
print(combined.to_string())


# =============================================================================
# 6. HANDLING OVERLAPPING COLUMN NAMES (SUFFIXES)
# =============================================================================

print("\n" + "=" * 60)
print("6. OVERLAPPING COLUMN NAMES — Suffixes")
print("=" * 60)

# When both tables have columns with the same name (other than the join key),
# pandas appends suffixes to distinguish them.

# Create two tables both having a "date" column
current_prices = pd.DataFrame({
    "product": ["Laptop", "Mouse", "Monitor"],
    "price": [999.99, 29.99, 449.99],
    "updated_date": ["2024-01-01", "2024-01-01", "2024-01-01"],
})

historical_prices = pd.DataFrame({
    "product": ["Laptop", "Mouse", "Keyboard"],
    "price": [1099.99, 34.99, 89.99],
    "updated_date": ["2023-01-01", "2023-01-01", "2023-01-01"],
})

price_comparison = pd.merge(
    current_prices,
    historical_prices,
    on="product",
    how="inner",
    suffixes=("_current", "_historical")  # customize the suffixes
)
price_comparison["price_change"] = (
    price_comparison["price_current"] - price_comparison["price_historical"]
).round(2)

print("Price comparison (with suffixes):")
print(price_comparison)


# =============================================================================
# 7. CONCAT() — STACKING DATAFRAMES
# =============================================================================

print("\n" + "=" * 60)
print("7. CONCAT() — Stacking DataFrames")
print("=" * 60)

# concat() combines DataFrames by stacking them:
#   axis=0: stack VERTICALLY (add rows — like UNION ALL in SQL)
#   axis=1: stack HORIZONTALLY (add columns — like a side-by-side join)

# --- Vertical concat (axis=0) — combine records from multiple sources ---
jan_orders = pd.DataFrame({
    "order_id": [1001, 1002, 1003],
    "month": ["Jan", "Jan", "Jan"],
    "amount": [250.0, 175.5, 390.0],
})
feb_orders = pd.DataFrame({
    "order_id": [1004, 1005],
    "month": ["Feb", "Feb"],
    "amount": [520.0, 88.0],
})
mar_orders = pd.DataFrame({
    "order_id": [1006, 1007, 1008],
    "month": ["Mar", "Mar", "Mar"],
    "amount": [310.0, 145.0, 760.0],
})

# Stack all three months together
all_orders = pd.concat(
    [jan_orders, feb_orders, mar_orders],
    axis=0,
    ignore_index=True   # reset the index to 0, 1, 2, ...
)
print("Vertical concat (all monthly orders):")
print(all_orders)

# With keys — adds a level to the index to track source
all_with_keys = pd.concat(
    [jan_orders, feb_orders, mar_orders],
    keys=["January", "February", "March"],
    axis=0
)
print(f"\nConcat with keys (MultiIndex):")
print(all_with_keys)

# --- Horizontal concat (axis=1) — add columns side by side ---
metrics_a = pd.DataFrame({"product": ["Laptop", "Mouse", "Monitor"], "revenue": [5000, 300, 2000]})
metrics_b = pd.DataFrame({"units_sold": [5, 10, 4], "returns": [1, 0, 0]})

combined_metrics = pd.concat([metrics_a, metrics_b], axis=1)
print(f"\nHorizontal concat (side by side):")
print(combined_metrics)


# =============================================================================
# MAIN DEMO
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("PRACTICAL DEMO: Building a Customer Order Report")
    print("=" * 60)

    orders = load_sales()
    customers = load_customers()

    # Join orders to customers (left join — keep all orders)
    enriched = pd.merge(
        orders,
        customers,
        left_on="customer_name",
        right_on="name",
        how="left",
        suffixes=("", "_customer")
    )

    # Build customer-level summary
    customer_report = enriched.groupby("customer_name").agg(
        total_orders=("order_id", "count"),
        total_spent=("total_amount", "sum"),
        avg_order=("total_amount", "mean"),
        country=("country", "first"),
        age=("age", "first"),
    ).reset_index().sort_values("total_spent", ascending=False)

    customer_report["total_spent"] = customer_report["total_spent"].round(2)
    customer_report["avg_order"] = customer_report["avg_order"].round(2)

    print("\nCustomer Order Report:")
    print(customer_report.to_string())

    print(f"\nTotal customers who placed orders: {len(customer_report)}")
    print(f"Total customers with no orders: "
          f"{len(customers) - customer_report['customer_name'].isin(customers['name']).sum()}")
