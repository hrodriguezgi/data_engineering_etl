"""
Module 1 - Lesson 0: Introduction to Python for Data Engineering
=================================================================
Python is one of the core languages for data engineering because it offers:
  - Fast development and readable syntax
  - A strong ecosystem for data processing (pandas, requests, SQL libraries)
  - Easy integration with files, APIs, and databases
  - Strong support for automation and ETL orchestration

In real ETL work, Python scripts usually follow this flow:
  extract() -> transform() -> validate() -> load()

This introductory lesson shows:
  - Why Python is used in data engineering
  - Typical responsibilities of an ETL script
  - A tiny end-to-end ETL-style example in pure Python
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List

# =============================================================================
# 1. WHY PYTHON IN DATA ENGINEERING
# =============================================================================

print("--- Why Python for Data Engineering ---")

reasons = [
    "Readable syntax: easier maintenance for data teams",
    "Large ecosystem: pandas, numpy, pyarrow, sqlalchemy, requests",
    "Flexible I/O: CSV, JSON, Excel, Parquet, APIs, databases",
    "Automation-ready: scheduling, logging, and pipeline scripting",
]

for i, reason in enumerate(reasons, start=1):
    print(f"{i}. {reason}")


# =============================================================================
# 2. ETL RESPONSIBILITIES (CONCEPTUAL)
# =============================================================================

print("\n--- Typical ETL Responsibilities ---")

etl_phases = {
    "extract": "Read data from source systems (files, APIs, DBs)",
    "transform": "Clean and standardize data for analytics",
    "validate": "Enforce quality rules and reject bad records",
    "load": "Write trusted data to destination systems",
}

for phase, description in etl_phases.items():
    print(f"{phase.upper():9s} -> {description}")


# =============================================================================
# 3. MINI ETL DEMO (PURE PYTHON)
# =============================================================================

print("\n--- Mini ETL Demo ---")


def extract() -> List[Dict]:
    """Simulate extraction from a raw source."""
    return [
        {"id": 1, "customer": "Alice", "amount": "250.00", "country": "co"},
        {"id": 2, "customer": "Bob", "amount": "-30", "country": "mx"},
        {"id": 3, "customer": "Carol ", "amount": "175.5", "country": "co"},
        {"id": 4, "customer": "", "amount": "invalid", "country": "pe"},
        {"id": 5, "customer": " John ", "amount": "120.00", "country": "cl"},
        {"id": 6, "customer": "  Charlie", "amount": "90.00", "country": "mx"},
    ]


def transform(records: List[Dict]) -> List[Dict]:
    """Normalize fields and cast data types where possible."""
    transformed = []
    for row in records:
        new_row = row.copy()
        new_row["country"] = new_row["country"].upper()
        new_row["customer"] = new_row["customer"].strip().title()

        try:
            new_row["amount"] = float(new_row["amount"])
        except (TypeError, ValueError):
            new_row["amount"] = None

        transformed.append(new_row)

    return transformed


def validate(records: List[Dict]) -> List[Dict]:
    """Keep only records that pass basic quality rules."""
    valid = []
    for row in records:
        if not row["customer"]:
            continue
        if row["amount"] is None or row["amount"] <= 0:
            continue
        valid.append(row)
    return valid


def load(records: List[Dict]) -> int:
    """Simulate loading records into a destination."""
    print("Records ready for destination:")
    for row in records:
        print(
            f"  id={row['id']}, customer={row['customer']}, amount={row['amount']}, country={row['country']}"
        )
    return len(records)


if __name__ == "__main__":
    print(f"Run timestamp: {datetime.now().isoformat(timespec='seconds')}")

    raw = extract()
    clean = transform(raw)
    trusted = validate(clean)
    loaded_count = load(trusted)

    print(
        f"\nSummary: extracted={len(raw)}, trusted={len(trusted)}, loaded={loaded_count}"
    )
