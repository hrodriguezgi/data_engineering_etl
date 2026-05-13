# Exercise 04 - File Handling (CSV + JSON)

## Goal
Practice reading and writing files for a small ETL-like workflow.

## Files
- `starter.py`: template to complete.

## Tasks
1. Read `sales_input.csv` from the same folder.
2. Compute a `total = quantity * unit_price` field per row.
3. Write transformed rows to `sales_output.csv`.
4. Write run summary to `run_summary.json` with:
   - `rows_processed`
   - `grand_total`

## Acceptance Criteria
- Use `with open(...)` context managers.
- Parse numeric fields correctly.
- For sample input, expected:
  - `rows_processed = 3`
  - `grand_total = 1369.96`
