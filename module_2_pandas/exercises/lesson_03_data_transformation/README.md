# Exercise 03 - Data Transformation

## Goal
Transform the cleaned sales dataset while practicing:
- Derived columns
- `pd.cut` for binning
- Date extraction
- `pivot_table`

## Files
- `starter.py`: your template to complete.

## Tasks
1. Load and clean `sales.csv`.
2. Add:
   - `order_month` from the `date` column in `YYYY-MM` format
   - `size_band` based on `total_amount`
3. Build a pivot table with `region` as rows, `category` as columns, and revenue as values.
4. Build a monthly revenue summary.

## Acceptance Criteria
- `size_band_counts = {'small': 6, 'medium': 6, 'large': 6, 'enterprise': 1}`
- `monthly_revenue = {'2024-01': 9449.72, '2024-02': 1519.93}`
- Pivot table includes:
  - `West / Electronics = 2969.93`
  - `South / Furniture = 1019.98`
