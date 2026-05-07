# Data Engineering ETL Course

A hands-on, practical course covering data engineering fundamentals through building real ETL (Extract, Transform, Load) pipelines with Python.

---

## 📚 Course Overview

This course takes you from Python fundamentals to building automated, production-style ETL pipelines. Each module builds on the previous one, culminating in a fully automated, config-driven ETL system.

---

## 🚀 Quick Start

### Prerequisites
- Anaconda (Conda)
- `uv` package manager

### Installation

```bash
# Clone the repository
git clone https://github.com/hrodriguezgi/data_engineering_etl.git
cd data_engineering_etl

# Create Conda environment
conda create -n etl-course python=3.10 -y
conda activate etl-course

# Initialize and install dependencies with uv
uv init
uv add -r requirements.txt
uv sync
```

### Verify Installation

```bash
uv run pytest -q
uv run python -c "import pandas, requests, sqlalchemy, schedule; print('All dependencies installed!')"
```

For full setup and troubleshooting, see [docs/ENVIRONMENT_SETUP.md](docs/ENVIRONMENT_SETUP.md).

---

## 📂 Repository Structure

```
data_engineering_etl/
├── README.md
├── requirements.txt
├── module_1_python_fundamentals/
│   ├── README.md
│   ├── 01_variables_and_data_types.py
│   ├── 02_control_flow.py
│   ├── 03_functions.py
│   ├── 04_file_handling.py
│   └── 05_error_handling.py
├── module_2_pandas/
│   ├── README.md
│   ├── data/
│   │   ├── sales.csv
│   │   └── customers.csv
│   ├── 01_intro_to_pandas.py
│   ├── 02_data_cleaning.py
│   ├── 03_data_transformation.py
│   ├── 04_aggregations.py
│   └── 05_merging_joining.py
├── module_3_data_extraction/
│   ├── README.md
│   ├── data/
│   │   ├── products.csv
│   │   └── transactions.json
│   ├── 01_extract_from_csv.py
│   ├── 02_extract_from_json.py
│   ├── 03_extract_from_api.py
│   └── 04_extract_from_database.py
├── module_4_etl_pipelines/
│   ├── README.md
│   ├── data/
│   │   └── raw_sales.csv
│   ├── 01_etl_design_principles.py
│   ├── 02_simple_etl_pipeline.py
│   ├── 03_etl_with_transformations.py
│   └── 04_etl_with_validation.py
├── module_5_automation/
│   ├── README.md
│   ├── config/
│   │   └── pipeline_config.json
│   ├── 01_scheduling_with_schedule.py
│   ├── 02_etl_with_logging.py
│   ├── 03_etl_orchestration.py
│   └── 04_config_driven_etl.py
└── tests/
    ├── __init__.py
    ├── test_module_2_pandas.py
    ├── test_module_3_extraction.py
    ├── test_module_4_etl.py
    └── test_module_5_automation.py
```

---

## 📖 Modules

### Module 1 – Python Fundamentals
**Goal:** Build a solid foundation in Python before diving into data engineering.

| File | Topics |
|------|--------|
| `01_variables_and_data_types.py` | Variables, strings, numbers, booleans, lists, dicts, tuples, sets, type conversion |
| `02_control_flow.py` | if/elif/else, for/while loops, comprehensions, break/continue |
| `03_functions.py` | def, args, kwargs, default params, lambda, map/filter, decorators, generators |
| `04_file_handling.py` | Reading/writing text, CSV, JSON; context managers |
| `05_error_handling.py` | try/except/finally, custom exceptions, logging |

**Run:**
```bash
cd module_1_python_fundamentals
python 01_variables_and_data_types.py
python 02_control_flow.py
# ... etc.
```

---

### Module 2 – Pandas for Data Engineering
**Goal:** Master pandas for data manipulation—the most-used tool in any data engineer's toolkit.

| File | Topics |
|------|--------|
| `01_intro_to_pandas.py` | Series, DataFrame, read_csv/read_json, info, describe, head/tail |
| `02_data_cleaning.py` | Null handling, duplicates, type conversion, string ops, renaming |
| `03_data_transformation.py` | apply/map, vectorized ops, binning, pivot tables, melt/stack |
| `04_aggregations.py` | groupby, agg, rolling windows, cumulative ops |
| `05_merging_joining.py` | merge, join, concat, inner/left/right/outer joins |

**Run:**
```bash
cd module_2_pandas
python 01_intro_to_pandas.py
```

---

### Module 3 – Data Extraction
**Goal:** Learn how to pull data from every common source a data engineer encounters.

| File | Topics |
|------|--------|
| `01_extract_from_csv.py` | Encodings, delimiters, skip rows, chunked reading |
| `02_extract_from_json.py` | Flat JSON, nested JSON, JSON normalization |
| `03_extract_from_api.py` | REST APIs, pagination, auth headers, rate limiting |
| `04_extract_from_database.py` | SQLAlchemy, SQLite, read_sql, parameterized queries |

**Run:**
```bash
cd module_3_data_extraction
python 01_extract_from_csv.py
python 03_extract_from_api.py   # requires internet connection
```

---

### Module 4 – ETL Pipelines
**Goal:** Build structured, maintainable ETL pipelines from scratch.

| File | Topics |
|------|--------|
| `01_etl_design_principles.py` | ETL phases, design patterns, idempotency, best practices |
| `02_simple_etl_pipeline.py` | End-to-end: CSV to transform to SQLite |
| `03_etl_with_transformations.py` | Normalization, enrichment, aggregation, derived columns |
| `04_etl_with_validation.py` | Schema validation, business rules, quality reports |

**Run:**
```bash
cd module_4_etl_pipelines
python 02_simple_etl_pipeline.py
```

---

### Module 5 – Automation
**Goal:** Make pipelines production-ready with scheduling, logging, orchestration, and configuration.

| File | Topics |
|------|--------|
| `01_scheduling_with_schedule.py` | schedule library, cron-style jobs, daemon loops |
| `02_etl_with_logging.py` | Log levels, file + console handlers, structured ETL metrics |
| `03_etl_orchestration.py` | Orchestrator class, step management, retries, status reporting |
| `04_config_driven_etl.py` | JSON config, dynamic pipeline construction, reusable templates |

**Run:**
```bash
cd module_5_automation
python 03_etl_orchestration.py
python 04_config_driven_etl.py
```

---

## 🧪 Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run a specific module's tests
pytest tests/test_module_2_pandas.py -v

# Run with coverage (if pytest-cov is installed)
pytest tests/ --cov=. -v
```

---

## 🛠️ Key Dependencies

| Package | Purpose |
|---------|---------|
| pandas | Data manipulation and analysis |
| requests | HTTP requests for API extraction |
| sqlalchemy | Database abstraction layer |
| schedule | Job scheduling |
| python-dotenv | Environment variable management |
| pytest | Testing framework |
| openpyxl | Excel file support for pandas |
| faker | Generating realistic fake data |

---

## 🎯 Learning Path

Complete each module in order. Each lesson file can be run independently—read the code, run it, modify it, and experiment.

Module 1 (Python Basics) -> Module 2 (Pandas) -> Module 3 (Data Extraction) -> Module 4 (ETL Pipelines) -> Module 5 (Automation)

---

## 💡 Tips

1. **Read the code comments** — every concept is explained inline.
2. **Experiment** — modify the examples and observe the output.
3. **Check the tests** — they show expected behavior and edge cases.
4. **Use `python -i script.py`** to run a script and stay in an interactive session to inspect variables.

---

## 📝 License

MIT License — free to use for learning and teaching.
