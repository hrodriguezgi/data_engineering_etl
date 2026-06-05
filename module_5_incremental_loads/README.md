# Module 5 – Incremental Load Patterns

Full-load ETL — reading all source data on every run — is expensive and slow at scale. This module teaches the foundational patterns every data engineer needs to build pipelines that process only what has changed.

---

## Learning Objectives

By the end of this module you will be able to:

- Implement watermark-based incremental extraction using a persistent state table
- Choose the right upsert strategy (INSERT OR IGNORE, INSERT OR REPLACE, or Staged MERGE) for a given use case
- Design Slowly Changing Dimension (SCD) Type 1 and Type 2 tables and apply changes correctly
- Build a full incremental pipeline with audit logging and a safe, restartable watermark

---

## Files

| File | Topics |
|------|--------|
| `01_watermark_based_extraction.py` | `pipeline_state` table, first run vs. incremental run, lookback buffer, simulating new source data |
| `02_upsert_patterns.py` | INSERT OR IGNORE, INSERT OR REPLACE, Staged MERGE, idempotency proof for all three strategies |
| `03_scd_type1_type2.py` | SCD Type 1 (overwrite), SCD Type 2 (`valid_from`/`valid_to`/`is_current`), point-in-time queries |
| `04_incremental_pipeline.py` | End-to-end pipeline: watermark extract → transform → staged merge load → watermark update → audit log |

## Data

| File | Description |
|------|-------------|
| `data/source_orders.csv` | 50 sample orders with `order_id`, `customer_id`, `product`, `amount`, `status`, `created_at`, `updated_at` |

---

## How to Run

```bash
# From the module_5_incremental_loads directory

# Lesson 1: Watermark extraction demo (creates watermark_demo.db)
python 01_watermark_based_extraction.py

# Lesson 2: Upsert patterns comparison (creates upsert_demo.db)
python 02_upsert_patterns.py

# Lesson 3: SCD Type 1 and Type 2 (creates scd_demo.db)
python 03_scd_type1_type2.py

# Lesson 4: Full incremental pipeline (creates incremental_pipeline.db)
python 04_incremental_pipeline.py
```

Each script is self-contained and creates its own SQLite database. The database files are regenerated on each run (clean slate for demos).

---

## Key Concepts

### Watermark-Based Extraction

```
last_watermark = SELECT watermark_val FROM pipeline_state WHERE pipeline_name = '...'

Extract:  SELECT * FROM source WHERE updated_at > last_watermark
Update:   UPDATE pipeline_state SET watermark_val = MAX(updated_at from batch)
```

A **lookback buffer** (e.g., 5 seconds) is subtracted from the watermark before querying to catch rows that arrived slightly late due to clock skew between source systems.

### Upsert Strategy Comparison

| Strategy | Handles Updates | Partial Column Update | Complexity | Best For |
|---|---|---|---|---|
| INSERT OR IGNORE | No | N/A | Low | Append-only event logs |
| INSERT OR REPLACE | Yes | No (full row) | Low | Simple dimension mirroring |
| Staged MERGE | Yes | Yes | Medium | Production fact/dimension tables |

### SCD Type 2 Timeline

```
customer_id  loyalty_tier  valid_from   valid_to     is_current
C001         bronze        2024-01-01   2024-02-28   0
C001         gold          2024-03-01   9999-12-31   1
```

The rule: **never delete history rows**. Close the old row by setting `valid_to`, then insert a new current row.

### Restartable Watermark

The watermark is only updated **after** a successful load. If the pipeline fails mid-run, the watermark stays at its previous value and the next run will re-process the same batch automatically.

---

## Incremental Load Patterns Summary

| Pattern | Use When |
|---|---|
| Watermark (timestamp) | Source has a reliable `updated_at` column |
| Watermark (ID-based) | Source uses auto-increment IDs and rows are append-only |
| Full refresh | Small dimension tables where incremental complexity isn't worth it |
| SCD Type 1 | Attribute corrections (typos, data quality fixes) |
| SCD Type 2 | Attributes that drive historical analysis (tier, location, category) |
