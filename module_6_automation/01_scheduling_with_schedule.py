"""
Module 6 - Lesson 1: Scheduling ETL Jobs with `schedule`
==========================================================
The `schedule` library provides a simple, human-readable API for running
functions on a schedule — without needing cron, Airflow, or any other
external tool.

It's perfect for:
  - Simple recurring jobs (hourly syncs, daily reports)
  - Development and testing of scheduled pipelines
  - Lightweight automation on a single machine

Topics covered:
  - Installing and using the `schedule` library
  - Scheduling jobs at various intervals
  - Running the scheduler in a daemon loop
  - Graceful shutdown with signal handling
  - Combining schedule with logging
  - Thread-safe scheduling

NOTE: This script runs an infinite loop when executed as __main__.
      Press Ctrl+C to stop it. The demo at the bottom also shows
      a bounded loop that runs for a fixed number of iterations.
"""

import logging
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import schedule

# Set up logging for the scheduler
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("etl.scheduler")

# Track whether we should keep running
_running = True


# =============================================================================
# SIMULATED ETL FUNCTIONS
# =============================================================================

def extract_sales_data() -> dict:
    """Simulate extracting sales data from a source."""
    logger.info("[EXTRACT] Reading sales data from source...")
    time.sleep(0.1)  # simulate work
    return {"rows": 42, "source": "sales.csv"}

def sync_inventory() -> dict:
    """Simulate syncing inventory data."""
    logger.info("[SYNC] Syncing inventory data...")
    time.sleep(0.05)
    return {"items_updated": 15}

def generate_daily_report() -> None:
    """Simulate generating a daily summary report."""
    logger.info("[REPORT] Generating daily sales report...")
    time.sleep(0.2)
    logger.info("[REPORT] Daily report complete.")

def health_check() -> bool:
    """Check that all pipeline dependencies are available."""
    logger.debug("[HEALTH] Checking pipeline health...")
    # In production: check DB connection, API reachability, disk space, etc.
    return True


# =============================================================================
# 1. BASIC SCHEDULING
# =============================================================================

print("=" * 60)
print("1. SCHEDULE LIBRARY BASICS")
print("=" * 60)

# The schedule library uses a builder pattern to define jobs.
# A "job" = a function to call + when to call it.

# Schedule reference (NOT running these yet — just showing syntax):
print("Available schedule intervals:")
print("  schedule.every(10).seconds.do(func)")
print("  schedule.every(5).minutes.do(func)")
print("  schedule.every().hour.do(func)")
print("  schedule.every().day.at('09:30').do(func)")
print("  schedule.every().monday.at('08:00').do(func)")
print("  schedule.every().week.do(func)")
print("  schedule.every(2).hours.do(func)")


# =============================================================================
# 2. JOB WITH ARGUMENTS
# =============================================================================

print("\n" + "=" * 60)
print("2. JOBS WITH ARGUMENTS")
print("=" * 60)

def etl_job(pipeline_name: str, source: str, dry_run: bool = False) -> None:
    """
    Generic ETL job that can be scheduled with different parameters.

    Args:
        pipeline_name: Name for logging.
        source: Data source identifier.
        dry_run: If True, just logs what it would do.
    """
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    if dry_run:
        logger.info(f"[{pipeline_name}] DRY RUN at {ts} — would process '{source}'")
    else:
        logger.info(f"[{pipeline_name}] RUNNING at {ts}")
        result = extract_sales_data()
        logger.info(f"[{pipeline_name}] Processed {result['rows']} rows from {result['source']}")

# Schedule with specific arguments using do(func, *args, **kwargs)
schedule.every(30).seconds.do(etl_job, "sales_pipeline", "sales.csv", dry_run=True)
schedule.every(45).seconds.do(etl_job, "inventory_sync", "inventory.csv")

print("Scheduled jobs:")
for job in schedule.jobs:
    print(f"  {job}")


# =============================================================================
# 3. JOBS WITH ERROR HANDLING
# =============================================================================

print("\n" + "=" * 60)
print("3. ROBUST JOB WITH ERROR HANDLING")
print("=" * 60)

