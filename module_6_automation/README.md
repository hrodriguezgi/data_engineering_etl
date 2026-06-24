# Module 5 – Automation

Production data pipelines don't run manually — they're scheduled, monitored, and self-healing. This module covers the tools and patterns to automate your ETL workflows.

## Files

| File | Key Concepts |
|------|-------------|
| `01_scheduling_with_schedule.py` | `schedule` library, job intervals, cron-style timing, daemon loop, graceful shutdown |
| `02_etl_with_logging.py` | Python `logging` module, log levels, FileHandler + StreamHandler, ETL metrics |
| `03_etl_orchestration.py` | Orchestrator class, step dependencies, retry logic, status tracking, run reports |
| `04_config_driven_etl.py` | JSON configuration files, dynamic pipeline construction, environment overrides |

## Config

- `config/pipeline_config.json` — Sample pipeline configuration file used by `04_config_driven_etl.py`

## How to Run

```bash
# From the module_5_automation directory

# Orchestration demo (runs immediately, no scheduling)
python 03_etl_orchestration.py

# Config-driven pipeline (reads pipeline_config.json)
python 04_config_driven_etl.py

# Logging demo
python 02_etl_with_logging.py

# Scheduler demo (runs in a loop — Ctrl+C to stop)
python 01_scheduling_with_schedule.py
```

## Automation Patterns

| Pattern | Use Case |
|---------|---------|
| **Scheduling** | Run pipelines at fixed times (hourly, daily, etc.) |
| **Orchestration** | Manage dependencies between pipeline steps |
| **Retry logic** | Automatically recover from transient failures |
| **Config-driven** | Reuse pipeline code with different data sources/targets |
| **Structured logging** | Make pipeline behavior observable and debuggable |
