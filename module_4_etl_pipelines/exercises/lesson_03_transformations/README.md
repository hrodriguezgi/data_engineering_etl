# Exercise: Lesson 03 - Data Transformations (Enrichment & Derived Columns)

## Objective

Build a data enrichment pipeline that joins transaction data with reference data and creates meaningful derived metrics.

## Scenario

You have transaction data (amount, timestamp, product_id) and reference data for products (id, category, tax_rate).
You need to:
- Enrich transactions with product info
- Compute derived financial metrics (tax, total, margin)
- Create time-based groupings

## Requirements

1. **Normalize** - Consistent formatting
   - Uppercase product_ids
   - Round amounts to 2 decimals
   - Parse timestamps

2. **Enrich** - Join with reference data
   - Add product category via lookup
   - Add tax_rate via lookup
   - Handle missing products (default to "UNKNOWN" category)

3. **Derive** - Calculated fields
   - tax_amount = amount * tax_rate
   - total_with_tax = amount + tax_amount
   - margin_pct = based on category (example: Electronics=15%, Clothing=40%)
   - profit = amount * margin_pct
   - hour_of_day = from timestamp

4. **Aggregate** - Summary tables
   - By product category: count, total_amount, total_profit
   - By hour of day: count, avg_transaction

## Success Criteria

✅ Lookup joins handle missing keys gracefully
✅ Derived columns computed correctly
✅ Aggregations produce expected summaries
✅ Edge cases: missing products, null amounts, timezone handling

## Sample Data

Products reference:
```
product_id,category,tax_rate
P001,Electronics,0.08
P002,Clothing,0.05
P003,Food,0.02
```

Transactions:
```
transaction_id,product_id,amount,timestamp
T1,P001,999.99,2024-01-15T09:00:00Z
T2,P002,49.99,2024-01-15T10:30:00Z
T3,UNKNOWN,25.00,2024-01-15T14:00:00Z
T4,P001,1299.99,2024-01-15T16:45:00Z
T5,,59.99,2024-01-15T18:00:00Z
```
