"""
Module 3 - Lesson 2: Extracting Data from JSON
================================================
JSON (JavaScript Object Notation) is the standard format for web APIs
and many modern data sources. It's more flexible than CSV but can be
more complex to work with, especially when nested.

JSON structures you'll encounter:
  - Array of objects: [{...}, {...}]  — maps directly to a DataFrame
  - Single object with nested arrays: {"data": [{...}], "meta": {...}}
  - Deeply nested: records where fields contain sub-dicts or sub-arrays
  - JSON Lines (JSONL): one JSON object per line

Topics covered:
  - Reading flat JSON with json module and pandas
  - Reading nested JSON with json_normalize
  - Handling JSON from API responses
  - JSON Lines format
  - Writing DataFrames back to JSON
"""

import json
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
SCRIPT_DIR = Path(__file__).parent


# =============================================================================
# 1. READING FLAT JSON (ARRAY OF OBJECTS)
# =============================================================================

print("=" * 60)
print("1. READING FLAT JSON")
print("=" * 60)

transactions_file = DATA_DIR / "transactions.json"

# Method 1: Python's built-in json module → list of dicts → DataFrame
with open(transactions_file, "r", encoding="utf-8") as f:
    transactions_list = json.load(f)   # deserialize JSON → Python list of dicts

print(f"Loaded {len(transactions_list)} transactions from JSON")
print(f"First record: {json.dumps(transactions_list[0], indent=2)}")

# Convert list of dicts to DataFrame
df_txn = pd.DataFrame(transactions_list)
print(f"\nDataFrame from json.load:\n{df_txn}")
print(f"\ndtypes:\n{df_txn.dtypes}")

# Method 2: pd.read_json() — reads directly from file or URL
df_txn2 = pd.read_json(transactions_file)
print(f"\npd.read_json result ({len(df_txn2)} rows):")
print(df_txn2.head(3))

# Parse timestamps
df_txn["timestamp"] = pd.to_datetime(df_txn["timestamp"])
print(f"\nTimestamp dtype: {df_txn['timestamp'].dtype}")
print(f"Date range: {df_txn['timestamp'].min()} to {df_txn['timestamp'].max()}")


# =============================================================================
# 2. READING NESTED JSON
# =============================================================================

print("\n" + "=" * 60)
print("2. NESTED JSON")
print("=" * 60)

# Nested JSON is the most common challenge with API data.
# Example: an API response where each record has sub-objects.

nested_data = [
    {
        "order_id": "ORD-001",
        "date": "2024-01-10",
        "customer": {
            "id": "C001",
            "name": "Alice Johnson",
            "contact": {
                "email": "alice@example.com",
                "phone": "555-1234"
            }
        },
        "shipping": {
            "address": "123 Main St",
            "city": "New York",
            "country": "USA"
        },
        "items": [
            {"product": "Laptop", "qty": 1, "price": 999.99},
            {"product": "Mouse",  "qty": 2, "price": 29.99},
        ],
        "total": 1059.97
    },
    {
        "order_id": "ORD-002",
        "date": "2024-01-12",
        "customer": {
            "id": "C002",
            "name": "Bob Smith",
            "contact": {
                "email": "bob@example.com",
                "phone": "555-5678"
            }
        },
        "shipping": {
            "address": "456 Oak Ave",
            "city": "Chicago",
            "country": "USA"
        },
        "items": [
            {"product": "Monitor", "qty": 1, "price": 449.99},
        ],
        "total": 449.99
    }
]

# Plain pd.DataFrame() won't flatten nested dicts properly
df_naive = pd.DataFrame(nested_data)
print("Naive DataFrame (nested dicts as objects):")
print(df_naive[["order_id", "customer", "total"]])
print(f"customer column type: {type(df_naive['customer'].iloc[0])}")

# json_normalize() — the right tool for flattening nested JSON
# It flattens each level of nesting using a separator in column names

from pandas import json_normalize

# Flatten one level (customer and shipping become flat columns)
df_flat = json_normalize(nested_data)
print(f"\njson_normalize (one level):")
print(f"Columns: {list(df_flat.columns)}")
print(df_flat[["order_id", "customer.name", "customer.contact.email",
               "shipping.city", "total"]].to_string())

# Flatten with custom separator
df_flat_sep = json_normalize(nested_data, sep="_")
print(f"\nColumns with underscore separator: {[c for c in df_flat_sep.columns]}")

# Flatten nested arrays — the 'items' field contains a list
# json_normalize with record_path flattens a nested array
df_items = json_normalize(
    nested_data,
    record_path="items",         # flatten this array field
    meta=["order_id", "date"],   # include these from the parent record
    meta_prefix="order_"         # prefix parent fields to avoid name conflicts
)
print(f"\nFlattened items (one row per item):")
print(df_items)


# =============================================================================
# 3. API RESPONSE STRUCTURE
# =============================================================================

print("\n" + "=" * 60)
print("3. TYPICAL API RESPONSE STRUCTURE")
print("=" * 60)

