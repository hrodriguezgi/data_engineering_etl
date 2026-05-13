# Exercise 05 - Error Handling and Logging

## Goal
Implement resilient record parsing with exception handling and basic logging.

## Files
- `starter.py`: template to complete.
- `solution.py`: one reference implementation.

## Tasks
1. Implement `safe_parse_amount(value)` with `try/except`.
2. Implement `process_records(records)` to:
   - parse amount
   - separate valid/invalid records
   - collect error reasons
3. Log summary counts using `logging`.

## Acceptance Criteria
- Invalid values should not crash execution.
- Return summary dict with:
  - `valid_count`
  - `invalid_count`
  - `errors` (list of dicts with `id`, `reason`)
- For sample input, expected:
  - `valid_count = 2`
  - `invalid_count = 3`
