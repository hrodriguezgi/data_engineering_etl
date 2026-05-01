# Module 4 – ETL Pipelines

This module is where everything comes together. You'll build progressively more sophisticated ETL pipelines, learning design patterns that scale to production systems.

## Sample Data

- `data/raw_sales.csv` — Raw sales data with intentional quality issues (missing values, wrong types, outliers) for realistic pipeline exercises

## Files

| File | Key Concepts |
|------|-------------|
| `01_etl_design_principles.py` | ETL vs ELT, extract/transform/load phases, idempotency, lineage, best practices |
| `02_simple_etl_pipeline.py` | Full end-to-end pipeline: CSV → clean/filter/calculate → SQLite |
| `03_etl_with_transformations.py` | Normalization, enrichment (lookups), aggregation, derived/calculated columns |
| `04_etl_with_validation.py` | Schema validation, business rules, null checks, range checks, quality report |

## How to Run

```bash
# From the module_4_etl_pipelines directory
python 01_etl_design_principles.py   # conceptual demo, no external data needed
python 02_simple_etl_pipeline.py     # creates etl_output.db
python 03_etl_with_transformations.py
python 04_etl_with_validation.py
```

## ETL Design Principles Summary

| Principle | Why It Matters |
|-----------|---------------|
| **Idempotency** | Running the pipeline twice should produce the same result |
| **Separation of concerns** | Extract, Transform, and Load are distinct phases with clear interfaces |
| **Fail fast** | Validate data as early as possible in the pipeline |
| **Observability** | Log metrics at every stage so you can debug failures |
| **Incremental loading** | Process only new/changed data where possible to save time and resources |
