"""Exercise 01 starter: intro to pandas."""

import pandas as pd

RAW_ORDERS = [
    {"order_id": 2001, "customer": "Alice", "product": "Laptop Stand", "quantity": 2, "unit_price": 39.99},
    {"order_id": 2002, "customer": "Bob", "product": "USB-C Hub", "quantity": 1, "unit_price": 49.99},
    {"order_id": 2003, "customer": "Carol", "product": 'Monitor 27"', "quantity": 1, "unit_price": 249.99},
    {"order_id": 2004, "customer": "Alice", "product": "Webcam HD", "quantity": 3, "unit_price": 79.99},
    {"order_id": 2005, "customer": "Dave", "product": "Keyboard", "quantity": 2, "unit_price": 89.99},
]


def build_orders_frame(records: list[dict]) -> pd.DataFrame:
    """Create the base DataFrame and add total_amount."""
    # TODO:
    # - build a DataFrame from records
    # - add total_amount = quantity * unit_price
    # - round total_amount to 2 decimals
    return pd.DataFrame()


def filter_high_value_orders(df: pd.DataFrame) -> pd.DataFrame:
    """Return only orders with total_amount >= 150."""
    # TODO
    return df


def build_summary(df: pd.DataFrame) -> dict:
    """Build a small business summary from the orders DataFrame."""
    # TODO
    return {
        "row_count": 0,
        "grand_total": 0.0,
        "top_product": "",
        "high_value_orders": 0,
    }


if __name__ == "__main__":
    orders_df = build_orders_frame(RAW_ORDERS)
    high_value_df = filter_high_value_orders(orders_df)
    summary = build_summary(orders_df)

    print("Orders DataFrame:")
    print(orders_df)

    print("\nHigh value orders:")
    print(high_value_df)

    print("\nSummary:")
    print(summary)
