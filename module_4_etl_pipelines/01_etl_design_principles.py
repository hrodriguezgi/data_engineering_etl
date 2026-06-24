# %% [markdown]
# # Module 4 - Lesson 1: ETL Design Principles
#
# ETL (Extract, Transform, Load) is the fundamental pattern for moving and reshaping data.
# Understanding the design principles behind ETL makes the difference between fragile scripts
# and robust pipelines that survive production failures.
#
# **What You'll Learn:**
# - The three phases of ETL and why separation matters
# - Idempotency: making pipelines safe to re-run
# - Failing fast: catching data problems early
# - Observability: metrics that help you debug
# - Incremental loading: processing only what's new
# - Data lineage: knowing where data came from

import hashlib
import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


# %% [markdown]
# ## Problem 1: What Breaks Without ETL Separation?
#
# **Scenario:** You're running a data pipeline that reads sales data, cleans it, and loads
# it to a database. If an error happens during the load phase, you've already modified your
# source data during extraction. Now you can't re-run safely—you've corrupted the original.
#
# **The Cost:** Lost data auditing, inability to recover, and no idea what state you're in.


# %%
# WRONG: Modifying data during extraction
def bad_extract_modifies_source(source: List[Dict]) -> List[Dict]:
    """
    DON'T DO THIS: Modifying the source data during extraction.
    """
    # This modifies the original list in place!
    for record in source:
        record["processed"] = True
    return source


# What happens?
RAW_SOURCE = [
    {"id": "1", "name": "alice", "salary": "85000"},
    {"id": "2", "name": "bob", "salary": "72000"},
]

print("Before bad_extract:")
print(f"  RAW_SOURCE[0] = {RAW_SOURCE[0]}")

bad_result = bad_extract_modifies_source(RAW_SOURCE)

print("After bad_extract:")
print(f"  RAW_SOURCE[0] = {RAW_SOURCE[0]}  ← Original data was modified!")
print()

# %% [markdown]
# **The Issue:** Once extraction modifies the source, you can't recover if the load fails.
# You've lost the original data audit trail.


# %%
# RIGHT: Extract returns a copy, leaving source untouched
def good_extract(source: List[Dict]) -> List[Dict]:
    """
    CORRECT: Extract makes a copy of raw source data, never modifying the original.
    This is critical for safety and auditability.
    """
    return [record.copy() for record in source]


# Test it
RAW_SOURCE_2 = [
    {"id": "1", "name": "alice", "salary": "85000"},
    {"id": "2", "name": "bob", "salary": "72000"},
]

print("Before good_extract:")
print(f"  RAW_SOURCE_2[0] = {RAW_SOURCE_2[0]}")

extracted = good_extract(RAW_SOURCE_2)
extracted[0]["processed"] = True

print("After good_extract (and modifying extracted copy):")
print(f"  RAW_SOURCE_2[0] = {RAW_SOURCE_2[0]}  ← Original unchanged!")
print(f"  extracted[0] = {extracted[0]}")
print()


# %% [markdown]
# ## The Three Phases of ETL
#
# ETL divides data movement into three distinct, isolated phases:

# %%
print("=" * 60)
print("THE THREE ETL PHASES")
print("=" * 60)

# EXTRACT: Read data from source systems with ZERO transformation
# TRANSFORM: Clean, validate, reshape data (business logic lives here)
# LOAD: Write to destination (database, file, data lake)

RAW_EMPLOYEE_DATA = [
    # Real messy data from a source system
    {"id": "1", "name": "  alice johnson  ", "dept": "engineering", "salary": "85000", "start_date": "2020-03-15"},
    {"id": "2", "name": "BOB SMITH", "dept": "marketing", "salary": "72000", "start_date": "2019-07-01"},
    {"id": "3", "name": "Carol White", "dept": "engineering", "salary": "N/A", "start_date": "2021-11-30"},
    {"id": "4", "name": None, "dept": "sales", "salary": "68000", "start_date": "2022-01-15"},
    {"id": "5", "name": "Dave Brown", "dept": "ENGINEERING", "salary": "91000", "start_date": "invalid"},
]


