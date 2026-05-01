"""
Module 4 - Lesson 1: ETL Design Principles
=============================================
ETL (Extract, Transform, Load) is the fundamental pattern for moving
and reshaping data. Understanding the design principles behind ETL
makes the difference between fragile scripts and robust pipelines.

This lesson covers concepts through code examples and comments.
No external dependencies are needed — concepts are demonstrated
with plain Python dicts and lists.

Core ETL Design Principles:
  1. Separation of Concerns — Extract, Transform, Load are distinct phases
  2. Idempotency — running the pipeline twice produces the same result
  3. Fail Fast — validate data as early as possible
  4. Observability — log metrics at every stage
  5. Incremental Loading — process only new/changed data
  6. Schema on Read vs Schema on Write
  7. Data Lineage — know where your data came from
"""

import hashlib
import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


# =============================================================================
# 1. THE THREE PHASES OF ETL
# =============================================================================

print("=" * 60)
print("1. THE THREE ETL PHASES")
print("=" * 60)

# ETL = Extract → Transform → Load
#
# EXTRACT: Read data from source systems (files, APIs, databases).
#          Goal: get a faithful copy of source data with minimal changes.
#          Keep raw data separate from transformed data.
#
# TRANSFORM: Clean, validate, reshape, and enrich data.
#            Apply business logic here.
#            This is where the most complexity lives.
#
# LOAD: Write the transformed data to the destination (database, data lake).
#       Handle errors gracefully.
#       Support incremental loads.

# --- Simple illustrative pipeline ---

RAW_SOURCE = [
    # Simulated raw records from a source system (as they arrive, messy)
    {"id": "1", "name": "  alice johnson  ", "dept": "engineering", "salary": "85000", "start_date": "2020-03-15"},
    {"id": "2", "name": "BOB SMITH",         "dept": "marketing",   "salary": "72000", "start_date": "2019-07-01"},
    {"id": "3", "name": "Carol White",        "dept": "engineering", "salary": "N/A",   "start_date": "2021-11-30"},
    {"id": "4", "name": None,                 "dept": "sales",       "salary": "68000", "start_date": "2022-01-15"},
    {"id": "5", "name": "Dave Brown",         "dept": "ENGINEERING", "salary": "91000", "start_date": "invalid"},
]

# --- PHASE 1: EXTRACT ---
def extract(source: List[Dict]) -> List[Dict]:
    """
    Extract phase: make a copy of raw source data.
    In real pipelines, this reads from a file, API, or database.
    The key rule: DO NOT modify data during extraction.
    """
    print(f"[EXTRACT] Reading {len(source)} raw records from source")
    # Return a copy — never mutate the original source
    return [record.copy() for record in source]

