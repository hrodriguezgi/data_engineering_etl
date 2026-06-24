# Exercise 02 - Data Cleaning

## Goal
Clean the raw sales dataset while practicing:
- `read_csv`
- Missing value handling with `fillna`
- Duplicate removal
- Type conversion with `pd.to_numeric`
- Basic quality reporting

## Files
- `starter.py`: your template to complete.

## Tasks
1. Load `module_2_pandas/data/sales.csv`.
2. Remove duplicate `order_id` rows, keeping the first occurrence.
3. Fill missing values as follows:
   - `quantity` -> `1`
   - `unit_price` -> median unit price
   - `customer_name` -> `"Anonymous"`
   - `region` -> `"Unknown"`
4. Convert `quantity` to integer.
5. Add `total_amount = quantity * unit_price`.
6. Build a quality report.

## Acceptance Criteria
- Cleaned DataFrame has `19` rows.
- `quantity`, `unit_price`, `customer_name`, and `region` contain no nulls.
- `anonymous_customers = 1`
- `unknown_regions = 1`
- `grand_total = 10969.65`
