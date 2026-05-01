"""
Module 2 - Lesson 2: Data Cleaning with Pandas
===============================================
Real-world data is messy. Before analysis or loading into a database,
data must be cleaned. This is often 70-80% of a data engineer's work.

Common data quality issues:
  - Missing values (NaN/None)
  - Duplicate rows
  - Wrong data types (e.g., numbers stored as strings)
  - Inconsistent formatting (e.g., "New York", "new york", "NY")
  - Leading/trailing whitespace
  - Outliers and impossible values

Topics covered:
  - Detecting and handling missing values (isnull, fillna, dropna)
  - Finding and removing duplicates
  - Type conversion (astype, pd.to_numeric, pd.to_datetime)
  - String operations using the .str accessor
  - Renaming and reorganizing columns
  - Replacing values
"""

import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


# =============================================================================
# 1. LOADING THE DATASET
# =============================================================================

print("=" * 60)
print("1. LOADING THE DATASET")
print("=" * 60)

df = pd.read_csv(DATA_DIR / "sales.csv")
print(f"Loaded {len(df)} rows, {df.shape[1]} columns")
print(f"\nRaw data (first 10 rows):")
print(df.head(10).to_string())
print(f"\nNull counts:\n{df.isnull().sum()}")
print(f"\nDtypes:\n{df.dtypes}")


# =============================================================================
# 2. HANDLING MISSING VALUES
# =============================================================================

print("\n" + "=" * 60)
print("2. MISSING VALUES")
print("=" * 60)

df_work = df.copy()   # always work on a copy to preserve the original

# --- Detecting nulls ---
# isnull() returns a boolean DataFrame
# any(axis=1) tells us which rows have at least one null
has_null = df_work.isnull().any(axis=1)
print(f"Rows with at least one null: {has_null.sum()}")
print("\nRows containing nulls:")
print(df_work[has_null].to_string())

# --- fillna() — fill missing values ---
# Fill numeric columns with a default value
df_work["quantity"] = df_work["quantity"].fillna(0).astype("Int64")

# Fill price with the median (robust to outliers)
median_price = df_work["unit_price"].median()
print(f"\nMedian unit_price: ${median_price:.2f}")
df_work["unit_price"] = df_work["unit_price"].fillna(median_price)

# Fill string columns with a placeholder
df_work["region"] = df_work["region"].fillna("Unknown")
df_work["customer_name"] = df_work["customer_name"].fillna("Anonymous")

print(f"\nNull counts after fillna:\n{df_work.isnull().sum()}")

# --- dropna() — remove rows/columns with nulls ---
# drop rows where specific columns are still null
df_no_nulls = df_work.dropna(subset=["unit_price"])
print(f"\nRows after dropna(subset=['unit_price']): {len(df_no_nulls)}")

# Drop columns that are entirely null
df_drop_cols = df_work.dropna(axis=1, how="all")  # 'all' = only if ALL values null
print(f"Columns after dropna(axis=1, how='all'): {list(df_drop_cols.columns)}")

# --- where() and mask() — conditional replacement ---
# Replace outlier quantities (> 100) with NaN, then fill
df_work["quantity"] = df_work["quantity"].where(df_work["quantity"] <= 10, other=np.nan)
df_work["quantity"] = df_work["quantity"].fillna(1)


# =============================================================================
# 3. HANDLING DUPLICATES
# =============================================================================

print("\n" + "=" * 60)
print("3. DUPLICATES")
print("=" * 60)

# duplicated() returns a boolean Series
# keep='first' marks all duplicates EXCEPT the first occurrence as True
dupe_mask = df_work.duplicated()
print(f"Total duplicate rows: {dupe_mask.sum()}")

# Show the duplicated rows
print("\nDuplicate rows:")
print(df_work[dupe_mask].to_string())

# duplicated on specific columns
order_dupes = df_work.duplicated(subset=["order_id"], keep="first")
print(f"\nDuplicate order_ids: {order_dupes.sum()}")

# drop_duplicates() — remove duplicate rows
df_deduped = df_work.drop_duplicates(subset=["order_id"], keep="first")
print(f"Rows before dedup: {len(df_work)}")
print(f"Rows after dedup:  {len(df_deduped)}")

# Reset the index after dropping rows
df_work = df_deduped.reset_index(drop=True)  # drop=True discards the old index
print(f"\nIndex after reset: {df_work.index.tolist()[:5]}...")


# =============================================================================
# 4. TYPE CONVERSION
# =============================================================================

print("\n" + "=" * 60)
print("4. TYPE CONVERSION")
print("=" * 60)

print(f"dtypes before conversion:\n{df_work.dtypes}")

# Convert date column from string to datetime
df_work["date"] = pd.to_datetime(df_work["date"])
print(f"\nDate column dtype after pd.to_datetime: {df_work['date'].dtype}")
print(f"Sample dates: {df_work['date'].head(3).tolist()}")

# Extract date parts — very useful for time-based analysis
df_work["year"] = df_work["date"].dt.year
df_work["month"] = df_work["date"].dt.month
df_work["day_of_week"] = df_work["date"].dt.day_name()
print(f"\nDate components:\n{df_work[['date', 'year', 'month', 'day_of_week']].head(5)}")

# Convert numeric columns
# pd.to_numeric() is safer than astype() — handles errors gracefully
df_work["unit_price"] = pd.to_numeric(df_work["unit_price"], errors="coerce")
# errors="coerce" converts invalid values to NaN instead of raising
# errors="raise" (default) raises on bad values
# errors="ignore" leaves bad values as-is

# astype() for straightforward conversions
df_work["order_id"] = df_work["order_id"].astype(int)