# --- PHASE 1: EXTRACT ---
def extract(source: List[Dict]) -> List[Dict]:
    """Extract: Copy raw source data without modification."""
    print(f"[EXTRACT] Reading {len(source)} raw records")
    return [record.copy() for record in source]


# --- PHASE 2: TRANSFORM ---
def transform(records: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """Transform: Clean, validate, reshape. Returns (valid, rejected)."""
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

        # Parse salary
        try:
            salary = float(str(rec.get("salary", "0")).replace(",", ""))
        except (ValueError, TypeError):
            rejected.append({"id": rec.get("id"), "_rejection_reason": "unparseable_salary"})
            continue

        # Parse date
        start_date = rec.get("start_date")
        parsed_date = None
        if start_date:
            try:
                parsed_date = datetime.strptime(start_date, "%Y-%m-%d").date().isoformat()
            except ValueError:
                parsed_date = None

        valid.append(
            {
                "id": int(rec["id"]),
                "name": name,
                "department": dept,
                "salary": salary,
                "start_date": parsed_date,
                "_etl_loaded_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    print(f"[TRANSFORM] {len(valid)} valid, {len(rejected)} rejected")
    return valid, rejected


# --- PHASE 3: LOAD ---
def load(records: List[Dict], target: str) -> int:
    """Load: Write records to destination (simulated)."""
    print(f"[LOAD] Writing {len(records)} records to '{target}'")
    return len(records)


# Run the pipeline
raw = extract(RAW_EMPLOYEE_DATA)
valid_records, rejected_records = transform(raw)
count = load(valid_records, "employees_db")

print("\nRejection summary:")
rejection_counts: Dict[str, int] = {}
for r in rejected_records:
    reason = r["_rejection_reason"]
    rejection_counts[reason] = rejection_counts.get(reason, 0) + 1
for reason, count in rejection_counts.items():
    print(f"  {reason}: {count}")
print()


# %% [markdown]
# ## Problem 2: Idempotency - Running Twice Should Be Safe
#
# **Scenario:** Your pipeline fails halfway through. You fix the bug and re-run it.
# But if your pipeline isn't idempotent, running it twice produces different results:
# - First run: 100 rows loaded
# - Second run: 200 rows (duplicates!)
#
# **The Cost:** Duplicated data, corrupt analytics, financial reports with wrong numbers.

# %%
# WRONG: Non-idempotent loading (INSERT always)
DATABASE_WRONG = {}


def bad_load_not_idempotent(records: List[Dict]) -> int:
    """Non-idempotent: Always INSERTs, causing duplicates on re-run."""
    count = 0
    for rec in records:
        # Always insert — no check for existing records
        DATABASE_WRONG[f"{len(DATABASE_WRONG)}_{rec['id']}"] = rec
        count += 1
    return count


print("Non-idempotent loading (WRONG):")
test_data = [
    {"id": 1, "name": "Alice", "salary": 85000},
    {"id": 2, "name": "Bob", "salary": 72000},
]

print(f"First run: Loaded {bad_load_not_idempotent(test_data)} records")
print(f"  DB size: {len(DATABASE_WRONG)}")

print(f"Second run (same data): Loaded {bad_load_not_idempotent(test_data)} records")
print(f"  DB size: {len(DATABASE_WRONG)}  ← Duplicates! This is bad!")
print()

# %%
# RIGHT: Idempotent loading (UPSERT by key)
DATABASE_RIGHT = {}


def good_load_idempotent(records: List[Dict], key_field: str = "id") -> Dict[str, int]:
    """
    ✓ Idempotent: UPSERT by key.
    Running twice with same data produces same state.
    """
    inserted = 0
    updated = 0

    for rec in records:
        key = str(rec[key_field])
        if key in DATABASE_RIGHT:
            DATABASE_RIGHT[key] = rec
            updated += 1
        else:
            DATABASE_RIGHT[key] = rec
            inserted += 1

    return {"inserted": inserted, "updated": updated}


print("Idempotent loading (CORRECT):")
test_data_2 = [
    {"id": 1, "name": "Alice", "salary": 85000},
    {"id": 2, "name": "Bob", "salary": 72000},
]

print(f"First run: {good_load_idempotent(test_data_2)}")
print(f"  DB size: {len(DATABASE_RIGHT)}")

print(f"Second run (same data): {good_load_idempotent(test_data_2)}")
print(f"  DB size: {len(DATABASE_RIGHT)}  ← Idempotent! Same state.")
print()


# %% [markdown]
# ## Problem 3: Failing Late vs. Failing Fast
#
# **Scenario:** Invalid data makes it to the database. Days later, your analytics team
# discovers rows with null IDs or negative salaries. By then, they've built reports on
# corrupted data.
#
# **The Cost:** Expensive fixes, lost confidence in data, re-running analytics from scratch.

# %%
print("=" * 60)
print("FAIL FAST — VALIDATE EARLY")
print("=" * 60)

# Define schema rules
SCHEMA = {
    "id": {"type": int, "required": True},
    "name": {"type": str, "required": True},
    "department": {"type": str, "required": True},
    "salary": {"type": float, "required": True, "min": 0, "max": 500_000},
}


def validate_schema(record: Dict, schema: Dict) -> List[str]:
    """
    Validate a record against a schema.
    Returns list of errors (empty if valid).
    """
    errors = []

    for field, rules in schema.items():
        value = record.get(field)

        # Check required fields
        if rules.get("required") and (value is None or value == ""):
            errors.append(f"'{field}' is required")
            continue

        if value is None:
            continue

        # Check type
        if not isinstance(value, rules["type"]):
            errors.append(f"'{field}' must be {rules['type'].__name__}, got {type(value).__name__}")
            continue

        # Check min/max
        if "min" in rules and value < rules["min"]:
            errors.append(f"'{field}' below minimum ({rules['min']})")
        if "max" in rules and value > rules["max"]:
            errors.append(f"'{field}' exceeds maximum ({rules['max']})")

    return errors


print("Schema validation of transformed records:")
valid_count = 0
invalid_count = 0
for rec in valid_records:
    errors = validate_schema(rec, SCHEMA)
    if errors:
        invalid_count += 1
    else:
        valid_count += 1
print(f"  {valid_count} passed validation")
print(f"  {invalid_count} failed validation")
print()


# %% [markdown]
# ## Observability: Tracking Pipeline Health
#
# **Scenario:** Your pipeline runs for 8 hours, silently processing 10 million rows.
# It finishes "successfully" but loaded 0 rows due to a schema change.
# You don't notice for a week.
#
# **The Cost:** Stale data in production, missed insights, lost operational visibility.

# %%
print("=" * 60)
print("OBSERVABILITY — PIPELINE METRICS")
print("=" * 60)


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
        """Record a metric."""
        self.metrics[key] = value

    def add_error(self, error: str) -> None:
        """Record an error."""
        self.errors.append(error)

    def finish(self, success: bool = True) -> None:
        """Mark as finished and compute duration."""
        self.end_time = time.time()
        self.status = "success" if success else "failed"
        self.metrics["duration_seconds"] = round(self.end_time - self.start_time, 3)

    def summary(self) -> Dict:
        """Return summary dict for logging."""
        return {
            "run_id": self.run_id,
            "pipeline": self.pipeline_name,
            "status": self.status,
            "metrics": self.metrics,
            "errors": self.errors,
        }


# Demonstrate metrics tracking
run = PipelineRun("employee_etl")

raw = extract(RAW_EMPLOYEE_DATA)
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
print()


# %% [markdown]
# ## Incremental Loading: Processing Only What's New
#
# **Scenario:** Every night you reload all 100 million customer records,
# but only 10,000 changed. You're wasting 99.99% of compute time and money.
#
# **The Cost:** Slow pipelines, high cloud bills, delayed data refresh times.

# %%
print("=" * 60)
print("INCREMENTAL LOADING")
print("=" * 60)


def compute_checksum(record: Dict) -> str:
    """Compute stable hash of record to detect changes."""
    stable_json = json.dumps(record, sort_keys=True)
    return hashlib.sha256(stable_json.encode()).hexdigest()[:16]


# Existing records already in destination
existing_records = {
    "1": {"id": 1, "name": "Alice Johnson", "department": "engineering", "salary": 85000.0},
    "2": {"id": 2, "name": "Bob Smith", "department": "marketing", "salary": 72000.0},
}

# New batch from source
new_batch = [
    {"id": 1, "name": "Alice Johnson", "department": "engineering", "salary": 90000.0},  # salary changed
    {"id": 2, "name": "Bob Smith", "department": "marketing", "salary": 72000.0},  # unchanged
    {"id": 6, "name": "Frank Miller", "department": "sales", "salary": 65000.0},  # new
]

inserts = []
updates = []
skips = []

for rec in new_batch:
    key = str(rec["id"])
    if key not in existing_records:
        inserts.append(rec)
    elif compute_checksum(rec) != compute_checksum(existing_records[key]):
        updates.append(rec)
    else:
        skips.append(rec)

print("Incremental load analysis:")
print(f"  New records (INSERT): {len(inserts)} → IDs {[r['id'] for r in inserts]}")
print(f"  Changed records (UPDATE): {len(updates)} → IDs {[r['id'] for r in updates]}")
print(f"  Unchanged records (SKIP): {len(skips)} → IDs {[r['id'] for r in skips]}")
print()


# %% [markdown]
# ## Data Lineage: Knowing Your Data's Journey
#
# **Scenario:** An analyst questions a number in a report. Where did it come from?
# What transformations were applied? Without lineage, you can't answer.
#
# **The Cost:** Inability to debug data issues, lost trust in analytics, compliance problems.

# %%
print("=" * 60)
print("DATA LINEAGE")
print("=" * 60)


def add_lineage_metadata(
    record: Dict,
    source: str,
    pipeline: str,
    transformations: List[str],
) -> Dict:
    """
    Enrich record with lineage metadata.
    This answers: Where did this come from? What was done to it?
    """
    return {
        **record,
        "_lineage": {
            "source": source,
            "pipeline": pipeline,
            "transformations_applied": transformations,
            "loaded_at": datetime.now(timezone.utc).isoformat(),
            "source_record_hash": compute_checksum(record),
        },
    }


sample = valid_records[0]
with_lineage = add_lineage_metadata(
    sample,
    source="employees.csv",
    pipeline="employee_etl_v1",
    transformations=["strip_whitespace", "normalize_case", "parse_date", "cast_salary_to_float"],
)
print("Record with lineage metadata:")
print(json.dumps(with_lineage, indent=2, default=str))
print()


# %% [markdown]
# ## Summary: ETL Design Principles
#
# | Principle | Why It Matters |
# |-----------|---------------|
# | **Separation** | Extract, Transform, Load are isolated phases with clear boundaries |
# | **Idempotency** | Re-running produces the same result — safe for retries and debugging |
# | **Fail Fast** | Validate early — bad data caught before it corrupts destination |
# | **Observability** | Log metrics at every stage — know if pipeline succeeded |
# | **Incremental Load** | Process only new/changed data — faster, cheaper, more responsive |
# | **Data Lineage** | Track data's journey — enables debugging, compliance, trust |
#
# Next lesson: Build a complete working ETL pipeline with real CSV data.
