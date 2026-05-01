"""
Module 5 - Lesson 3: ETL Pipeline Orchestration
================================================
An orchestrator manages a pipeline made up of multiple steps.
It handles:
  - Defining step order and dependencies
  - Running steps in sequence
  - Catching and logging errors in individual steps
  - Retrying failed steps
  - Reporting the final status of each step and the overall run

This is a simplified version of what tools like Apache Airflow and Prefect
do at scale. Understanding this pattern makes those tools easier to learn.

Topics covered:
  - Pipeline step abstraction (PipelineStep class)
  - Orchestrator class that manages and runs steps
  - Retry logic with exponential backoff
  - Step dependencies (run step B only if step A succeeded)
  - Status tracking (pending, running, success, failed, skipped)
  - Run summary reporting
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("etl.orchestrator")


# =============================================================================
# STEP STATUS ENUM
# =============================================================================

class StepStatus(Enum):
    """Possible states for a pipeline step."""
    PENDING  = "pending"   # not yet started
    RUNNING  = "running"   # currently executing
    SUCCESS  = "success"   # completed successfully
    FAILED   = "failed"    # failed (all retries exhausted)
    SKIPPED  = "skipped"   # skipped because a dependency failed


# =============================================================================
# PIPELINE STEP
# =============================================================================

@dataclass
class PipelineStep:
    """
    Represents a single step in a pipeline.

    Attributes:
        name: Unique step identifier.
        func: The callable to execute for this step.
        description: Human-readable description.
        depends_on: List of step names that must succeed before this runs.
        max_retries: Number of retry attempts on failure.
        retry_delay: Seconds to wait between retries.
        timeout: Maximum seconds for the step to complete (not enforced here — conceptual).
        on_failure: "fail" stops the pipeline; "continue" marks as failed but continues.
    """
    name: str
    func: Callable
    description: str = ""
    depends_on: List[str] = field(default_factory=list)
    max_retries: int = 0
    retry_delay: float = 1.0
    timeout: Optional[float] = None
    on_failure: str = "fail"   # "fail" or "continue"

    # Runtime state (set by the orchestrator)
    status: StepStatus = field(default=StepStatus.PENDING, init=False)
    result: Any = field(default=None, init=False)
    error: Optional[Exception] = field(default=None, init=False)
    start_time: Optional[float] = field(default=None, init=False)
    end_time: Optional[float] = field(default=None, init=False)
    attempt_count: int = field(default=0, init=False)

    @property
    def duration(self) -> Optional[float]:
        """Return step duration in seconds, or None if not finished."""
        if self.start_time and self.end_time:
            return round(self.end_time - self.start_time, 3)
        return None

    def reset(self):
        """Reset runtime state (useful for re-running)."""
        self.status = StepStatus.PENDING
        self.result = None
        self.error = None
        self.start_time = None
        self.end_time = None
        self.attempt_count = 0


# =============================================================================
# PIPELINE ORCHESTRATOR
# =============================================================================

class PipelineOrchestrator:
    """
    Manages and executes a sequence of PipelineSteps.

    Features:
      - Sequential execution with dependency checking
      - Per-step retry logic with exponential backoff
      - Status tracking per step
      - Detailed run report
    """

    def __init__(self, name: str):
        self.name = name
        self.steps: List[PipelineStep] = []
        self.run_id: str = ""
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.context: Dict[str, Any] = {}  # shared state passed between steps

    def add_step(self, step: PipelineStep) -> "PipelineOrchestrator":
        """Add a step to the pipeline. Returns self for chaining."""
        self.steps.append(step)
        return self

    def _get_step(self, name: str) -> Optional[PipelineStep]:
        """Look up a step by name."""
        return next((s for s in self.steps if s.name == name), None)

    def _dependencies_satisfied(self, step: PipelineStep) -> bool:
        """Return True if all dependencies for this step succeeded."""
        for dep_name in step.depends_on:
            dep = self._get_step(dep_name)
            if dep is None:
                logger.warning(f"Step '{step.name}' depends on '{dep_name}' which doesn't exist")
                return False
            if dep.status != StepStatus.SUCCESS:
                return False
        return True

    def _run_step(self, step: PipelineStep) -> bool:
        """
        Execute a single step with retry logic.

        Args:
            step: The step to execute.

        Returns:
            True if the step succeeded, False if it failed.
        """
        max_attempts = step.max_retries + 1  # +1 for the initial attempt
        step.start_time = time.time()

        for attempt in range(1, max_attempts + 1):
            step.attempt_count = attempt
            step.status = StepStatus.RUNNING

            if attempt > 1:
                # Exponential backoff: wait longer with each retry
                delay = step.retry_delay * (2 ** (attempt - 2))
                logger.info(f"  [RETRY {attempt}/{max_attempts}] Waiting {delay:.1f}s before retry...")
                time.sleep(delay)

            try:
                logger.info(f"  [RUN] '{step.name}'" +
                           (f" (attempt {attempt}/{max_attempts})" if max_attempts > 1 else ""))

                # Execute the step — pass the shared context
                result = step.func(self.context)
                step.result = result

                # Step succeeded
                step.end_time = time.time()
                step.status = StepStatus.SUCCESS
                logger.info(f"  [OK] '{step.name}' completed in {step.duration}s")
                return True

            except Exception as e:
                step.error = e
                if attempt < max_attempts:
                    logger.warning(f"  [RETRY] '{step.name}' failed (attempt {attempt}): {e}")
                else:
                    step.end_time = time.time()
                    step.status = StepStatus.FAILED
                    logger.error(f"  [FAIL] '{step.name}' failed after {max_attempts} attempt(s): {e}",
                                exc_info=True)
                    return False

        return False  # should not reach here

    def run(self) -> bool:
        """
        Execute all pipeline steps in order.

        Returns:
            True if all non-optional steps succeeded, False otherwise.
        """
        self.run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self.start_time = time.time()

        logger.info("=" * 55)
        logger.info(f"PIPELINE '{self.name}' STARTED | run_id={self.run_id}")
        logger.info(f"Steps: {[s.name for s in self.steps]}")
        logger.info("=" * 55)

        overall_success = True

        for step in self.steps:
            logger.info(f"\n→ Step: {step.name}" +
                       (f" [{step.description}]" if step.description else ""))

            # Check dependencies
            if step.depends_on and not self._dependencies_satisfied(step):
                failed_deps = [
                    d for d in step.depends_on
                    if self._get_step(d) and self._get_step(d).status != StepStatus.SUCCESS
                ]
                logger.warning(f"  [SKIP] '{step.name}' skipped — "
                              f"dependencies not satisfied: {failed_deps}")
                step.status = StepStatus.SKIPPED
                if step.on_failure == "fail":
                    overall_success = False
                continue

            # Run the step
            success = self._run_step(step)

            if not success:
                if step.on_failure == "fail":
                    overall_success = False
                    logger.error(f"Critical step '{step.name}' failed — aborting pipeline")
                    # Mark remaining steps as skipped
                    remaining = self.steps[self.steps.index(step) + 1:]
                    for remaining_step in remaining:
                        remaining_step.status = StepStatus.SKIPPED
                    break
                else:
                    logger.warning(f"Step '{step.name}' failed but on_failure='continue' — proceeding")

        self.end_time = time.time()

        duration = round(self.end_time - self.start_time, 3)
        status_str = "SUCCESS" if overall_success else "FAILED"
        logger.info("=" * 55)
        logger.info(f"PIPELINE '{self.name}' {status_str} | {duration}s")
        logger.info("=" * 55)

        return overall_success

    def get_report(self) -> str:
        """Generate a formatted run report."""
        total_duration = round((self.end_time or time.time()) - (self.start_time or time.time()), 3)
        succeeded = sum(1 for s in self.steps if s.status == StepStatus.SUCCESS)
        failed = sum(1 for s in self.steps if s.status == StepStatus.FAILED)
        skipped = sum(1 for s in self.steps if s.status == StepStatus.SKIPPED)

        lines = [
            "=" * 55,
            f"PIPELINE RUN REPORT: {self.name}",
            f"Run ID:   {self.run_id}",
            f"Duration: {total_duration}s",
            f"Steps:    {succeeded} succeeded, {failed} failed, {skipped} skipped",
            "=" * 55,
        ]
        icons = {
            StepStatus.SUCCESS: "✓",
            StepStatus.FAILED:  "✗",
            StepStatus.SKIPPED: "↷",
            StepStatus.PENDING: "⋯",
            StepStatus.RUNNING: "▶",
        }
        for step in self.steps:
            icon = icons[step.status]
            duration_str = f"{step.duration}s" if step.duration else "—"
            attempts_str = f" [{step.attempt_count} attempt(s)]" if step.attempt_count > 1 else ""
            error_str = f" ERROR: {step.error}" if step.error else ""
            lines.append(
                f"  {icon} {step.name:25s} {step.status.value:8s} "
                f"{duration_str:8s}{attempts_str}{error_str}"
            )
        lines.append("=" * 55)
        return "\n".join(lines)


# =============================================================================
# DEMO: SIMULATED SALES ETL PIPELINE
# =============================================================================

def build_sales_pipeline() -> PipelineOrchestrator:
    """
    Build a sample sales ETL pipeline with 6 steps.
    The steps demonstrate dependencies and retry logic.
    """
    pipeline = PipelineOrchestrator("sales_etl")

    # --- Step functions ---
    # Each function receives 'context' (a shared dict) and can read/write it

    def check_source(ctx: dict) -> dict:
        """Verify the source data file exists and is readable."""
        from pathlib import Path
        source = Path(__file__).parent.parent / "module_4_etl_pipelines" / "data" / "raw_sales.csv"
        if not source.exists():
            raise FileNotFoundError(f"Source not found: {source}")
        ctx["source_path"] = str(source)
        logger.info(f"    Source verified: {source.name}")
        return {"source": str(source)}

    def extract_data(ctx: dict) -> dict:
        """Extract raw data from source CSV."""
        import pandas as pd
        from pathlib import Path
        path = Path(ctx.get("source_path", ""))
        df = pd.read_csv(path, dtype=str)
        ctx["raw_df"] = df
        ctx["extracted_rows"] = len(df)
        logger.info(f"    Extracted {len(df)} rows")
        return {"rows": len(df)}

    def validate_schema(ctx: dict) -> dict:
        """Check that required columns are present."""
        df = ctx["raw_df"]
        required = {"id", "sale_date", "product_name", "qty", "price"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        logger.info(f"    Schema valid — all {len(required)} required columns present")
        return {"columns_validated": len(df.columns)}

    _transform_call_count = [0]  # mutable container for closure

    def transform_data(ctx: dict) -> dict:
        """Clean and transform the raw data."""
        import pandas as pd
        import numpy as np
        _transform_call_count[0] += 1

        # Simulate a flaky step that fails once
        if _transform_call_count[0] == 1:
            raise RuntimeError("Transient error in transform (will succeed on retry)")

        df = ctx["raw_df"].copy()
        df["qty"] = pd.to_numeric(df["qty"], errors="coerce").fillna(1).astype(int)
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
        df = df.dropna(subset=["price"])
        df = df[df["price"] > 0]
        df["net_amount"] = (df["qty"] * df["price"]).round(2)
        ctx["clean_df"] = df
        ctx["clean_rows"] = len(df)
        logger.info(f"    Transformed: {len(df)} valid rows")
        return {"rows": len(df)}

    def load_to_db(ctx: dict) -> dict:
        """Load clean data to SQLite."""
        from sqlalchemy import create_engine
        from pathlib import Path
        db_path = Path(__file__).parent / "orchestration_output.db"
        engine = create_engine(f"sqlite:///{db_path}")
        df = ctx["clean_df"]
        df.to_sql("sales", con=engine, if_exists="replace", index=False)
        engine.dispose()
        ctx["db_path"] = str(db_path)
        logger.info(f"    Loaded {len(df)} rows to {db_path.name}")
        return {"rows_loaded": len(df)}

    def send_notification(ctx: dict) -> dict:
        """Simulate sending a completion notification."""
        clean_rows = ctx.get("clean_rows", 0)
        extracted_rows = ctx.get("extracted_rows", 0)
        logger.info(f"    [NOTIFY] Pipeline complete: {clean_rows}/{extracted_rows} rows loaded")
        return {"notified": True}

    # --- Build the pipeline ---
    pipeline.add_step(PipelineStep(
        name="check_source",
        func=check_source,
        description="Verify source file exists",
        on_failure="fail"
    ))
    pipeline.add_step(PipelineStep(
        name="extract",
        func=extract_data,
        description="Read CSV into DataFrame",
        depends_on=["check_source"],
        on_failure="fail"
    ))
    pipeline.add_step(PipelineStep(
        name="validate_schema",
        func=validate_schema,
        description="Verify required columns",
        depends_on=["extract"],
        on_failure="fail"
    ))
    pipeline.add_step(PipelineStep(
        name="transform",
        func=transform_data,
        description="Clean and compute columns",
        depends_on=["validate_schema"],
        max_retries=2,          # retry up to 2 times
        retry_delay=0.1,        # wait 0.1s before retry
        on_failure="fail"
    ))
    pipeline.add_step(PipelineStep(
        name="load",
        func=load_to_db,
        description="Write to SQLite",
        depends_on=["transform"],
        on_failure="fail"
    ))
    pipeline.add_step(PipelineStep(
        name="notify",
        func=send_notification,
        description="Send completion notification",
        depends_on=["load"],
        on_failure="continue"   # failure here doesn't fail the pipeline
    ))

    return pipeline


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("DEMO: ETL Pipeline Orchestration")
    print("=" * 55)

    # Build and run the pipeline
    pipeline = build_sales_pipeline()
    success = pipeline.run()

    # Print the report
    print("\n" + pipeline.get_report())

    if success:
        # Verify the output
        import pandas as pd
        from pathlib import Path
        from sqlalchemy import create_engine
        db_path = Path(__file__).parent / "orchestration_output.db"
        if db_path.exists():
            engine = create_engine(f"sqlite:///{db_path}")
            result = pd.read_sql("SELECT region, COUNT(*) AS orders, ROUND(SUM(net_amount),2) AS revenue FROM sales GROUP BY region", con=engine)
            print("Revenue by region (from orchestrated pipeline):")
            print(result.to_string())
            engine.dispose()
            db_path.unlink()
            print(f"\nCleaned up {db_path.name}")
