# Exercise: Lesson 01 - Building an Idempotent Pipeline

## Objective

Build an ETL pipeline that can be safely re-run multiple times and produce the same result. This is critical for production pipelines that need to recover from failures.

## Scenario

You're building a customer data pipeline. The source contains customer records (id, name, email, signup_date). Your pipeline reads from a CSV, cleans the data, and loads it to a destination.

**Data source:** `customers.csv` (provided below as test data)
**Destination:** An in-memory dictionary representing a database table

## Requirements

1. **Extract Phase**
   - Read the CSV without modifying the source
   - Return all rows as-is (no transformation)

2. **Transform Phase**
   - Clean email addresses (lowercase, strip whitespace)
   - Parse dates (YYYY-MM-DD format)
   - Remove records with missing required fields (id, email)
   - Return (valid_records, rejected_records)

3. **Load Phase (IDEMPOTENT)**
   - Implement UPSERT by customer id
   - First run: inserts new records
   - Second run with same data: updates instead of inserting (no duplicates!)
   - Return stats: {inserted, updated}

4. **Test Idempotency**
   - Run the pipeline twice with the same data
   - Verify that the destination state is identical after both runs
   - Show that running twice doesn't double the record count

## Success Criteria

✅ Extract preserves original data (no mutations)
✅ Transform removes invalid records with clear reasons
✅ Load is idempotent (running twice = same state)
✅ Statistics show insert/update counts correctly
✅ Edge cases handled: missing emails, invalid dates, duplicate IDs

## Test Data

```csv
id,name,email,signup_date
1,Alice Johnson,alice@example.com,2023-01-15
2,Bob Smith,  BOB@EXAMPLE.COM  ,2023-02-20
3,Carol White,carol@example.com,invalid-date
4,,dave@example.com,2023-04-10
5,Eve Davis,eve@example.com,2023-05-12
```

## Hints

- Use a dictionary to represent your destination (db_state = {})
- Key by customer id
- In transform, use try/except for date parsing
- For idempotency, check if id exists in destination before inserting
