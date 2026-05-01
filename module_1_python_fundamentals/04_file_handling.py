"""
Module 1 - Lesson 4: File Handling
=====================================
Data engineering involves constant reading and writing of files.
Understanding how to work with different file formats is essential.

Topics covered:
  - Opening and closing files (open() and the `with` statement)
  - Reading text files (read, readline, readlines, iteration)
  - Writing text files
  - Appending to files
  - Working with CSV files using the csv module and pandas
  - Working with JSON files
  - File paths with the pathlib module
  - Checking if files/directories exist
"""

import csv
import json
import os
from pathlib import Path


# =============================================================================
# SETUP: Determine the directory where this script lives
# =============================================================================

# Using pathlib for robust, cross-platform file paths
SCRIPT_DIR = Path(__file__).parent        # directory containing this script
DATA_DIR = SCRIPT_DIR / "demo_data"       # subdirectory for demo files
DATA_DIR.mkdir(exist_ok=True)             # create it if it doesn't exist

print(f"Script directory: {SCRIPT_DIR}")
print(f"Data directory:   {DATA_DIR}")


# =============================================================================
# 1. TEXT FILES — WRITING
# =============================================================================

print("\n--- Writing Text Files ---")

# The `with` statement (context manager) ensures the file is closed properly
# even if an error occurs. Always use `with` for file I/O.
text_file = DATA_DIR / "sample.txt"

with open(text_file, "w", encoding="utf-8") as f:
    # write() writes a string — you must add \n yourself
    f.write("Line 1: Data Engineering\n")
    f.write("Line 2: ETL Pipelines\n")
    f.write("Line 3: Python is awesome\n")

print(f"Written to: {text_file}")

# Writing multiple lines at once with writelines()
lines_to_write = ["apple\n", "banana\n", "cherry\n"]
multi_file = DATA_DIR / "fruits.txt"

with open(multi_file, "w", encoding="utf-8") as f:
    f.writelines(lines_to_write)   # writelines() does NOT add newlines automatically!

print(f"Written fruits to: {multi_file}")


# =============================================================================
# 2. TEXT FILES — READING
# =============================================================================

print("\n--- Reading Text Files ---")

# Method 1: read() — reads entire file into a single string
with open(text_file, "r", encoding="utf-8") as f:
    content = f.read()
print(f"read() result type: {type(content)}")
print(f"Content:\n{content}")

# Method 2: readlines() — reads all lines into a list of strings
with open(text_file, "r", encoding="utf-8") as f:
    lines = f.readlines()   # each string includes the trailing \n
print(f"readlines() result: {lines}")

# Strip the newline characters
stripped_lines = [line.rstrip("\n") for line in lines]
print(f"Stripped: {stripped_lines}")

# Method 3: Iterate line by line (BEST for large files — low memory usage)
print("Iterating line by line:")
with open(text_file, "r", encoding="utf-8") as f:
    for line_number, line in enumerate(f, start=1):
        print(f"  Line {line_number}: {line.rstrip()}")

# Method 4: readline() — reads one line at a time
with open(text_file, "r", encoding="utf-8") as f:
    first_line = f.readline()
    second_line = f.readline()
print(f"First line: {first_line!r}")
print(f"Second line: {second_line!r}")


# =============================================================================
# 3. APPENDING TO FILES
# =============================================================================

print("\n--- Appending to Files ---")

# Mode "a" appends to the end of the file (creates it if it doesn't exist)
log_file = DATA_DIR / "etl_log.txt"

for i in range(3):
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[RUN {i+1}] Pipeline completed successfully\n")

print(f"Log file written 3 times:")
with open(log_file, "r", encoding="utf-8") as f:
    print(f.read())


# =============================================================================
# 4. CSV FILES — WRITING WITH csv MODULE
# =============================================================================

print("--- CSV Files ---")

sales_csv = DATA_DIR / "sales_demo.csv"