def make_safe_job(func: Callable, job_name: str = None) -> Callable:
    """
    Wrap any function to make it safe for scheduling:
      - Catches and logs exceptions so the scheduler keeps running
      - Logs start/end times and duration
      - Reports success/failure

    Args:
        func: The function to wrap.
        job_name: Name for logging (defaults to func.__name__).

    Returns:
        Wrapped function.
    """
    name = job_name or func.__name__

    def safe_wrapper(*args, **kwargs):
        start = time.time()
        logger.info(f"[JOB] Starting '{name}'")
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start
            logger.info(f"[JOB] '{name}' completed in {elapsed:.2f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start
            logger.error(f"[JOB] '{name}' FAILED after {elapsed:.2f}s: {e}", exc_info=True)
            # Returning None keeps the scheduler running (don't re-raise!)
            return None

    safe_wrapper.__name__ = name
    return safe_wrapper

# Create a flaky function that sometimes fails
_call_count = 0
def flaky_extraction():
    """A function that fails every other call — simulates transient failures."""
    global _call_count
    _call_count += 1
    if _call_count % 2 == 0:
        raise ConnectionError("Database connection lost!")
    return {"rows_extracted": 100}

# Wrap it to make it safe for scheduling
safe_extraction = make_safe_job(flaky_extraction, "db_extraction")

# Test the wrapper directly
print("Testing safe_wrapper (should handle the error on call 2):")
for i in range(3):
    result = safe_extraction()
    print(f"  Call {i+1}: result = {result}")


# =============================================================================
# 4. CANCELLING AND MANAGING JOBS
# =============================================================================

print("\n" + "=" * 60)
print("4. MANAGING SCHEDULED JOBS")
print("=" * 60)

# Clear all existing jobs first
schedule.clear()

# Schedule new jobs
hourly_job = schedule.every().hour.do(generate_daily_report)
health_job = schedule.every(30).seconds.do(make_safe_job(health_check, "health_check"))
report_job = schedule.every().day.at("09:00").do(generate_daily_report)

print(f"Total scheduled jobs: {len(schedule.jobs)}")
for job in schedule.jobs:
    print(f"  {job}")

# Cancel a specific job
schedule.cancel_job(hourly_job)
print(f"\nAfter cancelling hourly_job: {len(schedule.jobs)} jobs")

# Tag jobs for bulk management
schedule.clear()  # reset

schedule.every(10).seconds.do(etl_job, "sales", "sales.csv").tag("etl", "sales")
schedule.every(30).seconds.do(etl_job, "inventory", "inv.csv").tag("etl", "inventory")
schedule.every(60).seconds.do(health_check).tag("monitoring")

print("\nJobs by tag:")
etl_jobs = schedule.get_jobs("etl")
print(f"  'etl' tag: {len(etl_jobs)} jobs")
monitoring_jobs = schedule.get_jobs("monitoring")
print(f"  'monitoring' tag: {len(monitoring_jobs)} jobs")

# Cancel all jobs with a specific tag
schedule.clear("monitoring")
print(f"\nAfter clearing 'monitoring' tag: {len(schedule.jobs)} jobs remain")


# =============================================================================
# 5. GRACEFUL SHUTDOWN
# =============================================================================

print("\n" + "=" * 60)
print("5. GRACEFUL SHUTDOWN (Signal Handling)")
print("=" * 60)

def handle_shutdown(signum, frame):
    """
    Handle Ctrl+C (SIGINT) or kill signal (SIGTERM) gracefully.
    Sets the global flag to stop the scheduler loop.
    """
    global _running
    logger.info(f"\nReceived signal {signum}. Shutting down gracefully...")
    _running = False

# Register signal handlers
signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

print("Signal handlers registered for SIGINT (Ctrl+C) and SIGTERM")


# =============================================================================
# 6. THE SCHEDULER LOOP
# =============================================================================

print("\n" + "=" * 60)
print("6. SCHEDULER LOOP PATTERN")
print("=" * 60)

def run_scheduler(tick_interval: float = 1.0) -> None:
    """
    Start the main scheduler loop.

    Continuously runs pending jobs and sleeps between checks.
    Respects the _running flag for graceful shutdown.

    Args:
        tick_interval: Seconds to sleep between checks (default 1.0).
    """
    logger.info(f"Scheduler started with {len(schedule.jobs)} jobs")
    logger.info("Press Ctrl+C to stop.")

    while _running:
        schedule.run_pending()
        time.sleep(tick_interval)

    logger.info("Scheduler stopped cleanly.")


# =============================================================================
# MAIN DEMO (bounded loop — runs for a few iterations then stops)
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("DEMO: Bounded Scheduler Loop (5 ticks)")
    print("=" * 60)

    # Clear and set up a fresh schedule
    schedule.clear()
    _running = True

    tick_count = 0
    MAX_TICKS = 5

    # Schedule a very frequent job for demo purposes
    def demo_job(name: str):
        logger.info(f"[DEMO] Running '{name}' job (tick {tick_count})")

    schedule.every(1).seconds.do(demo_job, "quick_task")
    schedule.every(3).seconds.do(demo_job, "slow_task")

    logger.info("Starting bounded demo loop (5 ticks, 1s each)...")
    while tick_count < MAX_TICKS:
        schedule.run_pending()
        time.sleep(1.0)
        tick_count += 1
        logger.debug(f"Tick {tick_count}/{MAX_TICKS}")

    logger.info("Demo complete.")
    schedule.clear()

    print("\nTo run as a real scheduler (infinite loop), uncomment:")
    print("  run_scheduler(tick_interval=1.0)")
    print("\nOr run with cron (in production, prefer cron or Airflow):")
    print("  */5 * * * * python 01_scheduling_with_schedule.py --run-once")
