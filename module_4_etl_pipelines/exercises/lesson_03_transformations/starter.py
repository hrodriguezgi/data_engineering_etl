# Exercise: Lesson 03 - Data Transformations (Enrichment & Derived Columns)

import pandas as pd
from pathlib import Path
from typing import Dict, Tuple

# Reference data
PRODUCTS = {
    "P001": {"category": "Electronics", "tax_rate": 0.08, "margin": 0.15},
    "P002": {"category": "Clothing", "tax_rate": 0.05, "margin": 0.40},
    "P003": {"category": "Food", "tax_rate": 0.02, "margin": 0.35},
}

# Sample transactions
TRANSACTIONS_CSV = """transaction_id,product_id,amount,timestamp
T1,P001,999.99,2024-01-15T09:00:00Z
T2,P002,49.99,2024-01-15T10:30:00Z
T3,UNKNOWN,25.00,2024-01-15T14:00:00Z
T4,P001,1299.99,2024-01-15T16:45:00Z
T5,,59.99,2024-01-15T18:00:00Z"""


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """
    TODO: Normalize data for consistency.
    - Uppercase product_ids
    - Parse timestamps to datetime
    - Round amounts to 2 decimals
    """
    pass


def enrich(df: pd.DataFrame) -> pd.DataFrame:
    """
    TODO: Enrich with product reference data using product_id.
    Add columns:
    - category (default "UNKNOWN" if product not found)
    - tax_rate (default 0.0)
    - margin (default 0.2)
    """
    pass


def derive_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    TODO: Compute derived columns:
    - tax_amount = amount * tax_rate
    - total_with_tax = amount + tax_amount
    - profit = amount * margin
    - hour_of_day = hour from timestamp
    """
    pass


def aggregate_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """
    TODO: Create product category summary:
    Group by category, compute:
    - total_orders (count)
    - total_amount (sum)
    - avg_order (mean)
    - total_profit (sum)
    """
    pass


def aggregate_by_hour(df: pd.DataFrame) -> pd.DataFrame:
    """
    TODO: Create hourly summary:
    Group by hour_of_day, compute:
    - transactions (count)
    - avg_amount (mean)
    - total_profit (sum)
    """
    pass


# --- TEST ---

if __name__ == "__main__":
    # Load transactions
    df = pd.read_csv(pd.io.common.StringIO(TRANSACTIONS_CSV), dtype=str, keep_default_na=False).replace("", None)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    print("Original data:")
    print(df)

    # Transform pipeline
    df = normalize(df)
    print("\nAfter normalize:")
    print(df)

    df = enrich(df)
    print("\nAfter enrich:")
    print(df[["transaction_id", "product_id", "category", "tax_rate", "margin"]])

    df = derive_columns(df)
    print("\nAfter derive_columns:")
    print(df[["transaction_id", "amount", "tax_amount", "total_with_tax", "profit", "hour_of_day"]])

    cat_summary = aggregate_by_category(df)
    print("\nCategory summary:")
    print(cat_summary)

    hour_summary = aggregate_by_hour(df)
    print("\nHour summary:")
    print(hour_summary)

    print("\n✓ Done!")
