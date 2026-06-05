"""
Module 6 - Lesson 4: Config-Driven ETL Pipelines
==================================================
Hard-coding pipeline parameters (file paths, table names, filter thresholds)
makes pipelines brittle and non-reusable. Config-driven pipelines separate
CODE (what to do) from CONFIGURATION (what data to process and where).

Benefits:
  - Run the same pipeline code against different data sources
  - Change behavior without modifying source code
  - Store configs in version control (track changes)
  - Different configs for dev/staging/production environments

Topics covered:
  - Loading pipeline config from JSON
  - Validating config structure
  - Building a pipeline dynamically from config
  - Environment variable overrides (12-factor app pattern)
  - Merging configs for different environments
  - Config schema documentation
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy import create_engine

MODULE_DIR = Path(__file__).parent
CONFIG_DIR = MODULE_DIR / "config"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("etl.config_driven")


# =============================================================================
# 1. LOADING AND VALIDATING CONFIG
# =============================================================================

print("=" * 60)
print("1. LOADING CONFIGURATION")
print("=" * 60)

def load_config(config_path: Path) -> Dict[str, Any]:
    """
    Load and validate a pipeline configuration from a JSON file.

    Args:
        config_path: Path to the JSON configuration file.

    Returns:
        Validated configuration dict.

    Raises:
        FileNotFoundError: If the config file doesn't exist.
        ValueError: If required config keys are missing.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Validate required top-level keys
    required_keys = ["pipeline_name", "source", "destination", "transformations"]
    missing = [k for k in required_keys if k not in config]
    if missing:
        raise ValueError(f"Config missing required keys: {missing}")

    # Validate source config
    if "type" not in config["source"]:
        raise ValueError("Config 'source' must have a 'type' field")
    if "path" not in config["source"] and config["source"]["type"] in ("csv", "json"):
        raise ValueError("Config 'source' must have a 'path' field for CSV/JSON sources")

    # Validate destination config
    if "type" not in config["destination"]:
        raise ValueError("Config 'destination' must have a 'type' field")

    logger.info(f"Config loaded: {config['pipeline_name']} v{config.get('version', '?')}")
    return config

config = load_config(CONFIG_DIR / "pipeline_config.json")
print(f"Pipeline name: {config['pipeline_name']}")
print(f"Version:       {config.get('version', 'N/A')}")
print(f"Description:   {config.get('description', '')}")
print(f"Source type:   {config['source']['type']}")
print(f"Destination:   {config['destination']['database']}.{config['destination']['table']}")


# =============================================================================
# 2. ENVIRONMENT VARIABLE OVERRIDES
# =============================================================================

print("\n" + "=" * 60)
print("2. ENVIRONMENT VARIABLE OVERRIDES")
print("=" * 60)

def apply_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Override config values from environment variables.

    This follows the 12-factor app pattern: config from environment.
    Environment variables take precedence over file config.

    Convention: ETL_<KEY> overrides the top-level config key.
    Examples:
      ETL_SOURCE_PATH=/data/production/sales.csv  → config['source']['path']
      ETL_DESTINATION_DB=/db/prod.db              → config['destination']['database']
      ETL_LOG_LEVEL=DEBUG                         → config['logging']['level']

    Args:
        config: Base config dict loaded from file.

    Returns:
        Config with environment variable overrides applied.
    """
    import copy
    config = copy.deepcopy(config)

    overrides = {
        "ETL_PIPELINE_NAME": ("pipeline_name",),
        "ETL_SOURCE_PATH":   ("source", "path"),
        "ETL_SOURCE_ENCODING": ("source", "encoding"),
        "ETL_DEST_DB":       ("destination", "database"),
        "ETL_DEST_TABLE":    ("destination", "table"),
        "ETL_LOG_LEVEL":     ("logging", "level"),
    }

    applied = []
    for env_var, key_path in overrides.items():
        value = os.environ.get(env_var)
        if value is not None:
            # Navigate to the parent dict and set the value
            target = config
            for key in key_path[:-1]:
                target = target.setdefault(key, {})
            target[key_path[-1]] = value
            applied.append(f"{env_var}={value!r}")

    if applied:
        logger.info(f"Applied env overrides: {applied}")
    else:
        logger.debug("No environment variable overrides found")

    return config

# Apply overrides (in normal execution, these won't exist)
config = apply_env_overrides(config)
print(f"Source path (after env override check): {config['source']['path']}")

# Simulate setting an override
os.environ["ETL_LOG_LEVEL"] = "DEBUG"
config_with_override = apply_env_overrides(config)
print(f"Log level after ETL_LOG_LEVEL override: {config_with_override.get('logging', {}).get('level')}")
del os.environ["ETL_LOG_LEVEL"]


# =============================================================================
# 3. MERGING ENVIRONMENT-SPECIFIC CONFIGS
# =============================================================================

print("\n" + "=" * 60)
print("3. ENVIRONMENT-SPECIFIC CONFIG MERGING")
print("=" * 60)

# A common pattern: a base config with environment-specific overrides
# base_config.json   → common settings
# dev_config.json    → development overrides (local paths, debug logging)
# prod_config.json   → production overrides (real DB, warnings only)

def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep-merge multiple config dicts. Later configs override earlier ones.

    Args:
        *configs: Config dicts to merge, in order of increasing precedence.

    Returns:
        Merged config dict.
    """
    import copy

    def deep_merge(base: Dict, override: Dict) -> Dict:
        result = copy.deepcopy(base)
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)  # recurse
            else:
                result[key] = copy.deepcopy(value)
        return result

    result = {}
    for cfg in configs:
        result = deep_merge(result, cfg)
    return result

