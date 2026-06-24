# Exercise: Lesson 02 - Build an End-to-End ETL Pipeline

## Objective

Build a complete, working ETL pipeline from raw CSV data to a SQLite database. Handle the messiness of real data gracefully.

## Scenario

You're processing a log file from a web service. Each line contains:
- request_id (integer, required)
- timestamp (ISO 8601 datetime, required)
- endpoint (string, required)
- status_code (integer, 200-500)
- response_time_ms (float, milliseconds)
- user_id (string, optional)

**Challenges in the data:**
- Some timestamps are invalid or missing
- Status codes outside the normal range (e.g., -1, 999)
- Response times are occasionally negative (measurement errors)
- Some request_ids are duplicated
- Missing user_ids (should default to "UNKNOWN")

**Output:** A clean SQLite database with:
- `logs` table: valid records
- `logs_rejected` table: rejected records with rejection reasons

## Requirements

1. **Extract Phase**
   - Read CSV file with all columns as strings
   - Don't auto-convert anything

2. **Transform Phase**
   - Parse types carefully (integers, floats, dates)
   - Reject records with missing required fields
   - Reject records with invalid status codes (must be 200-599)
   - Reject records with negative response times
   - Fill missing user_ids with "UNKNOWN"
   - Add a derived field: `response_time_bucket` ("fast" <100ms, "medium" <500ms, "slow")

3. **Load Phase**
   - Write clean records to `logs` table
   - Write rejected records to `logs_rejected` table (with _rejection_reason)
   - Use idempotent loading (truncate and reload)

## Success Criteria

✅ Extracts raw data without type assumptions
✅ Transforms with explicit error handling
✅ Rejects invalid records with clear reasons
✅ Loads to both valid and rejection tables
✅ Handles edge cases (negative times, invalid status codes, missing fields)

## Hints

- Use `pd.read_csv(dtype=str)` to avoid silent type conversions
- Use `pd.to_numeric(errors='coerce')` and check for NaN to detect parse failures
- Track rejection reasons for each record
- Test idempotency by running the pipeline twice

## Testing

You can use the sample data provided or create your own `sample_logs.csv`.
