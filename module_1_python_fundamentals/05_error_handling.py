"""
Module 1 - Lesson 5: Error Handling and Logging
=================================================
Production ETL pipelines WILL encounter errors: bad data, network failures,
missing files, permission issues. The difference between a fragile script and
a production pipeline is how it handles these situations.

Topics covered:
  - try / except / else / finally blocks
  - Catching specific exception types
  - Raising exceptions
  - Exception chaining (raise ... from ...)
  - Custom exception classes
  - The logging module (the right way to output messages in production)
  - Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
  - Logging to a file and to the console simultaneously
  - Structured logging for ETL metrics
"""

import logging
import traceback
from pathlib import Path
from typing import Optional


# =============================================================================
# 1. BASIC TRY / EXCEPT
# =============================================================================

print("--- try / except ---")

# Without error handling — this would crash the program:
# result = int("not_a_number")  # ValueError!

# With error handling:
def safe_parse_int(value) -> Optional[int]:
    """Parse value to int, return None if it fails."""
    try:
        return int(value)
    except ValueError:
        # ValueError is raised when the string doesn't represent a valid int
        return None
    except TypeError:
        # TypeError is raised when the value can't be converted at all (e.g., None)
        return None

test_cases = ["42", "3.14", "abc", None, True, "  100  "]
for case in test_cases:
    result = safe_parse_int(case)
    print(f"  safe_parse_int({case!r:10}) = {result}")


# =============================================================================
# 2. CATCHING MULTIPLE EXCEPTION TYPES
# =============================================================================

print("\n--- Multiple Exception Types ---")