# --- PHASE 2: TRANSFORM ---
def transform(records: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """
    Transform phase: clean, validate, and reshape records.
    Returns (valid_records, rejected_records).
    """
    valid = []
    rejected = []

    for rec in records:
        # Validate required fields
        if rec.get("name") is None:
            rejected.append({"id": rec.get("id"), "_rejection_reason": "missing_name"})
            continue

        # Clean string fields
        name = str(rec["name"]).strip().title()
        dept = str(rec.get("dept", "")).strip().lower()

        # Parse salary — reject if not parseable
        try:
            salary = float(str(rec.get("salary", "0")).replace(",", ""))
        except (ValueError, TypeError):
            rejected.append({"id": rec.get("id"), "_rejection_reason": "unparseable_salary"})
            continue

        # Parse date — use None if invalid (don't reject — just flag)
        start_date = rec.get("start_date")
        parsed_date = None
        if start_date:
            try:
                parsed_date = datetime.strptime(start_date, "%Y-%m-%d").date().isoformat()
            except ValueError:
                parsed_date = None   # mark as null but keep the record

        valid.append({
            "id": int(rec["id"]),
            "name": name,
            "department": dept,
            "salary": salary,
            "start_date": parsed_date,
            "_etl_loaded_at": datetime.now(timezone.utc).isoformat(),
        })

    print(f"[TRANSFORM] {len(valid)} valid, {len(rejected)} rejected")
    return valid, rejected

# --- PHASE 3: LOAD ---
def load(records: List[Dict], target: str) -> int:
    """
    Load phase: write records to destination.
    In real pipelines, this writes to a database or file.
    """
    print(f"[LOAD] Writing {len(records)} records to '{target}'")
    # BEST PRACTICE: Never log per-record details that could expose PII.
    # Use aggregate counts for operational visibility instead.
    print(f"[LOAD] Successfully wrote {len(records)} records.")
    return len(records)

# Run the pipeline
raw = extract(RAW_SOURCE)
valid_records, rejected_records = transform(raw)
count = load(valid_records, "employees_db")

print(f"\nRejected records:")
# BEST PRACTICE: Log only aggregate rejection counts — never log individual
# records or record IDs, as they may carry PII via taint from the source.
rejection_counts: Dict[str, int] = {}
for r in rejected_records:
    reason = r['_rejection_reason']
    rejection_counts[reason] = rejection_counts.get(reason, 0) + 1
for reason, count in rejection_counts.items():
    print(f"  {reason}: {count} record(s)")


# =============================================================================
# 2. IDEMPOTENCY
# =============================================================================

print("\n" + "=" * 60)
print("2. IDEMPOTENCY")
print("=" * 60)

# An idempotent pipeline produces the same result whether run once or 100 times.
# This is critical because pipelines often need to be re-run:
#   - After a failure
#   - To reprocess historical data
#   - After fixing a bug in the transform logic
#
# Pattern 1: "DELETE then INSERT" (simplest)
# Pattern 2: "UPSERT" (update if exists, insert if new)
# Pattern 3: "Truncate and reload" for small tables
# Pattern 4: Partition replacement for large tables

# Simulated in-memory "database"
DATABASE: Dict[str, Dict] = {}

def load_idempotent(records: List[Dict], key_field: str = "id") -> Dict[str, int]:
    """
    Idempotent load: upsert records by key.
    Running this twice with the same data produces the same state.
    """
    inserted = 0
    updated = 0

    for rec in records:
        key = str(rec[key_field])
        if key in DATABASE:
            DATABASE[key] = rec
            updated += 1
        else:
            DATABASE[key] = rec
            inserted += 1

    return {"inserted": inserted, "updated": updated}

# First run
print("First run:")
stats = load_idempotent(valid_records)
print(f"  {stats}")
print(f"  DB size: {len(DATABASE)} records")

# Second run (same data — result should be same)
print("\nSecond run (same data):")
stats = load_idempotent(valid_records)
print(f"  {stats}")
print(f"  DB size: {len(DATABASE)} records (unchanged — idempotent!)")


# =============================================================================
# 3. FAIL FAST — VALIDATE EARLY
# =============================================================================

print("\n" + "=" * 60)
print("3. FAIL FAST — VALIDATE EARLY")
print("=" * 60)

# "Fail fast" means detecting problems as early as possible in the pipeline.
# The later a bug is caught, the more expensive it is to fix.
#
# Validation layers:
#   Level 1: Schema validation (right types, required fields present)
#   Level 2: Integrity validation (values in expected ranges)
#   Level 3: Business rule validation (amounts positive, dates in valid range)
#   Level 4: Cross-record validation (no duplicate IDs, referential integrity)

SCHEMA = {
    "id":         {"type": int,   "required": True},
    "name":       {"type": str,   "required": True},
    "department": {"type": str,   "required": True},
    "salary":     {"type": float, "required": True, "min": 0, "max": 500_000},
}

def validate_schema(record: Dict, schema: Dict) -> List[str]:
    """
    Validate a record against a schema definition.
    Returns a list of error messages (empty if valid).
    """
    errors = []

    for field, rules in schema.items():
        value = record.get(field)

        # Check required fields
        if rules.get("required") and (value is None or value == ""):
            errors.append(f"'{field}' is required")
            continue

        if value is None:
            continue   # field is optional and missing — OK

        # Check type
        if not isinstance(value, rules["type"]):
            errors.append(f"'{field}' must be {rules['type'].__name__}, got {type(value).__name__}")
            continue

        # Check min/max — report the rule violation without echoing back the value
        if "min" in rules and value < rules["min"]:
            errors.append(f"'{field}' is below minimum ({rules['min']})")
        if "max" in rules and value > rules["max"]:
            errors.append(f"'{field}' exceeds maximum ({rules['max']})")

    return errors

print("Schema validation results:")
# BEST PRACTICE: Report aggregate counts, not per-record details with record IDs.
valid_count = 0
invalid_count = 0
for rec in valid_records:
    errors = validate_schema(rec, SCHEMA)
    if errors:
        invalid_count += 1
    else:
        valid_count += 1
print(f"  {valid_count} record(s) passed all schema checks")
print(f"  {invalid_count} record(s) failed schema validation")


# =============================================================================
# 4. OBSERVABILITY — LOG PIPELINE METRICS
# =============================================================================

print("\n" + "=" * 60)
print("4. OBSERVABILITY — PIPELINE METRICS")
print("=" * 60)

# A production pipeline should report metrics so you can:
#   - Know if a pipeline ran successfully
#   - Compare this run with previous runs
#   - Detect data quality degradation over time

class PipelineRun:
    """Tracks metrics for a single pipeline execution."""

    def __init__(self, pipeline_name: str, run_id: Optional[str] = None):
        self.pipeline_name = pipeline_name
        self.run_id = run_id or datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.metrics: Dict[str, Any] = {}
        self.errors: List[str] = []
        self.status = "running"

    def record(self, key: str, value: Any) -> None:
        """Record a metric value."""
        self.metrics[key] = value

    def add_error(self, error: str) -> None:
        """Record an error message."""
        self.errors.append(error)

    def finish(self, success: bool = True) -> None:
        """Mark the run as finished and compute duration."""
        self.end_time = time.time()
        self.status = "success" if success else "failed"
        self.metrics["duration_seconds"] = round(self.end_time - self.start_time, 3)

    def summary(self) -> Dict:
        """Return a summary dict for logging/storage."""
        return {
            "run_id": self.run_id,
            "pipeline": self.pipeline_name,
            "status": self.status,
            "metrics": self.metrics,
            "errors": self.errors,
        }

# Demonstrate pipeline metrics tracking
run = PipelineRun("employee_etl")

raw = extract(RAW_SOURCE)
run.record("extracted_rows", len(raw))

valid, rejected = transform(raw)
run.record("transformed_rows", len(valid))
run.record("rejected_rows", len(rejected))
run.record("rejection_rate", round(len(rejected) / len(raw) * 100, 1))

loaded = load(valid, "employees_db")
run.record("loaded_rows", loaded)

run.finish(success=True)
print("\nPipeline run summary:")
print(json.dumps(run.summary(), indent=2))


# =============================================================================
# 5. INCREMENTAL LOADING
# =============================================================================

print("\n" + "=" * 60)
print("5. INCREMENTAL LOADING")
print("=" * 60)

# Processing ALL data every run is expensive for large datasets.
# Incremental loading processes only new or changed records.
#
# Common incremental patterns:
#   - Timestamp-based: "WHERE updated_at > last_run_time"
#   - ID-based: "WHERE id > max_loaded_id"
#   - Hash-based: compare checksums of records

def compute_checksum(record: Dict) -> str:
    """Compute a stable hash of a record to detect changes."""
    # Sort keys for stability, then hash the JSON representation
    # Use SHA-256 — preferred over MD5 for data-integrity checksums
    stable_json = json.dumps(record, sort_keys=True)
    return hashlib.sha256(stable_json.encode()).hexdigest()[:16]

# Simulate existing records in the destination
existing_records = {
    "1": {"id": 1, "name": "Alice Johnson", "department": "engineering", "salary": 85000.0},
    "2": {"id": 2, "name": "Bob Smith",     "department": "marketing",   "salary": 72000.0},
}

# New batch from source
new_batch = [
    {"id": 1, "name": "Alice Johnson", "department": "engineering", "salary": 90000.0},  # salary changed
    {"id": 2, "name": "Bob Smith",     "department": "marketing",   "salary": 72000.0},  # unchanged
    {"id": 6, "name": "Frank Miller",  "department": "sales",       "salary": 65000.0},  # new record
]

inserts = []
updates = []
skips = []

for rec in new_batch:
    key = str(rec["id"])
    if key not in existing_records:
        inserts.append(rec)   # new record
    elif compute_checksum(rec) != compute_checksum(existing_records[key]):
        updates.append(rec)   # existing but changed
    else:
        skips.append(rec)     # no change

print(f"Incremental load analysis:")
print(f"  New records (INSERT): {len(inserts)} → {[r['id'] for r in inserts]}")
print(f"  Changed records (UPDATE): {len(updates)} → {[r['id'] for r in updates]}")
print(f"  Unchanged records (SKIP): {len(skips)} → {[r['id'] for r in skips]}")


# =============================================================================
# 6. DATA LINEAGE
# =============================================================================

print("\n" + "=" * 60)
print("6. DATA LINEAGE")
print("=" * 60)

# Data lineage answers: "Where did this data come from? What transformations were applied?"
# Adding lineage metadata to records makes debugging much easier.

def add_lineage_metadata(
    record: Dict,
    source: str,
    pipeline: str,
    transformations: List[str],
) -> Dict:
    """
    Enrich a record with data lineage metadata.
    This is added to every record in the loaded dataset.
    """
    return {
        **record,
        "_lineage": {
            "source": source,
            "pipeline": pipeline,
            "transformations_applied": transformations,
            "loaded_at": datetime.now(timezone.utc).isoformat(),
            "source_record_hash": compute_checksum(record),
        }
    }

sample = valid_records[0]
with_lineage = add_lineage_metadata(
    sample,
    source="employees.csv",
    pipeline="employee_etl_v1",
    transformations=["strip_whitespace", "normalize_case", "parse_date", "cast_salary_to_float"]
)
print("Record with lineage metadata:")
print(json.dumps(with_lineage, indent=2))


# =============================================================================
# MAIN DEMO
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("PRACTICAL DEMO: All Principles Together")
    print("=" * 60)

    run = PipelineRun("principles_demo")

    # Extract
    raw_data = extract(RAW_SOURCE)
    run.record("source", "RAW_SOURCE (in-memory)")
    run.record("extracted", len(raw_data))

    # Validate schema before transform (fail fast)
    print("\nPre-transform schema check:")
    pre_errors = 0
    for rec in raw_data:
        # Basic sanity: 'id' must exist
        if not rec.get("id"):
            run.add_error("Missing id in a record (record skipped)")
            pre_errors += 1
    print(f"  Pre-transform errors found: {pre_errors}")

    # Transform
    valid, rejected = transform(raw_data)
    run.record("valid_after_transform", len(valid))
    run.record("rejected", len(rejected))

    # Post-transform schema validation
    validation_errors = 0
    for rec in valid:
        errs = validate_schema(rec, SCHEMA)
        if errs:
            validation_errors += 1
            # Log only the count of violations per rule, not record-level PII.
            run.add_error(f"schema_violation: {'; '.join(errs)}")
    run.record("validation_errors", validation_errors)

    # Load (idempotent upsert)
    load_stats = load_idempotent(valid)
    run.record("loaded_inserted", load_stats["inserted"])
    run.record("loaded_updated", load_stats["updated"])

    run.finish(success=True)
    print("\nFinal pipeline summary:")
    print(json.dumps(run.summary(), indent=2))