# Define the data
fieldnames = ["order_id", "customer", "product", "quantity", "unit_price"]
rows = [
    {"order_id": 1001, "customer": "Alice", "product": "Laptop", "quantity": 1, "unit_price": 999.99},
    {"order_id": 1002, "customer": "Bob",   "product": "Mouse",  "quantity": 3, "unit_price": 29.99},
    {"order_id": 1003, "customer": "Carol", "product": "Monitor","quantity": 2, "unit_price": 349.99},
    {"order_id": 1004, "customer": "Dave",  "product": "Keyboard","quantity": 1,"unit_price": 79.99},
]

# Write CSV using DictWriter
with open(sales_csv, "w", newline="", encoding="utf-8") as f:
    # newline="" is important on Windows to prevent extra blank lines
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()      # writes the header row
    writer.writerows(rows)    # writes all data rows

print(f"Written CSV: {sales_csv}")


# =============================================================================
# 5. CSV FILES — READING WITH csv MODULE
# =============================================================================

# Read with DictReader — each row becomes a dict with column names as keys
print("\nReading CSV with DictReader:")
with open(sales_csv, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        # Note: ALL values are strings when read from CSV — always convert types!
        total = int(row["quantity"]) * float(row["unit_price"])
        print(f"  {row['customer']:8s}: {row['product']:10s} = ${total:.2f}")

# Read with reader (list-based, no automatic column names)
print("\nReading CSV with reader (raw rows):")
with open(sales_csv, "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    header = next(reader)    # consume and store the header row
    print(f"  Header: {header}")
    for row in reader:
        print(f"  Row: {row}")


# =============================================================================
# 6. CSV FILES — READING WITH PANDAS (RECOMMENDED FOR DATA ENGINEERING)
# =============================================================================

print("\n--- CSV with Pandas ---")

try:
    import pandas as pd

    # pd.read_csv is the standard way to load CSV data in data engineering
    df = pd.read_csv(sales_csv)
    print(f"Shape: {df.shape} (rows, columns)")
    print(f"Columns: {list(df.columns)}")
    print(df.to_string())

    # Pandas keeps dtypes correctly for numeric columns
    print(f"\ndtypes:\n{df.dtypes}")

    # Adding a calculated column
    df["total"] = df["quantity"] * df["unit_price"]
    print(f"\nWith total column:\n{df[['customer', 'product', 'total']].to_string()}")

    # Writing back to CSV
    output_csv = DATA_DIR / "sales_with_total.csv"
    df.to_csv(output_csv, index=False)  # index=False avoids writing the row numbers
    print(f"\nSaved with totals to: {output_csv}")

except ImportError:
    print("pandas not installed — skipping pandas CSV demo")


# =============================================================================
# 7. JSON FILES — WRITING
# =============================================================================

print("\n--- JSON Files ---")

# JSON is the lingua franca of web APIs. Python's json module handles it natively.
pipeline_config = {
    "pipeline_name": "sales_etl",
    "version": "1.0",
    "source": {
        "type": "csv",
        "path": "data/sales.csv",
        "encoding": "utf-8"
    },
    "transformations": [
        {"type": "drop_nulls", "columns": ["amount"]},
        {"type": "cast", "column": "amount", "to": "float"},
        {"type": "filter", "condition": "amount > 0"}
    ],
    "destination": {
        "type": "sqlite",
        "database": "output.db",
        "table": "cleaned_sales",
        "if_exists": "replace"
    },
    "active": True,
    "max_rows": None   # None becomes null in JSON
}

config_file = DATA_DIR / "pipeline_config.json"

with open(config_file, "w", encoding="utf-8") as f:
    json.dump(pipeline_config, f, indent=2)  # indent=2 for pretty printing
    # Use indent=None for compact format (smaller files)

print(f"Written JSON config to: {config_file}")

# Show the raw file content
with open(config_file, "r", encoding="utf-8") as f:
    print(f.read())


# =============================================================================
# 8. JSON FILES — READING
# =============================================================================

print("Reading JSON config:")
with open(config_file, "r", encoding="utf-8") as f:
    loaded_config = json.load(f)   # deserialize JSON → Python dict

# Accessing nested values
print(f"Pipeline: {loaded_config['pipeline_name']}")
print(f"Source type: {loaded_config['source']['type']}")
print(f"Source path: {loaded_config['source']['path']}")
print(f"Active: {loaded_config['active']}")
print(f"Max rows: {loaded_config['max_rows']}")  # None (null in JSON)

# List of transformations
print("Transformations:")
for t in loaded_config["transformations"]:
    print(f"  - {t['type']}", end="")
    if "column" in t:
        print(f" on column '{t['column']}'", end="")
    print()

# JSON strings (for API responses, etc.)
json_string = '{"status": "ok", "count": 42, "records": [1, 2, 3]}'
data = json.loads(json_string)    # loads() for string → dict
print(f"\njson.loads result: {data}")

back_to_string = json.dumps(data, indent=2)  # dumps() for dict → string
print(f"json.dumps result:\n{back_to_string}")


# =============================================================================
# 9. PATHLIB — MODERN FILE PATH HANDLING
# =============================================================================

print("\n--- pathlib: Modern File Paths ---")

# pathlib.Path is the modern, object-oriented way to handle file paths.
# It's cross-platform (works on Windows, macOS, Linux).

p = Path("/home/runner/work/data_engineering_etl")

# Path components
print(f"Path: {p}")
print(f"Name: {p.name}")
print(f"Stem: {p.stem}")
print(f"Suffix: {p.suffix}")
print(f"Parent: {p.parent}")

# Building paths (/ operator)
data_path = p / "module_2_pandas" / "data" / "sales.csv"
print(f"Built path: {data_path}")
print(f"Absolute: {data_path.is_absolute()}")

# Check existence
print(f"DATA_DIR exists: {DATA_DIR.exists()}")
print(f"DATA_DIR is dir: {DATA_DIR.is_dir()}")
print(f"sales_csv exists: {sales_csv.exists()}")
print(f"sales_csv is file: {sales_csv.is_file()}")

# List files in a directory
print(f"\nFiles in {DATA_DIR}:")
for f in sorted(DATA_DIR.iterdir()):
    size = f.stat().st_size if f.is_file() else "-"
    print(f"  {'DIR' if f.is_dir() else 'FILE':4s} {f.name} ({size} bytes)")

# Glob pattern matching
print("\nCSV files in data dir:")
for csv_path in DATA_DIR.glob("*.csv"):
    print(f"  {csv_path.name}")

# Creating nested directories
nested = DATA_DIR / "subdir" / "nested"
nested.mkdir(parents=True, exist_ok=True)
print(f"\nCreated nested dir: {nested}")

# Read a file with pathlib
print(f"\nReading {text_file.name} with pathlib:")
content = text_file.read_text(encoding="utf-8")
print(content)


# =============================================================================
# MAIN DEMO
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("PRACTICAL DEMO: ETL File Processing")
    print("=" * 60)

    # Simulate an ETL process that reads from JSON config,
    # processes a CSV, and writes results to a new CSV and JSON summary.

    # Step 1: Read config
    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)
    print(f"\n[1] Loaded config: {config['pipeline_name']}")

    # Step 2: Read source CSV
    source_path = DATA_DIR / "sales_demo.csv"
    records = []
    with open(source_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append({
                "order_id": int(row["order_id"]),
                "customer": row["customer"].strip(),
                "product": row["product"].strip(),
                "quantity": int(row["quantity"]),
                "unit_price": float(row["unit_price"]),
                "total": round(int(row["quantity"]) * float(row["unit_price"]), 2),
            })
    print(f"[2] Loaded {len(records)} records from {source_path.name}")

    # Step 3: Write transformed output CSV
    output_path = DATA_DIR / "etl_output.csv"
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
    print(f"[3] Wrote output to {output_path.name}")

    # Step 4: Write JSON summary
    summary = {
        "pipeline": config["pipeline_name"],
        "records_processed": len(records),
        "total_revenue": round(sum(r["total"] for r in records), 2),
        "top_customer": max(records, key=lambda r: r["total"])["customer"],
    }
    summary_path = DATA_DIR / "run_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"[4] Wrote summary to {summary_path.name}")
    print(f"\nSummary:\n{json.dumps(summary, indent=2)}")

    # Cleanup demo files
    print("\n[CLEANUP] Removing demo data directory...")
    import shutil
    shutil.rmtree(DATA_DIR)
    print("Done.")