# Demo: merge base + environment-specific config
base_config = {
    "pipeline_name": "sales_etl",
    "source": {"type": "csv", "path": "data/sales.csv", "encoding": "utf-8"},
    "destination": {"type": "sqlite", "database": "output.db", "table": "sales"},
    "logging": {"level": "INFO"},
    "validation": {"enabled": True, "fail_on_error_rate_above": 0.1},
}

dev_overrides = {
    "source": {"path": "data/dev_sales.csv"},  # only override path
    "destination": {"database": "dev_output.db"},
    "logging": {"level": "DEBUG"},
}

prod_overrides = {
    "source": {"path": "/var/data/prod/sales.csv"},
    "destination": {"database": "/var/db/production.db"},
    "logging": {"level": "WARNING"},
    "validation": {"fail_on_error_rate_above": 0.05},  # stricter in prod
}

dev_config = merge_configs(base_config, dev_overrides)
prod_config = merge_configs(base_config, prod_overrides)

print(f"Dev  source path: {dev_config['source']['path']}")
print(f"Prod source path: {prod_config['source']['path']}")
print(f"Dev  log level:   {dev_config['logging']['level']}")
print(f"Prod log level:   {prod_config['logging']['level']}")
print(f"Dev  error rate:  {dev_config['validation']['fail_on_error_rate_above']}")
print(f"Prod error rate:  {prod_config['validation']['fail_on_error_rate_above']}")


# =============================================================================
# 4. BUILDING AN ETL PIPELINE FROM CONFIG
# =============================================================================

print("\n" + "=" * 60)
print("4. CONFIG-DRIVEN PIPELINE EXECUTION")
print("=" * 60)

class ConfigDrivenPipeline:
    """
    An ETL pipeline whose behavior is fully defined by a configuration dict.

    The config specifies:
      - Source type and location
      - List of transformation steps (in order)
      - Validation rules
      - Destination type and table
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config["pipeline_name"]
        self._df: Optional[pd.DataFrame] = None
        self._rejected: Optional[pd.DataFrame] = None

    # ---- EXTRACT ----

    def extract(self) -> pd.DataFrame:
        """Extract data based on source config."""
        src = self.config["source"]
        src_type = src["type"]
        logger.info(f"[EXTRACT] type={src_type}, path={src.get('path')}")

        if src_type == "csv":
            path = Path(src["path"])
            if not path.is_absolute():
                # Resolve relative to the repo root
                path = Path(__file__).parent.parent / path

            df = pd.read_csv(
                path,
                encoding=src.get("encoding", "utf-8"),
                sep=src.get("delimiter", ","),
                dtype=src.get("dtype_overrides"),
                na_values=src.get("null_values"),
                keep_default_na=True,
            )
        elif src_type == "json":
            path = Path(src["path"])
            if not path.is_absolute():
                path = Path(__file__).parent.parent / path
            df = pd.read_json(path)
        else:
            raise ValueError(f"Unsupported source type: {src_type}")

        logger.info(f"[EXTRACT] {len(df)} rows, {df.shape[1]} columns")
        return df

    # ---- TRANSFORM ----

    def apply_transformations(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply each transformation step defined in config."""
        steps = self.config.get("transformations", [])
        logger.info(f"[TRANSFORM] Applying {len(steps)} transformation steps")

        for step in steps:
            step_type = step["step"]
            logger.debug(f"  Applying step: {step_type} — {step.get('description', '')}")

            if step_type == "parse_types":
                for col, opts in step.get("columns", {}).items():
                    if col not in df.columns:
                        continue
                    dtype = opts.get("type")
                    default = opts.get("default")
                    on_error = opts.get("on_error", "coerce")
                    if dtype in ("int", "float"):
                        df[col] = pd.to_numeric(df[col], errors=on_error)
                        if default is not None:
                            df[col] = df[col].fillna(default)
                        if dtype == "int":
                            df[col] = df[col].fillna(0).astype(int)

            elif step_type == "parse_dates":
                fmt = step.get("format")
                for col in step.get("columns", []):
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col], format=fmt, errors="coerce")

            elif step_type == "fill_nulls":
                for col, value in step.get("fills", {}).items():
                    if col in df.columns:
                        df[col] = df[col].fillna(value)

            elif step_type == "filter":
                initial = len(df)
                for rule in step.get("rules", []):
                    col = rule["column"]
                    op = rule["operator"]
                    val = rule["value"]
                    if col not in df.columns:
                        continue
                    numeric_col = pd.to_numeric(df[col], errors="coerce")
                    if op == "gt":
                        df = df[numeric_col > val]
                    elif op == "lt":
                        df = df[numeric_col < val]
                    elif op == "eq":
                        df = df[df[col] == val]
                    elif op == "ne":
                        df = df[df[col] != val]
                logger.info(f"  Filter: {initial} → {len(df)} rows")

            elif step_type == "derive":
                # Evaluate simple column expressions
                for col, expr in step.get("columns", {}).items():
                    try:
                        if "." in expr and not expr.startswith("\""):
                            # Date attribute access: "sale_date.year"
                            parts = expr.split(".")
                            src_col = parts[0]
                            attr = parts[1]
                            if src_col in df.columns:
                                df[col] = getattr(df[src_col].dt, attr, None)
                        else:
                            # Arithmetic expression
                            df[col] = df.eval(expr)
                    except Exception as e:
                        logger.warning(f"  Could not compute derived column '{col}': {e}")

            else:
                logger.warning(f"  Unknown transformation step type: {step_type}")

        logger.info(f"[TRANSFORM] Complete: {len(df)} rows")
        return df

    # ---- LOAD ----

    def load(self, df: pd.DataFrame) -> int:
        """Load data to destination based on config."""
        dest = self.config["destination"]
        dest_type = dest["type"]

        logger.info(f"[LOAD] type={dest_type}, table={dest.get('table')}")

        if dest_type == "sqlite":
            db_path = Path(__file__).parent / dest["database"]
            engine = create_engine(f"sqlite:///{db_path}")
            df.to_sql(
                dest["table"],
                con=engine,
                if_exists=dest.get("if_exists", "replace"),
                index=False,
            )
            engine.dispose()
            logger.info(f"[LOAD] {len(df)} rows → {db_path.name}.{dest['table']}")
            return len(df)

        elif dest_type == "csv":
            out_path = Path(dest["path"])
            df.to_csv(out_path, index=False)
            logger.info(f"[LOAD] {len(df)} rows → {out_path}")
            return len(df)

        else:
            raise ValueError(f"Unsupported destination type: {dest_type}")

    # ---- RUN ----

    def run(self) -> Dict[str, Any]:
        """Execute the full pipeline and return run statistics."""
        start = datetime.now(timezone.utc)
        logger.info("=" * 50)
        logger.info(f"PIPELINE '{self.name}' STARTED")
        logger.info("=" * 50)

        stats: Dict[str, Any] = {"pipeline": self.name}

        try:
            df = self.extract()
            stats["extracted"] = len(df)

            df = self.apply_transformations(df)
            stats["transformed"] = len(df)

            loaded = self.load(df)
            stats["loaded"] = loaded
            stats["status"] = "success"

        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            stats["status"] = "failed"
            stats["error"] = str(e)

        finally:
            duration = (datetime.now(timezone.utc) - start).total_seconds()
            stats["duration_seconds"] = round(duration, 3)
            logger.info(f"PIPELINE '{self.name}' {stats.get('status', 'unknown').upper()}")
            logger.info("=" * 50)

        return stats


