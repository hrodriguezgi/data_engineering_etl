"""
Module 2 - Lesson 1: Introduction to Pandas
=============================================
Pandas is the most important library for data engineering in Python.
It provides two key data structures:
  - Series: a 1-dimensional labeled array (like a single column)
  - DataFrame: a 2-dimensional labeled table (like a spreadsheet)

Think of a DataFrame as an in-memory database table with powerful
built-in operations for filtering, transforming, and aggregating data.

Topics covered:
  - Creating Series and DataFrames
  - Reading CSV and JSON files
  - Basic inspection: info(), describe(), head(), tail(), shape, dtypes
  - Selecting columns and rows
  - Basic filtering
  - Summary statistics
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Reference to the data directory
DATA_DIR = Path(__file__).parent / "data"


# =============================================================================
# 1. PANDAS SERIES
# =============================================================================

print("=" * 60)
print("1. PANDAS SERIES")
print("=" * 60)

# A Series is a 1D labeled array. Each element has an index label.
# Think of it as a single column in a spreadsheet.

# Create from a list (auto-index: 0, 1, 2, ...)
prices = pd.Series([999.99, 29.99, 79.99, 349.99, 449.99])
print("Prices series:")
print(prices)
print(f"dtype: {prices.dtype}")  # float64

# Create with a custom index
products = pd.Series(
    [999.99, 29.99, 79.99, 349.99],
    index=["laptop", "mouse", "keyboard", "monitor"],
    name="price_usd"   # give the series a name
)
print("\nProducts series with custom index:")
print(products)

# Accessing elements
print(f"\nAccess by label: products['laptop'] = {products['laptop']}")
print(f"Access by position: products.iloc[0] = {products.iloc[0]}")

# Series operations are vectorized (apply to all elements at once)
with_tax = products * 1.08
print("\nPrices with 8% tax:")
print(with_tax.round(2))

# Boolean indexing on a Series
expensive = products[products > 100]
print("\nProducts > $100:")
print(expensive)

# Series statistics
print(f"\nMean:   ${products.mean():.2f}")
print(f"Median: ${products.median():.2f}")
print(f"Max:    ${products.max():.2f}")
print(f"Min:    ${products.min():.2f}")


# =============================================================================
# 2. CREATING DATAFRAMES
# =============================================================================

print("\n" + "=" * 60)
print("2. CREATING DATAFRAMES")
print("=" * 60)

# Method 1: From a list of dicts — most common in data engineering
records = [
    {"order_id": 1001, "customer": "Alice", "product": "Laptop",  "quantity": 1, "price": 999.99},
    {"order_id": 1002, "customer": "Bob",   "product": "Mouse",   "quantity": 3, "price": 29.99},
    {"order_id": 1003, "customer": "Carol", "product": "Monitor", "quantity": 2, "price": 349.99},
    {"order_id": 1004, "customer": "Dave",  "product": "Laptop",  "quantity": 1, "price": 999.99},
]
df_from_dicts = pd.DataFrame(records)
print("DataFrame from list of dicts:")
print(df_from_dicts)

# Method 2: From a dict of lists (column-oriented)
df_from_dict_of_lists = pd.DataFrame({
    "name": ["Alice", "Bob", "Carol"],
    "age":  [32, 28, 45],
    "city": ["New York", "LA", "Chicago"],
})
print("\nDataFrame from dict of lists:")
print(df_from_dict_of_lists)

# Method 3: From a 2D numpy array with column names
data_array = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
df_from_array = pd.DataFrame(data_array, columns=["A", "B", "C"])
print("\nDataFrame from numpy array:")
print(df_from_array)

# Method 4: Empty DataFrame with defined schema
df_empty = pd.DataFrame(columns=["order_id", "customer", "amount", "date"])
print(f"\nEmpty DataFrame schema: {list(df_empty.columns)}")


# =============================================================================
# 3. READING FILES WITH PANDAS
# =============================================================================

print("\n" + "=" * 60)
print("3. READING FILES")
print("=" * 60)

# Read CSV — the most common operation in data engineering
sales_csv = DATA_DIR / "sales.csv"
df_sales = pd.read_csv(sales_csv)
print(f"Sales DataFrame shape: {df_sales.shape}")  # (rows, columns)
print(f"Columns: {list(df_sales.columns)}")

# Read with type hints — helps pandas parse columns correctly
df_sales_typed = pd.read_csv(
    sales_csv,
    dtype={
        "order_id": "Int64",     # nullable integer (capital I)
        "quantity": "Int64",
        "unit_price": "float64",
    },
    parse_dates=["date"],   # automatically parse date columns
)
print(f"\nTyped dtypes:\n{df_sales_typed.dtypes}")

# Read JSON
# Create a simple JSON to read
import json, tempfile
json_data = [
    {"id": 1, "name": "Alice", "score": 95.5},
    {"id": 2, "name": "Bob",   "score": 87.0},
    {"id": 3, "name": "Carol", "score": 92.3},
]
json_str = json.dumps(json_data)
df_json = pd.read_json(json_str)
print(f"\nDataFrame from JSON:\n{df_json}")


# =============================================================================
# 4. BASIC INSPECTION METHODS
# =============================================================================

print("\n" + "=" * 60)
print("4. BASIC INSPECTION")
print("=" * 60)

df = df_sales.copy()

# .head(n) and .tail(n) — first/last n rows (default n=5)
print("First 5 rows (head):")
print(df.head())

print("\nLast 3 rows (tail):")
print(df.tail(3))

# .info() — column names, non-null counts, dtypes, memory usage
print("\nDataFrame info:")
df.info()

# .describe() — summary statistics for numeric columns
print("\nDescriptive statistics:")
print(df.describe())

# .describe() for object (string) columns
print("\nObject column statistics:")
print(df.describe(include="object"))

# Shape, size, ndim
print(f"\nShape (rows, cols): {df.shape}")
print(f"Total cells: {df.size}")
print(f"Dimensions: {df.ndim}")
print(f"Row count: {len(df)}")

# Column names and index
print(f"\nColumns: {list(df.columns)}")
print(f"Index: {df.index}")

# Data types
print(f"\nData types:\n{df.dtypes}")

# Value counts — frequency of each unique value
print(f"\nCategory value counts:\n{df['category'].value_counts()}")
print(f"\nRegion value counts:\n{df['region'].value_counts()}")

# Unique values
print(f"\nUnique categories: {df['category'].unique()}")
print(f"Number of unique customers: {df['customer_name'].nunique()}")

# Null counts per column
print(f"\nNull counts:\n{df.isnull().sum()}")


# =============================================================================
# 5. SELECTING COLUMNS AND ROWS
# =============================================================================

print("\n" + "=" * 60)
print("5. SELECTING COLUMNS AND ROWS")
print("=" * 60)

# Selecting a single column — returns a Series
product_col = df["product"]
print(f"Product column type: {type(product_col).__name__}")
print(product_col.head())

# Selecting multiple columns — returns a DataFrame
subset_df = df[["order_id", "customer_name", "unit_price"]]
print(f"\nSubset DataFrame:\n{subset_df.head()}")

# .loc[rows, cols] — label-based selection
print(f"\nRow at index 2: \n{df.loc[2]}")
print(f"\nRows 0-3, specific columns:\n{df.loc[0:3, ['customer_name', 'product', 'unit_price']]}")

# .iloc[rows, cols] — integer position-based selection
print(f"\nFirst 3 rows, first 3 columns (iloc):\n{df.iloc[:3, :3]}")
print(f"\nLast row: \n{df.iloc[-1]}")

# Boolean indexing — filter rows by condition
electronics = df[df["category"] == "Electronics"]
print(f"\nElectronics orders: {len(electronics)} rows")

# Multiple conditions — use & (and) and | (or), with parentheses
high_value_electronics = df[
    (df["category"] == "Electronics") &
    (df["unit_price"] > 100)
]
print(f"High-value electronics: {len(high_value_electronics)} rows")
print(high_value_electronics[["order_id", "product", "unit_price"]].to_string())

# .query() method — SQL-like filtering
north_sales = df.query("region == 'North' and unit_price > 50")
print(f"\nNorth region, price > 50: {len(north_sales)} rows")

# isin() — check if value is in a set
target_regions = ["North", "East"]
filtered = df[df["region"].isin(target_regions)]
print(f"\nNorth or East region: {len(filtered)} rows")


# =============================================================================
# 6. BASIC CALCULATIONS
# =============================================================================

print("\n" + "=" * 60)
print("6. BASIC CALCULATIONS")
print("=" * 60)

# Add a calculated column
# Note: quantity and unit_price may have nulls — pandas handles them as NaN
df["total_price"] = df["quantity"] * df["unit_price"]
print("Total price column added:")
print(df[["order_id", "quantity", "unit_price", "total_price"]].head(8))

# Aggregations over a column
print(f"\nTotal revenue (ignoring nulls): ${df['total_price'].sum():.2f}")
print(f"Average order value: ${df['total_price'].mean():.2f}")
print(f"Largest order: ${df['total_price'].max():.2f}")
print(f"Smallest order: ${df['total_price'].min():.2f}")


# =============================================================================
# MAIN DEMO
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("PRACTICAL DEMO: Loading and Profiling the Sales Dataset")
    print("=" * 60)

    df = pd.read_csv(DATA_DIR / "sales.csv")

    print(f"\n📊 Dataset Profile")
    print(f"   Rows:     {len(df)}")
    print(f"   Columns:  {df.shape[1]}")
    print(f"   Null values:\n{df.isnull().sum().to_string()}")
    print(f"\n   Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"\n   Categories: {df['category'].unique()}")
    print(f"   Regions:    {sorted(df['region'].dropna().unique())}")
    print(f"   Customers:  {df['customer_name'].nunique()} unique")

    df["total_price"] = df["quantity"] * df["unit_price"]
    print(f"\n   Total revenue: ${df['total_price'].sum():.2f}")
    print(f"   Top product:   {df.groupby('product')['total_price'].sum().idxmax()}")
