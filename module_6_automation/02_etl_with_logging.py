"""
Module 6 - Lesson 2: ETL Logging Best Practices
=================================================
Logging is the most important observability tool in production ETL.
When a pipeline fails at 2am, logs are what you use to diagnose the problem.

Python's built-in `logging` module is powerful but requires proper setup.
This lesson shows the patterns used in production data engineering.

Topics covered:
  - Log levels and when to use each
  - Configuring handlers (console, rotating file)
  - Log formatters with useful context
  - Creating module-specific loggers (logger hierarchy)
  - Logging ETL metrics in a structured way
  - Avoiding common logging mistakes
  - Context variables with LoggerAdapter
  - Capturing uncaught exceptions in the log
"""

import json
import logging
import logging.handlers
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

LOGS_DIR = Path(__file__).parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)


# =============================================================================
# 1. LOG LEVELS
# =============================================================================

print("=" * 60)
print("1. LOG LEVELS")
print("=" * 60)

# Python logging levels (lowest to highest):
#
#   DEBUG    (10): Detailed diagnostic info. Only in development.
#   INFO     (20): Confirmation that things are working. Every major step.
#   WARNING  (30): Something unexpected happened, but we can continue.
#   ERROR    (40): A serious problem. A function couldn't do its job.
#   CRITICAL (50): A very serious error. The program may stop.
#
# The configured level acts as a MINIMUM threshold.
# Setting level=INFO means: capture INFO, WARNING, ERROR, CRITICAL
# but NOT DEBUG messages.

# Basic demo
basic_logger = logging.getLogger("demo.levels")
basic_logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter("[%(levelname)-8s] %(message)s"))
basic_logger.addHandler(handler)

basic_logger.debug("DEBUG: Low-level tracing (query params, row counts per batch)")
basic_logger.info("INFO:  Pipeline step started/completed, record counts")
basic_logger.warning("WARNING: Data quality issue found, missing field, slow query")
basic_logger.error("ERROR:  DB connection failed, file not found, transform failed")
basic_logger.critical("CRITICAL: Cannot continue — disk full, license expired")

# Clean up demo logger
basic_logger.handlers.clear()


# =============================================================================
# 2. LOGGER HIERARCHY
# =============================================================================

print("\n" + "=" * 60)
print("2. LOGGER HIERARCHY")
print("=" * 60)

# Loggers form a hierarchy based on their name (separated by dots).
# A logger "etl.extract" is a child of "etl".
# By default, children propagate to their parent logger.
#
# Best practice: use __name__ as the logger name in each module.
# This gives you fine-grained control over which modules log what.

# Parent logger
etl_logger = logging.getLogger("etl")
etl_logger.setLevel(logging.DEBUG)

# Child loggers (automatically get their parent's handlers)
extract_logger = logging.getLogger("etl.extract")
transform_logger = logging.getLogger("etl.transform")
load_logger = logging.getLogger("etl.load")

# You can set a higher threshold for a noisy child
transform_logger.setLevel(logging.WARNING)  # only warnings+ from transform

print("Logger hierarchy:")
print(f"  etl (root): level={etl_logger.level}")
print(f"  etl.extract:    effective level={extract_logger.getEffectiveLevel()}")
print(f"  etl.transform:  effective level={transform_logger.getEffectiveLevel()} (overridden)")
print(f"  etl.load:       effective level={load_logger.getEffectiveLevel()}")


# =============================================================================
# 3. SETTING UP PRODUCTION LOGGING
# =============================================================================

print("\n" + "=" * 60)
print("3. PRODUCTION LOGGING SETUP")
print("=" * 60)

