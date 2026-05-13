# Exercise 03 - Functions for Reusable ETL Logic

## Goal
Build reusable ETL-style functions and compose them into a mini pipeline.

## Files
- `starter.py`: template to complete.

## Tasks
1. Implement `extract_active(records)` to keep only active records.
2. Implement `transform_amount(records, tax_rate=0.08)` to:
   - cast `amount` to float
   - add `amount_with_tax`
3. Implement `load_summary(records)` to return:
   - `count`
   - `total_amount`
   - `total_amount_with_tax`

## Acceptance Criteria
- Pipeline should be run through `run_pipeline(records)`.
- Invalid numeric amounts are skipped during transform.
- For the provided sample, expected output:
  - `count = 2`
  - `total_amount = 425.5`
  - `total_amount_with_tax = 459.54`
