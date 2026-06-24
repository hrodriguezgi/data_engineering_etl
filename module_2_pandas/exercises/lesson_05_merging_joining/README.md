# Exercise 05 - Merging and Joining

## Goal
Combine sales data with the customer reference table while practicing:
- `merge`
- Left joins
- The `_merge` indicator column
- Aggregation after joining

## Files
- `starter.py`: your template to complete.

## Tasks
1. Load and clean `sales.csv`.
2. Load `customers.csv`.
3. Left join sales with customers using customer name.
4. Keep the `_merge` indicator to identify unmatched orders.
5. Build:
   - a DataFrame of unmatched orders
   - a country revenue summary for matched rows only

## Acceptance Criteria
- Joined DataFrame keeps `19` rows.
- `unmatched_count = 6`
- Unmatched customers are:
  - `Karen Martinez`
  - `Liam Anderson`
  - `Mia Thompson`
  - `Anonymous`
  - `Noah Garcia`
  - `Olivia Robinson`
- In the country summary:
  - `Canada = 2599.98`
  - `USA = 2599.90`
