"""Exercise 01 starter: data types and collections."""

from typing import Dict, List, Tuple

RAW_RECORDS = [
    {"id": 1, "customer": "Alice", "amount": "250.00"},
    {"id": 2, "customer": "Bob", "amount": "-30"},
    {"id": 3, "customer": "Carol", "amount": "175.5"},
    {"id": 4, "customer": "", "amount": "80"},
    {"id": 5, "customer": "Eve", "amount": "100"},
]


def clean_records(records: List[Dict]) -> Tuple[List[Dict], int]:
    """Return (valid_records, invalid_count)."""
    valid_records: List[Dict] = []
    invalid_count = 0

    # TODO:
    # - iterate records
    # - validate customer and amount
    # - cast amount to float
    # - append valid records
    # - count invalid records

    return valid_records, invalid_count


def build_summary(valid_records: List[Dict], invalid_count: int) -> Dict:
    """Build summary metrics for cleaned records."""
    # TODO: compute metrics according to README acceptance criteria
    return {
        "valid_count": 0,
        "invalid_count": invalid_count,
        "total_amount": 0.0,
        "customers": [],
    }


if __name__ == "__main__":
    cleaned, invalid = clean_records(RAW_RECORDS)
    summary = build_summary(cleaned, invalid)

    print("Cleaned records:")
    for row in cleaned:
        print(row)

    print("\nSummary:")
    print(summary)
