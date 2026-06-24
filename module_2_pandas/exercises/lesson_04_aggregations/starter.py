"""Exercise 04 starter: aggregations with pandas."""

from pathlib import Path

import pandas as pd

DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "sales.csv"


def load_clean_sales() -> pd.DataFrame:
    """Load sales.csv and return the cleaned dataset."""
    # TODO
    return pd.DataFrame()


def summarize_by_customer(df: pd.DataFrame) -> pd.DataFrame:
    """Return customer-level metrics sorted by total_revenue descending."""
    # TODO
    return pd.DataFrame()


def summarize_by_region(df: pd.DataFrame) -> pd.DataFrame:
    """Return region-level metrics sorted by total_revenue descending."""
    # TODO
    return pd.DataFrame()


if __name__ == "__main__":
    sales_df = load_clean_sales()
    customer_summary = summarize_by_customer(sales_df)
    region_summary = summarize_by_region(sales_df)

    print("Customer summary:")
    print(customer_summary.head())

    print("\nRegion summary:")
    print(region_summary)
