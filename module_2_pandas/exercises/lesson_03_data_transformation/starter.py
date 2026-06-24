"""Exercise 03 starter: data transformation with pandas."""

from pathlib import Path

import pandas as pd

DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "sales.csv"


def load_clean_sales() -> pd.DataFrame:
    """Load sales.csv and return the cleaned dataset."""
    # TODO
    return pd.DataFrame()


def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add order_month and size_band columns."""
    # TODO
    return df.copy()


def build_region_category_pivot(df: pd.DataFrame) -> pd.DataFrame:
    """Return a revenue pivot table by region and category."""
    # TODO
    return pd.DataFrame()


def build_monthly_revenue(df: pd.DataFrame) -> dict:
    """Return monthly revenue totals as a dict."""
    # TODO
    return {}


if __name__ == "__main__":
    sales_df = load_clean_sales()
    enriched_df = add_derived_columns(sales_df)
    pivot_df = build_region_category_pivot(enriched_df)
    monthly_revenue = build_monthly_revenue(enriched_df)

    print("Enriched sales:")
    print(enriched_df[["order_id", "order_month", "size_band", "total_amount"]].head())

    print("\nRegion/category pivot:")
    print(pivot_df)

    print("\nMonthly revenue:")
    print(monthly_revenue)
