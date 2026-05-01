# Module 3 – Data Extraction

The "E" in ETL. This module covers the four most common data sources you'll encounter as a data engineer: CSV files, JSON, REST APIs, and relational databases.

## Sample Data

- `data/products.csv` — Product catalog with 15 rows
- `data/transactions.json` — JSON array of 10 financial transactions

## Files

| File | Key Concepts |
|------|-------------|
| `01_extract_from_csv.py` | pandas read_csv, encoding, delimiter, skiprows, dtype hints, chunked reading |
| `02_extract_from_json.py` | json module, pd.read_json, json_normalize for nested data |
| `03_extract_from_api.py` | requests library, GET/POST, headers, pagination, rate limiting, error handling |
| `04_extract_from_database.py` | SQLAlchemy engine, create_engine, pd.read_sql, parameterized queries, SQLite |

## How to Run

```bash
# Offline scripts (no internet required)
python 01_extract_from_csv.py
python 02_extract_from_json.py
python 04_extract_from_database.py

# Requires internet connection
python 03_extract_from_api.py
```

## Notes on API Extraction

`03_extract_from_api.py` uses the free public API at https://jsonplaceholder.typicode.com — no authentication required. The patterns shown (pagination, headers, error handling) apply to any REST API.

## Notes on Database Extraction

`04_extract_from_database.py` creates a local SQLite database file (`module3_sample.db`) so no external database server is needed. All SQLAlchemy patterns demonstrated work identically with PostgreSQL, MySQL, etc. — just change the connection string.
