"""Exercise 03 starter: reusable ETL functions."""

from typing import Dict, List

RAW_RECORDS = [
    {"id": 1, "status": "active", "amount": "250.00"},
    {"id": 2, "status": "inactive", "amount": "90.00"},
    {"id": 3, "status": "active", "amount": "175.5"},
    {"id": 4, "status": "active", "amount": "invalid"},
]


def extract_active(records: List[Dict]) -> List[Dict]:
    """Return only active records."""
    # TODO
    return records


def transform_amount(records: List[Dict], tax_rate: float = 0.08) -> List[Dict]:
    """Cast amount to float and add amount_with_tax."""
    transformed: List[Dict] = []
    # TODO
    return transformed


def load_summary(records: List[Dict]) -> Dict:
    """Return aggregate metrics for transformed records."""
    # TODO
    return {
        "count": 0,
        "total_amount": 0.0,
        "total_amount_with_tax": 0.0,
    }


def run_pipeline(records: List[Dict]) -> Dict:
    """Run extract -> transform -> load summary."""
    active = extract_active(records)
    transformed = transform_amount(active)
    return load_summary(transformed)


if __name__ == "__main__":
    summary = run_pipeline(RAW_RECORDS)
    print(summary)