def setup_logging(
    pipeline_name: str,
    log_dir: Path = LOGS_DIR,
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
) -> logging.Logger:
    """
    Configure logging with rotating file + console handlers.

    Using RotatingFileHandler:
      - Automatically rotates log files when they reach max_bytes
      - Keeps backup_count old log files
      - Prevents logs from filling up disk

    Args:
        pipeline_name: Used as logger name and in the log filename.
        log_dir: Directory to store log files.
        console_level: Minimum level for console output.
        file_level: Minimum level for file output.
        max_bytes: Maximum log file size before rotation.
        backup_count: Number of rotated files to keep.

    Returns:
        Configured Logger instance.
    """
    logger = logging.getLogger(f"etl.{pipeline_name}")
    logger.setLevel(logging.DEBUG)  # capture everything; handlers filter

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    logger.propagate = False   # don't propagate to root logger

    # --- Console handler: INFO and above ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    logger.addHandler(console_handler)

    # --- Rotating file handler: DEBUG and above ---
    log_file = log_dir / f"{pipeline_name}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8"
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s [%(levelname)-8s] [%(name)s] %(filename)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    logger.addHandler(file_handler)

    return logger

pipeline_logger = setup_logging("sales_pipeline")
pipeline_logger.info("Sales pipeline logger configured")
pipeline_logger.debug("This appears only in the log file (not console)")
print(f"Log file written to: {LOGS_DIR}/sales_pipeline.log")


# =============================================================================
# 4. STRUCTURED LOGGING FOR ETL METRICS
# =============================================================================

print("\n" + "=" * 60)
print("4. STRUCTURED ETL LOGGING")
print("=" * 60)

class ETLMetricsLogger:
    """
    Logs structured metrics for each ETL phase.
    Metrics are logged as JSON for easy parsing by log aggregation tools
    like Elasticsearch, Splunk, or Datadog.
    """

    def __init__(self, pipeline_name: str, run_id: Optional[str] = None):
        self.pipeline_name = pipeline_name
        self.run_id = run_id or datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self._logger = setup_logging(
            f"{pipeline_name}",
            console_level=logging.INFO,
            file_level=logging.DEBUG,
        )
        self._phase_start: Optional[float] = None
        self._metrics: Dict[str, Any] = {}

    def _log_event(self, event_type: str, data: Dict, level: int = logging.INFO):
        """Log a structured event as JSON."""
        event = {
            "event": event_type,
            "pipeline": self.pipeline_name,
            "run_id": self.run_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **data
        }
        self._logger.log(level, json.dumps(event))

    def pipeline_started(self):
        import time
        self._phase_start = time.time()
        self._log_event("pipeline_started", {})
        self._logger.info("=" * 50)
        self._logger.info(f"PIPELINE '{self.pipeline_name}' STARTED | run_id={self.run_id}")

    def pipeline_finished(self, success: bool):
        import time
        duration = round(time.time() - self._phase_start, 3) if self._phase_start else 0
        status = "SUCCESS" if success else "FAILED"
        self._log_event("pipeline_finished", {"status": status, "duration_seconds": duration})
        self._logger.info(f"PIPELINE '{self.pipeline_name}' {status} | {duration}s")
        self._logger.info("=" * 50)

    def log_extract(self, source: str, rows: int, bytes_read: Optional[int] = None):
        data = {"phase": "extract", "source": source, "rows_extracted": rows}
        if bytes_read:
            data["bytes_read"] = bytes_read
        self._log_event("phase_complete", data)
        self._logger.info(f"[EXTRACT] source={source!r}, rows={rows}")

    def log_transform(self, rows_in: int, rows_out: int, rejected: int):
        rejection_rate = rejected / max(rows_in, 1) * 100
        self._log_event("phase_complete", {
            "phase": "transform",
            "rows_in": rows_in,
            "rows_out": rows_out,
            "rows_rejected": rejected,
            "rejection_rate_pct": round(rejection_rate, 2),
        })
        self._logger.info(f"[TRANSFORM] in={rows_in}, out={rows_out}, rejected={rejected} ({rejection_rate:.1f}%)")
        if rejection_rate > 10:
            self._logger.warning(f"High rejection rate: {rejection_rate:.1f}%")

    def log_load(self, destination: str, rows: int, table: str):
        self._log_event("phase_complete", {
            "phase": "load",
            "destination": destination,
            "table": table,
            "rows_loaded": rows,
        })
        self._logger.info(f"[LOAD] destination={destination!r}, table={table!r}, rows={rows}")

    def log_error(self, phase: str, error: Exception):
        self._log_event("error", {
            "phase": phase,
            "error_type": type(error).__name__,
            "error_message": str(error),
        }, level=logging.ERROR)
        self._logger.error(f"[{phase.upper()}] {type(error).__name__}: {error}")


