# Exercise 01 - Intro to Pandas

## Goal
Create a small orders DataFrame and practice:
- Building a DataFrame from Python records
- Creating calculated columns
- Filtering rows
- Producing a simple summary from pandas operations

## Files
- `starter.py`: your template to complete.

## Acceptance Criteria
Your implementation should:
1. Build a DataFrame from `RAW_ORDERS`.
2. Add a `total_amount` column equal to `quantity * unit_price`, rounded to 2 decimals.
3. Return a filtered DataFrame with only orders where `total_amount >= 150`.
4. Build a summary dict with:
   - `row_count`
   - `grand_total`
   - `top_product`
   - `high_value_orders`

## Expected Output (for given sample)
- `row_count = 5`
- `grand_total = 799.91`
- `top_product = 'Monitor 27"'`
- `high_value_orders = 3`
