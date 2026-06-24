# Exercise: Lesson 02 - Build an End-to-End ETL Pipeline
#
# Process web service logs from CSV → SQLite
# Handle data quality issues gracefully

import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple
from sqlalchemy import create_engine

# Sample CSV data (paste into sample_logs.csv)
SAMPLE_CSV = """request_id,timestamp,endpoint,status_code,response_time_ms,user_id
1,2024-01-15T10:30:00Z,/api/users,200,45.2,user123
2,2024-01-15T10:30:05Z,/api/posts,200,120.5,user456
3,2024-01-15T10:30:10Z,/api/comments,invalid_date,80.3,user789
4,2024-01-15T10:30:15Z,/api/users,-1,90.1,user123
5,2024-01-15T10:30:20Z,/api/posts,201,150.0,
6,2024-01-15T10:30:25Z,/api/comments,999,200.5,user456
7,2024-01-15T10:30:30Z,/api/data,,55.0,user789
8,2024-01-15T10:30:35Z,/api/users,200,-5.2,user123
9,2024-01-15T10:30:40Z,/api/posts,200,500.0,user456
10,2024-01-15T10:30:45Z,/api/webhook,200,1200.3,user789"""


def extract(csv_path: Path) -> pd.DataFrame:
    """
    Extract logs from CSV file.

    TODO: Read the CSV with dtype=str to avoid silent conversions.

    Args:
        csv_path: Path to CSV file

    Returns:
        Raw DataFrame
    """
    pass


def transform(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Transform and validate log records.

    TODO: Implement the following:
    1. Strip whitespace from string columns
    2. Parse request_id as integer
    3. Parse timestamp as datetime
    4. Validate status_code (must be 200-599)
    5. Parse response_time_ms as float (reject if negative)
    6. Fill missing user_ids with "UNKNOWN"
    7. Create response_time_bucket: "fast" (<100), "medium" (<500), "slow"
    8. Add _etl_loaded_at timestamp
    9. Return (valid_df, rejected_df)

    Args:
        df: Raw DataFrame from extract

    Returns:
        Tuple of (clean_df, rejected_df)
    """
    pass


def load(clean_df: pd.DataFrame, rejected_df: pd.DataFrame, db_path: Path) -> dict:
    """
    Load clean and rejected records to SQLite.

    TODO: Create an engine and:
    1. Write clean_df to 'logs' table (replace=idempotent)
    2. Write rejected_df to 'logs_rejected' table

    Args:
        clean_df: Valid records
        rejected_df: Invalid records with _rejection_reason
        db_path: Path to SQLite database

    Returns:
        Dict with load statistics
    """
    pass


# --- TEST ---

if __name__ == "__main__":
    # Create sample CSV file
    csv_path = Path("sample_logs.csv")
    csv_path.write_text(SAMPLE_CSV)
    db_path = Path("logs.db")

    # Run pipeline
    print("Extracting...")
    raw_df = extract(csv_path)
    print(f"  Read {len(raw_df)} rows\n")

    print("Transforming...")
    clean_df, rejected_df = transform(raw_df)
    print(f"  {len(clean_df)} valid, {len(rejected_df)} rejected\n")

    print("Loading...")
    stats = load(clean_df, rejected_df, db_path)
    print(f"  {stats}\n")

    # Verify
    print("Verification:")
    engine = create_engine(f"sqlite:///{db_path}")
    logs = pd.read_sql("SELECT * FROM logs ORDER BY request_id", con=engine)
    print(f"\n[Logs Table] ({len(logs)} rows):")
    print(logs.to_string(index=False))

    try:
        rejected = pd.read_sql(
            "SELECT request_id, status_code, response_time_ms, _rejection_reason FROM logs_rejected",
            con=engine
        )
        print(f"\n[Rejected Table] ({len(rejected)} rows):")
        print(rejected.to_string(index=False))
    except:
        print("\nNo rejected records")

    engine.dispose()

    # Cleanup
    if db_path.exists():
        db_path.unlink()
    csv_path.unlink()

    print("\n✓ Done!")