# Most REST APIs wrap data in a response envelope like this:
api_response = {
    "status": "success",
    "total_count": 3,
    "page": 1,
    "per_page": 10,
    "data": [
        {"id": 1, "name": "Product A", "price": 19.99, "in_stock": True},
        {"id": 2, "name": "Product B", "price": 49.99, "in_stock": True},
        {"id": 3, "name": "Product C", "price": 9.99,  "in_stock": False},
    ]
}

# Extract the 'data' array and convert to DataFrame
records = api_response["data"]
df_api = pd.DataFrame(records)
print(f"Extracted {len(df_api)} records from API response")
print(df_api)

# Check metadata
print(f"\nAPI metadata:")
print(f"  status:      {api_response['status']}")
print(f"  total_count: {api_response['total_count']}")
print(f"  page:        {api_response['page']}")


# =============================================================================
# 4. JSON LINES FORMAT (JSONL)
# =============================================================================

print("\n" + "=" * 60)
print("4. JSON LINES FORMAT (JSONL)")
print("=" * 60)

# JSON Lines: one JSON object per line — common in log files and streaming data
# Each line is a complete, valid JSON object.

# Write JSONL
jsonl_file = SCRIPT_DIR / "demo_events.jsonl"
events = [
    {"event_id": "E001", "type": "page_view", "user": "U001", "ts": "2024-01-10T10:00:00Z"},
    {"event_id": "E002", "type": "click",     "user": "U001", "ts": "2024-01-10T10:01:00Z"},
    {"event_id": "E003", "type": "purchase",  "user": "U002", "ts": "2024-01-10T10:05:00Z"},
    {"event_id": "E004", "type": "page_view", "user": "U003", "ts": "2024-01-10T10:06:00Z"},
]

with open(jsonl_file, "w", encoding="utf-8") as f:
    for event in events:
        f.write(json.dumps(event) + "\n")

print(f"Written {len(events)} events to {jsonl_file.name}")

# Read JSONL — use lines=True with pd.read_json
df_jsonl = pd.read_json(jsonl_file, lines=True)
print(f"\nRead JSONL ({len(df_jsonl)} rows):")
print(df_jsonl)

# Read JSONL manually (line by line) — good for large files
records_manual = []
with open(jsonl_file, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:   # skip empty lines
            records_manual.append(json.loads(line))
df_manual = pd.DataFrame(records_manual)
print(f"\nManually read JSONL: {len(df_manual)} rows")

jsonl_file.unlink(missing_ok=True)


# =============================================================================
# 5. WRITING JSON
# =============================================================================

print("\n" + "=" * 60)
print("5. WRITING JSON")
print("=" * 60)

# DataFrame to JSON
output_file = SCRIPT_DIR / "demo_output.json"

# records orientation: [{col: val, ...}, ...] — most common for data exchange
df_txn_small = df_txn[["transaction_id", "customer_id", "amount", "status"]].head(3)
df_txn_small.to_json(output_file, orient="records", indent=2)
print(f"Written to {output_file.name}:")
print(output_file.read_text())

# Write JSON Lines
jsonl_out = SCRIPT_DIR / "demo_output.jsonl"
df_txn_small.to_json(jsonl_out, orient="records", lines=True)
print(f"\nWritten JSONL ({jsonl_out.name}):")
print(jsonl_out.read_text())

# JSON to a string (for API payloads etc.)
json_string = df_txn_small.to_json(orient="records")
print(f"\nJSON string: {json_string}")

# Clean up
output_file.unlink(missing_ok=True)
jsonl_out.unlink(missing_ok=True)


# =============================================================================
# MAIN DEMO
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("PRACTICAL DEMO: Extract and Analyze Transaction Data")
    print("=" * 60)

    # Load transaction data
    with open(DATA_DIR / "transactions.json") as f:
        raw = json.load(f)

    print(f"\nLoaded {len(raw)} transactions")

    # Convert to DataFrame
    df = pd.DataFrame(raw)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["date"] = df["timestamp"].dt.date

    # Summary stats
    print(f"\nTransaction Summary:")
    print(f"  Total transactions: {len(df)}")
    print(f"  Total amount:       ${df['amount'].sum():,.2f}")
    print(f"  Average amount:     ${df['amount'].mean():,.2f}")

    print(f"\nBy status:")
    status_summary = df.groupby("status")["amount"].agg(count="count", total="sum")
    print(status_summary)

    print(f"\nBy payment method:")
    payment_summary = df.groupby("payment_method")["amount"].agg(count="count", total="sum")
    print(payment_summary.sort_values("total", ascending=False))

    # Export completed transactions as JSONL
    completed = df[df["status"] == "completed"]
    out_file = SCRIPT_DIR / "completed_transactions.jsonl"
    completed.to_json(out_file, orient="records", lines=True, date_format="iso")
    print(f"\nExported {len(completed)} completed transactions to {out_file.name}")
    out_file.unlink(missing_ok=True)
