"""Exercise 02 starter: control flow and routing."""

from typing import Dict, List, Tuple

RAW_RECORDS = [
    {"id": 1, "status": "active", "amount": "250"},
    {"id": 2, "status": "inactive", "amount": "500"},
    {"id": 3, "status": "active", "amount": "175"},
    {"id": 4, "status": "active", "amount": "not_a_number"},
    {"id": 5, "status": "active", "amount": "300"},
]


def route_records(records: List[Dict]) -> Tuple[Dict[str, List[Dict]], Dict[str, int]]:
    """Route records into priority, standard, and invalid buckets."""
    buckets = {"priority": [], "standard": [], "invalid": []}

    # TODO: implement routing rules from README.md

    summary = {
        "priority": len(buckets["priority"]),
        "standard": len(buckets["standard"]),
        "invalid": len(buckets["invalid"]),
    }
    return buckets, summary


if __name__ == "__main__":
    buckets, summary = route_records(RAW_RECORDS)

    print("Routed IDs:")
    for name, items in buckets.items():
        print(f"{name}: {[row['id'] for row in items]}")

    print("\nSummary:")
    print(summary)
