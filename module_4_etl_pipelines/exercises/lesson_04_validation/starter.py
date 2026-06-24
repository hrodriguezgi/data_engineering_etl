# Exercise: Lesson 04 - Building a Validation Framework

import pandas as pd
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Dict, List, Tuple

SAMPLE_CSV = """customer_id,email,age,birth_date,phone
C001,alice@example.com,28,1996-05-15,555-1234
C002,bob.example.com,31,1993-08-20,
C003,,45,1979-03-10,555-5678
C004,carol@example.com,150,1874-01-01,555-9999
C005,dave@example.com,22,2030-12-31,555-4444
C006,eve@example.com,35,1989-06-15,"""


@dataclass
class ValidationRule:
    """
    TODO: Define a ValidationRule with:
    - name (str): rule identifier
    - description (str): what it checks
    - check (Callable): function(df) -> boolean mask (True = valid)
    - severity (str): "error" or "warning"
    """
    pass


@dataclass
class ValidationReport:
    """
    TODO: Define a ValidationReport that tracks:
    - total_records, valid_records, invalid_records, warning_records
    - rule_results: list of dicts with rule details
    - Method: summary() -> formatted string report
    """
    pass


class DataValidator:
    """
    TODO: Implement DataValidator with:
    - __init__(name): initialize with validator name
    - add_rule(rule): add a ValidationRule, return self for chaining
    - validate(df): run all rules, return (valid_df, invalid_df, report)
      - Add _validation_errors and _validation_warnings columns
      - Track which rules each record fails
    """
    pass


# --- DEFINE RULES ---

def build_customer_validator() -> DataValidator:
    """
    TODO: Build a DataValidator with customer-specific rules:

    Error rules (reject record):
    - required_email: email must be non-null
    - valid_email_format: email must contain @ and .
    - valid_age: age must be 18-120
    - valid_birth_date: birth_date must not be in future

    Warning rules (flag but keep):
    - recommended_contact: must have email OR phone
    """
    pass


# --- TEST ---

if __name__ == "__main__":
    # Load sample data
    df = pd.read_csv(pd.io.common.StringIO(SAMPLE_CSV), dtype=str, keep_default_na=False).replace("", None)
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df["birth_date"] = pd.to_datetime(df["birth_date"], errors="coerce")

    print("Sample data:")
    print(df)
    print()

    # Validate
    validator = build_customer_validator()
    valid_df, invalid_df, report = validator.validate(df)

    # Show report
    print(report.summary())

    # Show invalid records
    if len(invalid_df) > 0:
        print(f"\nInvalid records ({len(invalid_df)}):")
        print(invalid_df[["customer_id", "email", "age", "_validation_errors"]])

    # Show warnings
    warned = valid_df[valid_df["_validation_warnings"].notna()]
    if len(warned) > 0:
        print(f"\nWarnings ({len(warned)}):")
        print(warned[["customer_id", "email", "phone", "_validation_warnings"]])

    print("\n✓ Done!")