# Convert category column to pandas Categorical — saves memory with many repeated values
df_work["category"] = df_work["category"].astype("category")
df_work["region"] = df_work["region"].astype("category")
print(f"\nMemory after categorical conversion:")
print(df_work.memory_usage(deep=True))

print(f"\ndtypes after conversion:\n{df_work.dtypes}")


# =============================================================================
# 5. STRING OPERATIONS — THE .str ACCESSOR
# =============================================================================

print("\n" + "=" * 60)
print("5. STRING OPERATIONS (.str accessor)")
print("=" * 60)

# The .str accessor provides vectorized string methods for Series of strings.
# These work like Python string methods but apply to every element at once.

df_str = df_work.copy()

# Introduce some messy string data to clean
df_str["customer_name"] = df_str["customer_name"].str.strip()  # remove whitespace
df_str["product"] = df_str["product"].str.strip()

# Case operations
df_str["customer_upper"] = df_str["customer_name"].str.upper()
df_str["product_lower"] = df_str["product"].str.lower()
df_str["customer_title"] = df_str["customer_name"].str.title()
print("String case operations:")
print(df_str[["customer_name", "customer_upper", "product_lower"]].head(5))

# Contains — boolean mask (useful for filtering)
laptop_mask = df_str["product"].str.contains("Laptop", case=False, na=False)
print(f"\nRows containing 'Laptop': {laptop_mask.sum()}")

# Replace substrings
df_str["product_clean"] = df_str["product"].str.replace('"', 'in', regex=False)
print(f"\nProduct with quote replaced:\n{df_str['product_clean'].unique()}")

# Split strings — returns a Series of lists
df_str["first_name"] = df_str["customer_name"].str.split().str[0]
df_str["last_name"] = df_str["customer_name"].str.split().str[-1]
print(f"\nName splitting:\n{df_str[['customer_name', 'first_name', 'last_name']].head(5)}")

# startswith, endswith, len
print(f"\nProducts starting with 'W': {df_str['product'].str.startswith('W').sum()}")
print(f"Average product name length: {df_str['product'].str.len().mean():.1f}")

# Extract patterns with regex
# Example: extract order number from "ORD-1001"
order_strings = pd.Series(["ORD-1001", "ORD-1002", "ORD-1003"])
extracted = order_strings.str.extract(r"ORD-(\d+)")
print(f"\nExtracted order numbers:\n{extracted}")


# =============================================================================
# 6. RENAMING AND REORGANIZING COLUMNS
# =============================================================================

print("\n" + "=" * 60)
print("6. RENAMING AND REORGANIZING COLUMNS")
print("=" * 60)

df_clean = df_work[["order_id", "date", "customer_name", "product",
                     "category", "quantity", "unit_price", "region"]].copy()

# rename() — rename specific columns
df_clean = df_clean.rename(columns={
    "customer_name": "customer",
    "unit_price": "price_usd",
})
print(f"Columns after rename: {list(df_clean.columns)}")

# Lowercase all column names (common normalization step)
df_clean.columns = df_clean.columns.str.lower().str.replace(" ", "_")
print(f"Lowercase columns: {list(df_clean.columns)}")

# Add a calculated column
df_clean["total_amount"] = (df_clean["quantity"] * df_clean["price_usd"]).round(2)

# Reorder columns
desired_order = ["order_id", "date", "customer", "product", "category",
                 "region", "quantity", "price_usd", "total_amount"]
df_clean = df_clean[desired_order]
print(f"\nFinal column order: {list(df_clean.columns)}")

# Drop columns we don't need
df_clean = df_clean.drop(columns=[])  # nothing to drop here, but syntax shown

# --- replace() — replace specific values ---
# Map region abbreviations to full names
region_map = {"North": "North Region", "South": "South Region",
              "East": "East Region",  "West": "West Region",
              "Unknown": "Unspecified"}
df_clean["region"] = df_clean["region"].astype(str).replace(region_map)
print(f"\nRegion values after replace: {df_clean['region'].unique()}")


# =============================================================================
# MAIN DEMO — FULL CLEANING PIPELINE
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("PRACTICAL DEMO: Full Data Cleaning Pipeline")
    print("=" * 60)

    # Load raw data
    raw = pd.read_csv(DATA_DIR / "sales.csv")
    print(f"\n[1] Raw data: {len(raw)} rows, {raw.isnull().sum().sum()} null cells")

    # Step 1: Remove exact duplicates
    cleaned = raw.drop_duplicates(subset=["order_id"], keep="first").copy()
    print(f"[2] After dedup: {len(cleaned)} rows")

    # Step 2: Fill missing values
    cleaned["quantity"] = pd.to_numeric(cleaned["quantity"], errors="coerce").fillna(1).astype(int)
    cleaned["unit_price"] = pd.to_numeric(cleaned["unit_price"], errors="coerce")
    cleaned["unit_price"] = cleaned["unit_price"].fillna(cleaned["unit_price"].median())
    cleaned["region"] = cleaned["region"].fillna("Unknown")
    cleaned["customer_name"] = cleaned["customer_name"].fillna("Anonymous")
    print(f"[3] Nulls after fill: {cleaned.isnull().sum().sum()}")

    # Step 3: Type conversion
    cleaned["date"] = pd.to_datetime(cleaned["date"])
    cleaned["category"] = cleaned["category"].astype("category")

    # Step 4: String cleaning
    cleaned["customer_name"] = cleaned["customer_name"].str.strip().str.title()
    cleaned["product"] = cleaned["product"].str.strip()

    # Step 5: Derived column
    cleaned["total_amount"] = (cleaned["quantity"] * cleaned["unit_price"]).round(2)

    print(f"[4] Final dtypes:\n{cleaned.dtypes}")
    print(f"\n[5] Cleaned data ({len(cleaned)} rows):")
    print(cleaned.to_string())
