# Exercise 04 - Aggregations

## Goal
Create business summaries from the cleaned sales data while practicing:
- `groupby`
- Named aggregations with `agg`
- Sorting summary tables
- Combining count and revenue metrics

## Files
- `starter.py`: your template to complete.

## Tasks
1. Load and clean `sales.csv`.
2. Build a customer summary with:
   - `order_count`
   - `total_revenue`
   - `avg_order_value`
3. Build a region summary with:
   - `order_count`
   - `total_revenue`
   - `avg_items`
4. Sort each summary by `total_revenue` descending.

## Acceptance Criteria
- Top customer is `Dave Brown` with `total_revenue = 2599.98`
- `Alice Johnson` has `order_count = 3`
- Top region is `West` with `total_revenue = 3669.91`
- `Unknown` region has `order_count = 1`
