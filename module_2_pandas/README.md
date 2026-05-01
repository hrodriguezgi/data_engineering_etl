# Module 2 – Pandas for Data Engineering

Pandas is the cornerstone of data engineering in Python. This module covers everything you need to load, inspect, clean, transform, aggregate, and join datasets.

## Sample Data

- `data/sales.csv` — 20-row sales dataset with intentional nulls/duplicates for cleaning exercises
- `data/customers.csv` — 10-row customer reference table for join exercises

## Files

| File | Key Concepts |
|------|-------------|
| `01_intro_to_pandas.py` | Series, DataFrame creation, read_csv/read_json, info/describe, head/tail, shape, dtypes |
| `02_data_cleaning.py` | isnull/fillna/dropna, duplicates, type casting, str accessor, rename columns |
| `03_data_transformation.py` | apply/map, vectorized ops, pd.cut (binning), pivot_table, melt, stack/unstack |
| `04_aggregations.py` | groupby, agg, named aggregations, rolling windows, cumsum/cumprod |
| `05_merging_joining.py` | merge (inner/left/right/outer), join, concat (axis 0 and 1), indicator column |

## How to Run

```bash
# From the module_2_pandas directory
python 01_intro_to_pandas.py
python 02_data_cleaning.py
# ... etc.
```

## Key Pandas Concepts for Data Engineering

1. **DataFrames are your primary data container** — think of them as in-memory tables.
2. **Vectorized operations are fast** — avoid Python loops over rows; use pandas built-ins.
3. **Method chaining** keeps transformation code readable.
4. **Always check dtypes** — wrong types are a common source of bugs.
