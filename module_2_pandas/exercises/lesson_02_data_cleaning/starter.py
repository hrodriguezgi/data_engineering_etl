"""Exercise 02 starter: data cleaning with pandas."""

from pathlib import Path

import pandas as pd

DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "sales.csv"


def load_sales() -> pd.DataFrame:
    """Load the raw sales CSV."""
    # TODO
    return pd.DataFrame()


def clean_sales(df: pd.DataFrame) -> pd.DataFrame:
    """Return a cleaned copy of the sales dataset."""
    # TODO:
    # - drop duplicate order_id rows
    # - fill missing quantity, unit_price, customer_name, and region
    # - convert quantity to int
    # - add total_amount rounded to 2 decimals
    return df.copy()


def build_quality_report(df: pd.DataFrame) -> dict:
    """Summarize key quality checks for the cleaned dataset."""
    # TODO
    return {
        "row_count": 0,
        "null_quantity": 0,
        "null_unit_price": 0,
        "anonymous_customers": 0,
        "unknown_regions": 0,
        "grand_total": 0.0,
    }


if __name__ == "__main__":
    raw_df = load_sales()
    clean_df = clean_sales(raw_df)
    report = build_quality_report(clean_df)

    print("Cleaned sales:")
    print(clean_df.head())

    print("\nQuality report:")
    print(report)
