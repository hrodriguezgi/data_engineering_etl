"""Exercise 05 starter: merging and joining with pandas."""

from pathlib import Path

import pandas as pd

SALES_FILE = Path(__file__).resolve().parents[2] / "data" / "sales.csv"
CUSTOMERS_FILE = Path(__file__).resolve().parents[2] / "data" / "customers.csv"


def load_clean_sales() -> pd.DataFrame:
    """Load sales.csv and return the cleaned dataset."""
    # TODO
    return pd.DataFrame()


def load_customers() -> pd.DataFrame:
    """Load the customer reference table."""
    # TODO
    return pd.DataFrame()


def join_sales_with_customers(sales_df: pd.DataFrame, customers_df: pd.DataFrame) -> pd.DataFrame:
    """Return a left join with the merge indicator included."""
    # TODO
    return pd.DataFrame()


def get_unmatched_orders(joined_df: pd.DataFrame) -> pd.DataFrame:
    """Return only unmatched orders."""
    # TODO
    return pd.DataFrame()


def build_country_summary(joined_df: pd.DataFrame) -> pd.DataFrame:
    """Return country revenue for matched rows only."""
    # TODO
    return pd.DataFrame()


if __name__ == "__main__":
    sales_df = load_clean_sales()
    customers_df = load_customers()
    joined_df = join_sales_with_customers(sales_df, customers_df)
    unmatched_df = get_unmatched_orders(joined_df)
    country_summary = build_country_summary(joined_df)

    print("Joined data:")
    print(joined_df.head())

    print("\nUnmatched orders:")
    print(unmatched_df[["order_id", "customer_name", "_merge"]])

    print("\nCountry summary:")
    print(country_summary)