# Demonstrate the metrics logger
metrics = ETLMetricsLogger("demo_sales_etl")
metrics.pipeline_started()
metrics.log_extract("sales.csv", rows=1000)
metrics.log_transform(rows_in=1000, rows_out=950, rejected=50)
metrics.log_load("output.db", rows=950, table="clean_sales")
metrics.pipeline_finished(success=True)


# =============================================================================
# 5. LOGGER ADAPTER — ADDING CONTEXT TO LOG MESSAGES
# =============================================================================

print("\n" + "=" * 60)
print("5. LOGGER ADAPTER — CONTEXT IN LOGS")
print("=" * 60)

# LoggerAdapter lets you inject context into every log message
# without repeating it in every log call.
# Useful for adding job_id, pipeline_name, batch_id, etc.

class PipelineLoggerAdapter(logging.LoggerAdapter):
    """
    Adds pipeline context to every log message.
    The 'extra' dict is automatically injected into the format string.
    """
    def process(self, msg, kwargs):
        pipeline = self.extra.get("pipeline", "?")
        batch = self.extra.get("batch_id", "?")
        return f"[{pipeline}][batch={batch}] {msg}", kwargs

# Usage
base_logger = setup_logging("context_demo")
adapter = PipelineLoggerAdapter(
    base_logger,
    extra={"pipeline": "orders_etl", "batch_id": "2024-01-15"}
)

adapter.info("Starting extraction")
adapter.info("Processing 500 records")
adapter.warning("Found 12 records with missing customer IDs")
adapter.info("Load complete")


# =============================================================================
# 6. CAPTURING UNCAUGHT EXCEPTIONS
# =============================================================================

print("\n" + "=" * 60)
print("6. CAPTURING UNCAUGHT EXCEPTIONS")
print("=" * 60)

# By default, Python prints uncaught exceptions to stderr and exits.
# In production, we want these captured in the log file.

def log_uncaught_exception(exc_type, exc_value, exc_traceback):
    """
    Custom sys.excepthook — called when an unhandled exception occurs.
    Logs the full traceback to our logger instead of just printing to stderr.
    """
    if issubclass(exc_type, KeyboardInterrupt):
        # Don't log Ctrl+C as an error
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    pipeline_logger.critical(
        "Uncaught exception",
        exc_info=(exc_type, exc_value, exc_traceback)
    )

# Install the custom exception handler
sys.excepthook = log_uncaught_exception
print("Installed custom sys.excepthook for uncaught exceptions")


# =============================================================================
# MAIN DEMO
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("PRACTICAL DEMO: Full ETL with Comprehensive Logging")
    print("=" * 60)

    import time
    import random

    def simulate_etl_run(pipeline_name: str, batch_size: int = 100):
        """Simulate a full ETL run with comprehensive logging."""
        logger = ETLMetricsLogger(pipeline_name)
        logger.pipeline_started()

        try:
            # Extract
            time.sleep(0.05)
            rows_extracted = batch_size + random.randint(-10, 10)
            logger.log_extract("source_db.orders", rows=rows_extracted)

            # Transform
            time.sleep(0.05)
            rejected = random.randint(0, rows_extracted // 10)
            rows_out = rows_extracted - rejected
            logger.log_transform(rows_in=rows_extracted, rows_out=rows_out, rejected=rejected)

            # Simulate occasional warnings
            if rejected > 5:
                logger._logger.warning(f"Rejection count {rejected} exceeded threshold 5")

            # Load
            time.sleep(0.02)
            logger.log_load("output.db", rows=rows_out, table=f"{pipeline_name}_clean")

            logger.pipeline_finished(success=True)

        except Exception as e:
            logger.log_error("unknown", e)
            logger.pipeline_finished(success=False)
            raise

    # Run three simulated pipelines
    for pipeline in ["sales_etl", "inventory_etl", "customer_etl"]:
        simulate_etl_run(pipeline, batch_size=150)
        time.sleep(0.1)

    print(f"\nCheck log files in: {LOGS_DIR}")
    for log_file in sorted(LOGS_DIR.glob("*.log")):
        size = log_file.stat().st_size
        print(f"  {log_file.name}: {size} bytes")
