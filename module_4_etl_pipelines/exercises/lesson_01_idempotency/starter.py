# Exercise: Lesson 01 - Building an Idempotent Pipeline
# Complete the three phases of ETL and ensure idempotency.

import io
import csv
from datetime import datetime
from typing import List, Dict, Tuple

# Test CSV data (in-memory)
CSV_DATA = """id,name,email,signup_date
1,Alice Johnson,alice@example.com,2023-01-15
2,Bob Smith,  BOB@EXAMPLE.COM  ,2023-02-20
3,Carol White,carol@example.com,invalid-date
4,,dave@example.com,2023-04-10
5,Eve Davis,eve@example.com,2023-05-12"""


def extract(csv_content: str) -> List[Dict]:
    """
    Extract phase: Read CSV without modification.

    Args:
        csv_content: Raw CSV data as string

    Returns:
        List of raw records from CSV
    """
    # TODO: Implement extract
    # Hint: Use csv.DictReader to parse the CSV
    pass


def transform(records: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """
    Transform phase: Clean and validate customer data.

    Args:
        records: Raw records from extract

    Returns:
        Tuple of (valid_records, rejected_records)

    Valid records must have:
    - non-empty id
    - non-empty email
    - valid date in YYYY-MM-DD format

    Cleaning:
    - Strip whitespace from name and email
    - Lowercase emails
    - Parse dates
    """
    # TODO: Implement transform
    pass


def load_idempotent(records: List[Dict], destination: Dict) -> Dict:
    """
    Load phase: UPSERT records by id (idempotent).

    If id already exists in destination, update it.
    If id is new, insert it.
    This ensures running the pipeline twice produces the same result.

    Args:
        records: Valid records from transform
        destination: Dictionary representing the database (modified in-place)

    Returns:
        Dict with stats: {"inserted": count, "updated": count}
    """
    # TODO: Implement idempotent load
    pass


def run_pipeline(csv_content: str, destination: Dict) -> Tuple[int, int]:
    """
    Run the full ETL pipeline.

    Args:
        csv_content: Raw CSV data
        destination: Dictionary to load into

    Returns:
        Tuple of (inserted, updated)
    """
    # TODO: Call extract, transform, and load_idempotent in sequence
    pass


# --- TEST YOUR IMPLEMENTATION ---

if __name__ == "__main__":
    # Initialize destination
    db = {}

    # First run
    print("First run:")
    inserted, updated = run_pipeline(CSV_DATA, db)
    print(f"  Inserted: {inserted}, Updated: {updated}")
    print(f"  DB size: {len(db)}")

    # Second run (same data — should be idempotent!)
    print("\nSecond run (same data):")
    inserted, updated = run_pipeline(CSV_DATA, db)
    print(f"  Inserted: {inserted}, Updated: {updated}")
    print(f"  DB size: {len(db)} (should be unchanged!)")

    # Check idempotency
    if inserted == 0 and updated > 0:
        print("\n✓ Idempotency verified! Second run updated but didn't insert.")
    else:
        print("\n✗ Idempotency failed. Second run shouldn't insert new records.")

    # Show loaded data
    print("\nLoaded customers:")
    for cust_id, record in sorted(db.items()):
        print(f"  {record}")