# =============================================================================
# MAIN DEMO
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("PRACTICAL DEMO: Config-Driven ETL")
    print("=" * 60)

    # Load the real config from file
    real_config = load_config(CONFIG_DIR / "pipeline_config.json")
    real_config = apply_env_overrides(real_config)

    # Override destination to use a local file for the demo
    real_config["destination"]["database"] = str(
        Path(__file__).parent / "config_demo_output.db"
    )

    print(f"\nRunning pipeline from config: {CONFIG_DIR / 'pipeline_config.json'}")
    print(f"Pipeline: {real_config['pipeline_name']}")
    print(f"Source:   {real_config['source']['path']}")
    print(f"Dest:     {real_config['destination']['database']}")

    # Run the pipeline
    pipeline = ConfigDrivenPipeline(real_config)
    stats = pipeline.run()

    print(f"\nRun stats: {json.dumps(stats, indent=2)}")

    # Verify output
    if stats.get("status") == "success":
        db_path = Path(real_config["destination"]["database"])
        if db_path.exists():
            engine = create_engine(f"sqlite:///{db_path}")
            result = pd.read_sql(
                f"SELECT * FROM {real_config['destination']['table']} LIMIT 5",
                con=engine
            )
            print(f"\nSample output ({result.shape[0]} rows shown):")
            print(result.to_string())
            engine.dispose()

            # Clean up
            db_path.unlink()
            print(f"\nCleaned up {db_path.name}")

    # Also demonstrate running the same code with a different config
    print("\n" + "=" * 50)
    print("SAME CODE, DIFFERENT CONFIG (dev environment)")
    print("=" * 50)

    dev_merged = merge_configs(real_config, {
        "pipeline_name": "sales_etl_dev",
        "destination": {
            "table": "sales_dev",
            "database": str(Path(__file__).parent / "dev_output.db"),
        },
        "logging": {"level": "DEBUG"},
    })

    dev_pipeline = ConfigDrivenPipeline(dev_merged)
    dev_stats = dev_pipeline.run()
    print(f"Dev run stats: {dev_stats}")

    # Clean up dev output
    dev_db = Path(dev_merged["destination"]["database"])
    if dev_db.exists():
        dev_db.unlink()