# Catch multiple exceptions in one line
def read_file_safe(filepath: str) -> Optional[str]:
    """Read a file and return its content, or None on failure."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"  ERROR: File not found: {filepath}")
        return None
    except PermissionError:
        print(f"  ERROR: No permission to read: {filepath}")
        return None
    except (IOError, OSError) as e:
        # Catch multiple exceptions with a tuple
        print(f"  ERROR: IO error reading {filepath}: {e}")
        return None

content = read_file_safe("nonexistent_file.txt")
content = read_file_safe("/etc/shadow")  # likely permission denied

# Catching Exception — the base class for most exceptions (not SystemExit, etc.)
# Use this as a last resort; always prefer specific exception types.
def divide_safe(a: float, b: float) -> Optional[float]:
    """Divide a by b, return None if division fails."""
    try:
        return a / b
    except ZeroDivisionError:
        print("  Cannot divide by zero!")
        return None

print(f"\n  10 / 2 = {divide_safe(10, 2)}")
print(f"  10 / 0 = {divide_safe(10, 0)}")


# =============================================================================
# 3. ELSE AND FINALLY
# =============================================================================

print("\n--- else and finally ---")

# try-except-else-finally:
#   try:     run this code
#   except:  run this if an exception occurred
#   else:    run this if NO exception occurred (optional)
#   finally: run this ALWAYS, exception or not (optional, great for cleanup)

def process_record(record: dict) -> dict:
    """
    Process a single data record with full error handling structure.
    Returns a result dict with either processed data or error info.
    """
    result = {"id": record.get("id"), "status": "unknown"}
    connection = None  # simulated resource

    try:
        # Simulate acquiring a resource
        connection = "db_connection"
        print(f"  [try] Processing record {record['id']}")

        # This might raise an exception
        if record["amount"] < 0:
            raise ValueError(f"Negative amount: {record['amount']}")

        processed_amount = record["amount"] * 1.08  # apply tax
        result["amount_with_tax"] = round(processed_amount, 2)

    except ValueError as e:
        print(f"  [except] Validation error: {e}")
        result["status"] = "error"
        result["error"] = str(e)

    else:
        # Only runs if no exception was raised in try
        print(f"  [else] Record processed successfully")
        result["status"] = "success"

    finally:
        # ALWAYS runs — perfect for cleanup (closing files, DB connections, etc.)
        print(f"  [finally] Closing connection: {connection}")
        connection = None  # "close" the resource

    return result

records = [
    {"id": 1, "amount": 250.00},
    {"id": 2, "amount": -50.00},   # will raise ValueError
    {"id": 3, "amount": 175.50},
]

for rec in records:
    result = process_record(rec)
    print(f"  Result: {result}\n")


# =============================================================================
# 4. RAISING EXCEPTIONS
# =============================================================================

print("--- Raising Exceptions ---")

# raise — explicitly raise an exception
def validate_age(age) -> int:
    """Validate and return age as an integer."""
    if not isinstance(age, (int, float)):
        raise TypeError(f"Age must be numeric, got {type(age).__name__}")
    age = int(age)
    if age < 0:
        raise ValueError(f"Age cannot be negative: {age}")
    if age > 150:
        raise ValueError(f"Age is unrealistically high: {age}")
    return age

for val in [25, -5, 200, "old", None]:
    try:
        result = validate_age(val)
        print(f"  validate_age({val!r}) = {result}")
    except (TypeError, ValueError) as e:
        print(f"  validate_age({val!r}) ERROR: {e}")

# Exception chaining — preserve original context
def load_config(path: str) -> dict:
    """Load a JSON config file, wrapping errors with context."""
    import json
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError as e:
        # 'raise ... from ...' chains exceptions — original error preserved
        raise RuntimeError(f"Config file not found: {path}") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file: {path}") from e

try:
    load_config("missing_config.json")
except RuntimeError as e:
    print(f"\nChained exception: {e}")
    print(f"  Original cause: {e.__cause__}")


# =============================================================================
# 5. CUSTOM EXCEPTION CLASSES
# =============================================================================

print("\n--- Custom Exceptions ---")

# Custom exceptions make code more readable and allow callers to catch
# pipeline-specific errors without catching generic Exception.

class ETLError(Exception):
    """Base class for all ETL pipeline errors."""
    pass

class ExtractionError(ETLError):
    """Raised when data extraction fails."""
    def __init__(self, source: str, reason: str):
        self.source = source
        self.reason = reason
        super().__init__(f"Extraction failed from '{source}': {reason}")

class TransformationError(ETLError):
    """Raised when a transformation step fails."""
    def __init__(self, step: str, record_id, reason: str):
        self.step = step
        self.record_id = record_id
        self.reason = reason
        super().__init__(f"Transformation '{step}' failed for record {record_id}: {reason}")

class ValidationError(ETLError):
    """Raised when data fails validation rules."""
    def __init__(self, field: str, value, rule: str):
        self.field = field
        self.value = value
        self.rule = rule
        super().__init__(f"Validation failed: field='{field}', value={value!r}, rule='{rule}'")

class LoadError(ETLError):
    """Raised when data loading fails."""
    def __init__(self, destination: str, reason: str):
        self.destination = destination
        self.reason = reason
        super().__init__(f"Load failed to '{destination}': {reason}")

# Demonstrate custom exceptions
def extract_from_source(source: str) -> list:
    if source == "bad_source":
        raise ExtractionError(source, "Connection refused (timeout after 30s)")
    return [{"id": 1, "amount": 100.0}]

def transform_record(record: dict, step: str = "normalize") -> dict:
    if record.get("amount") is None:
        raise TransformationError(step, record.get("id"), "amount is None")
    return {**record, "amount": float(record["amount"])}

def validate_record(record: dict) -> None:
    if record["amount"] <= 0:
        raise ValidationError("amount", record["amount"], "must be positive")

scenarios = [
    ("bad_source", None),
    ("good_source", {"id": 1, "amount": None}),
    ("good_source", {"id": 2, "amount": -50}),
    ("good_source", {"id": 3, "amount": 250}),
]

for source, override_record in scenarios:
    try:
        records = extract_from_source(source)
        record = override_record if override_record else records[0]
        transformed = transform_record(record)
        validate_record(transformed)
        print(f"  SUCCESS: record {transformed['id']} processed")
    except ExtractionError as e:
        print(f"  EXTRACT ERROR: {e} (source={e.source})")
    except TransformationError as e:
        print(f"  TRANSFORM ERROR: {e} (step={e.step})")
    except ValidationError as e:
        print(f"  VALIDATION ERROR: {e} (field={e.field}, value={e.value})")
    except ETLError as e:
        print(f"  GENERIC ETL ERROR: {e}")


# =============================================================================
# 6. THE LOGGING MODULE
# =============================================================================

print("\n--- The logging Module ---")

# The logging module is the standard way to produce output in production code.
# Unlike print(), it supports:
#   - Log levels (DEBUG < INFO < WARNING < ERROR < CRITICAL)
#   - Multiple output destinations (console, file, network)
#   - Timestamps and source file/line numbers
#   - Filtering by level

# --- Basic configuration ---
# Only configure logging once, at the entry point (usually main script or module)

# Create a logger for this module
logger = logging.getLogger("etl.module1.lesson5")
logger.setLevel(logging.DEBUG)  # capture ALL levels from DEBUG up

# Log to console with a clean format
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_formatter = logging.Formatter(
    fmt="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)
console_handler.setFormatter(console_formatter)

# Only add the handler if the logger doesn't already have one
# (prevents duplicate output if this module is imported multiple times)
if not logger.handlers:
    logger.addHandler(console_handler)

# Demonstrate log levels
logger.debug("DEBUG: Detailed info for diagnosing problems (verbose)")
logger.info("INFO: Confirmation that things are working as expected")
logger.warning("WARNING: Something unexpected happened, but we can continue")
logger.error("ERROR: A serious problem — a function could not perform its task")
logger.critical("CRITICAL: A severe error — the program may not continue")

# Logging exceptions — use logger.exception() inside an except block
# It automatically includes the full stack trace
try:
    result = 1 / 0
except ZeroDivisionError:
    logger.exception("Caught an unexpected math error")


# =============================================================================
# 7. FILE + CONSOLE LOGGING SETUP (Production Pattern)
# =============================================================================

print("\n--- Production Logging Setup ---")

def setup_etl_logger(
    name: str,
    log_file: Optional[Path] = None,
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
) -> logging.Logger:
    """
    Set up a logger that writes to both console and (optionally) a file.

    Args:
        name: Logger name (usually __name__ or pipeline name).
        log_file: Path to log file. If None, no file logging.
        console_level: Minimum level for console output (default INFO).
        file_level: Minimum level for file output (default DEBUG).

    Returns:
        Configured Logger instance.
    """
    etl_logger = logging.getLogger(name)
    etl_logger.setLevel(logging.DEBUG)  # capture everything; handlers filter

    # Avoid duplicate handlers on re-import
    if etl_logger.handlers:
        return etl_logger

    fmt = "%(asctime)s [%(levelname)-8s] %(name)s - %(message)s"
    formatter = logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S")

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(console_level)
    ch.setFormatter(formatter)
    etl_logger.addHandler(ch)

    # File handler (if path provided)
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setLevel(file_level)
        fh.setFormatter(formatter)
        etl_logger.addHandler(fh)

    return etl_logger


# =============================================================================
# 8. STRUCTURED ETL LOGGING
# =============================================================================

print("\n--- Structured ETL Logging ---")

class ETLLogger:
    """
    A wrapper around Python's logging module that adds ETL-specific
    methods for logging pipeline metrics and events.
    """

    def __init__(self, pipeline_name: str):
        self.pipeline_name = pipeline_name
        self._logger = setup_etl_logger(f"etl.{pipeline_name}")
        self._metrics: dict = {}

    def start(self):
        self._logger.info("=" * 50)
        self._logger.info(f"Pipeline '{self.pipeline_name}' STARTED")
        self._logger.info("=" * 50)

    def end(self, success: bool = True):
        status = "COMPLETED" if success else "FAILED"
        self._logger.info("=" * 50)
        self._logger.info(f"Pipeline '{self.pipeline_name}' {status}")
        self._logger.info(f"Metrics: {self._metrics}")
        self._logger.info("=" * 50)

    def record_metric(self, key: str, value):
        self._metrics[key] = value
        self._logger.debug(f"Metric: {key} = {value}")

    def log_extract(self, source: str, row_count: int):
        self._logger.info(f"[EXTRACT] source='{source}', rows={row_count}")
        self.record_metric("extracted_rows", row_count)

    def log_transform(self, rows_in: int, rows_out: int, rows_rejected: int):
        self._logger.info(
            f"[TRANSFORM] in={rows_in}, out={rows_out}, rejected={rows_rejected}"
        )
        self.record_metric("transformed_rows", rows_out)
        self.record_metric("rejected_rows", rows_rejected)
        if rows_rejected > 0:
            pct = rows_rejected / rows_in * 100
            self._logger.warning(f"{rows_rejected} rows rejected ({pct:.1f}%)")

    def log_load(self, destination: str, row_count: int):
        self._logger.info(f"[LOAD] destination='{destination}', rows={row_count}")
        self.record_metric("loaded_rows", row_count)

    def log_error(self, phase: str, error: Exception):
        self._logger.error(f"[{phase.upper()}] Error: {error}", exc_info=True)


# Demonstrate the ETL logger
etl_log = ETLLogger("sales_pipeline")
etl_log.start()
etl_log.log_extract("sales.csv", 1000)
etl_log.log_transform(rows_in=1000, rows_out=950, rows_rejected=50)
etl_log.log_load("sales_db.orders", 950)
etl_log.end(success=True)


# =============================================================================
# MAIN DEMO
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("PRACTICAL DEMO: Resilient ETL with Error Handling + Logging")
    print("=" * 60)

    pipeline_logger = ETLLogger("demo_pipeline")
    pipeline_logger.start()

    # Simulate extracting from multiple sources, some of which will fail
    sources = ["orders.csv", "bad_source", "customers.csv"]
    all_records = []

    for source in sources:
        try:
            records = extract_from_source(source)
            pipeline_logger.log_extract(source, len(records))
            all_records.extend(records)
        except ExtractionError as e:
            pipeline_logger.log_error("extract", e)
            # Continue to next source instead of crashing
            continue

    # Transform records
    transformed = []
    rejected = 0
    for rec in all_records:
        try:
            t = transform_record(rec)
            validate_record(t)
            transformed.append(t)
        except (TransformationError, ValidationError) as e:
            pipeline_logger.log_error("transform", e)
            rejected += 1

    pipeline_logger.log_transform(
        rows_in=len(all_records),
        rows_out=len(transformed),
        rows_rejected=rejected
    )

    # Simulate load
    pipeline_logger.log_load("output.db", len(transformed))
    pipeline_logger.end(success=True)
