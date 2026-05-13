# Exercise 01 - Data Types and Collections

## Goal
Clean and summarize a small set of raw sales records while practicing:
- Type conversion (`str` -> `float`)
- Missing value checks
- List/dict usage
- Basic aggregation

## Files
- `starter.py`: your template to complete.
- `solution.py`: one reference implementation.

## Acceptance Criteria
Your implementation should:
1. Keep only valid records (`customer` present, numeric positive `amount`).
2. Return amounts as `float`.
3. Build a summary dict with:
   - `valid_count`
   - `invalid_count`
   - `total_amount`
   - `customers` (sorted unique customer names)
4. Print both cleaned records and summary in `__main__`.

## Expected Output (for given sample)
- `valid_count = 3`
- `invalid_count = 2`
- `total_amount = 525.5`
- `customers = ['Alice', 'Carol', 'Eve']`
