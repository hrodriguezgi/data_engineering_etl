"""
Tests for Module 5: Automation Components
==========================================
Tests cover automation utilities taught in module_5_automation:
  - Orchestrator (step execution, dependencies, retries, status tracking)
  - Config loading, validation, and merging
  - Logging setup
  - Schedule-based job wrapping (safe job wrapper)
"""

import json
import logging
import sys
import time
import pytest
import pandas as pd
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch, call

# Reference to module 5
MODULE5_DIR = Path(__file__).parent.parent / "module_5_automation"
CONFIG_DIR = MODULE5_DIR / "config"


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def pipeline_config():
    """Load the sample pipeline config."""
    with open(CONFIG_DIR / "pipeline_config.json") as f:
        return json.load(f)


@pytest.fixture
def minimal_config():
    """A minimal valid pipeline configuration dict."""
    return {
        "pipeline_name": "test_pipeline",
        "version": "1.0",
        "source": {
            "type": "csv",
            "path": "data/test.csv",
            "encoding": "utf-8",
        },
        "transformations": [],
        "destination": {
            "type": "sqlite",
            "database": "test.db",
            "table": "test_table",
            "if_exists": "replace",
        },
    }


# =============================================================================
# ORCHESTRATOR TESTS
# =============================================================================

class TestOrchestrator:
    """Tests for the PipelineOrchestrator class."""

    def _make_orchestrator(self):
        """Import and instantiate the orchestrator."""
        sys.path.insert(0, str(MODULE5_DIR))
        from module_5_automation.etl_orchestration_helpers import (
            PipelineOrchestrator, PipelineStep, StepStatus
        )
        return PipelineOrchestrator, PipelineStep, StepStatus

    def test_step_success_changes_status(self):
        """A successful step should have status SUCCESS."""
        sys.path.insert(0, str(Path(__file__).parent.parent))
        try:
            from module_5_automation.etl_orchestration_helpers import (
                PipelineOrchestrator, PipelineStep, StepStatus
            )
        except ImportError:
            pytest.skip("Orchestration helpers not available as importable module")

        def my_step(ctx):
            return {"done": True}

        pipeline = PipelineOrchestrator("test")
        pipeline.add_step(PipelineStep(name="step1", func=my_step))
        pipeline.run()
        assert pipeline.steps[0].status == StepStatus.SUCCESS

    def test_step_failure_changes_status(self):
        """A failing step should have status FAILED."""
        sys.path.insert(0, str(Path(__file__).parent.parent))
        try:
            from module_5_automation.etl_orchestration_helpers import (
                PipelineOrchestrator, PipelineStep, StepStatus
            )
        except ImportError:
            pytest.skip("Orchestration helpers not available as importable module")

        def failing_step(ctx):
            raise RuntimeError("Intentional failure")

        pipeline = PipelineOrchestrator("test")
        pipeline.add_step(PipelineStep(name="step1", func=failing_step, on_failure="continue"))
        pipeline.run()
        assert pipeline.steps[0].status == StepStatus.FAILED
        assert pipeline.steps[0].error is not None

    def test_dependent_step_skipped_when_dependency_fails(self):
        """A step should be SKIPPED if its dependency failed."""
        sys.path.insert(0, str(Path(__file__).parent.parent))
        try:
            from module_5_automation.etl_orchestration_helpers import (
                PipelineOrchestrator, PipelineStep, StepStatus
            )
        except ImportError:
            pytest.skip("Orchestration helpers not available as importable module")

        def failing(ctx):
            raise ValueError("step 1 fails")

        def dependent(ctx):
            return {"ok": True}

        pipeline = PipelineOrchestrator("test")
        pipeline.add_step(PipelineStep(name="step1", func=failing, on_failure="continue"))
        pipeline.add_step(PipelineStep(name="step2", func=dependent, depends_on=["step1"]))
        pipeline.run()

        assert pipeline.steps[0].status == StepStatus.FAILED
        assert pipeline.steps[1].status == StepStatus.SKIPPED


# =============================================================================
# ORCHESTRATOR LOGIC TESTS (Pure Logic, No Import Needed)
# =============================================================================

class TestOrchestratorLogic:
    """Tests for orchestrator logic using inline implementations."""

    def test_retry_succeeds_on_second_attempt(self):
        """A step that fails once but succeeds on retry should show SUCCESS."""
        call_count = [0]

        def flaky_func(ctx):
            call_count[0] += 1
            if call_count[0] < 2:
                raise ConnectionError("Transient error")
            return {"ok": True}

        # Simulate retry logic
        max_retries = 2
        last_error = None
        result = None
        for attempt in range(1, max_retries + 1):
            try:
                result = flaky_func({})
                break
            except Exception as e:
                last_error = e

        assert result == {"ok": True}
        assert call_count[0] == 2

    def test_retry_exhausted_raises(self):
        """Exhausting all retries should propagate the last exception."""
        def always_fails(ctx):
            raise RuntimeError("Always fails")

        max_retries = 3
        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                always_fails({})
            except Exception as e:
                last_error = e

        assert isinstance(last_error, RuntimeError)
        assert str(last_error) == "Always fails"

    def test_exponential_backoff_increases_delay(self):
        """Exponential backoff delays should increase with each attempt."""
        base_delay = 0.1
        delays = [base_delay * (2 ** attempt) for attempt in range(4)]
        for i in range(1, len(delays)):
            assert delays[i] > delays[i - 1]

    def test_context_dict_passed_between_steps(self):
        """Steps should be able to read and write to a shared context dict."""
        context = {}

        def step1(ctx):
            ctx["result_from_step1"] = 42

        def step2(ctx):
            assert "result_from_step1" in ctx
            ctx["result_from_step2"] = ctx["result_from_step1"] * 2

        step1(context)
        step2(context)

        assert context["result_from_step1"] == 42
        assert context["result_from_step2"] == 84

    def test_step_duration_calculation(self):
        """Step duration should be correctly calculated."""
        start = time.time()
        time.sleep(0.01)
        end = time.time()
        duration = round(end - start, 3)
        assert 0.005 <= duration <= 0.5  # Should be ~10ms


# =============================================================================
# CONFIG LOADING TESTS
# =============================================================================

class TestConfigLoading:
    """Tests for pipeline configuration loading and validation."""

    def test_config_file_loads(self, pipeline_config):
        """Pipeline config file should load without errors."""
        assert isinstance(pipeline_config, dict)
        assert "pipeline_name" in pipeline_config

    def test_config_has_required_keys(self, pipeline_config):
        """Config should have all required top-level keys."""
        required = ["pipeline_name", "source", "destination", "transformations"]
        for key in required:
            assert key in pipeline_config, f"Missing required key: {key}"

    def test_config_source_has_type_and_path(self, pipeline_config):
        """Source config should have type and path."""
        source = pipeline_config["source"]
        assert "type" in source
        assert "path" in source

    def test_config_destination_has_required_fields(self, pipeline_config):
        """Destination config should have type, database, and table."""
        dest = pipeline_config["destination"]
        assert "type" in dest
        assert "database" in dest
        assert "table" in dest

    def test_config_transformations_is_list(self, pipeline_config):
        """Transformations should be a list."""
        assert isinstance(pipeline_config["transformations"], list)

    def test_config_validation_detects_missing_key(self, minimal_config):
        """Removing a required key should be detectable."""
        config = minimal_config.copy()
        del config["source"]
        required_keys = ["pipeline_name", "source", "destination", "transformations"]
        missing = [k for k in required_keys if k not in config]
        assert "source" in missing

    def test_config_env_override_logic(self, minimal_config):
        """Environment variable override logic should update config values."""
        import os
        import copy

        os.environ["ETL_TEST_DEST_DB"] = "override.db"
        config = copy.deepcopy(minimal_config)

        # Apply override logic
        env_val = os.environ.get("ETL_TEST_DEST_DB")
        if env_val:
            config["destination"]["database"] = env_val

        assert config["destination"]["database"] == "override.db"
        del os.environ["ETL_TEST_DEST_DB"]

    def test_config_merge_overrides_correctly(self):
        """Config merge should give later configs priority."""
        base = {"name": "base", "level": "INFO", "db": {"host": "localhost", "port": 5432}}
        override = {"name": "override", "db": {"host": "prod.server.com"}}

        import copy

        def deep_merge(b, o):
            result = copy.deepcopy(b)
            for key, value in o.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = copy.deepcopy(value)
            return result

        merged = deep_merge(base, override)
        assert merged["name"] == "override"        # overridden
        assert merged["level"] == "INFO"           # kept from base
        assert merged["db"]["host"] == "prod.server.com"  # nested override
        assert merged["db"]["port"] == 5432        # nested base preserved

    def test_config_schedule_section(self, pipeline_config):
        """Schedule section should have expected fields."""
        if "schedule" in pipeline_config:
            schedule = pipeline_config["schedule"]
            assert "interval" in schedule
            assert "max_retries" in schedule

    def test_config_transformations_have_step_field(self, pipeline_config):
        """Each transformation step should have a 'step' field."""
        for step in pipeline_config["transformations"]:
            assert "step" in step, f"Transformation missing 'step' field: {step}"


# =============================================================================
# LOGGING TESTS
# =============================================================================

class TestLoggingSetup:
    """Tests for logging configuration."""

    def test_logger_is_configured(self):
        """Logger should be configurable with handlers."""
        logger = logging.getLogger("test.etl.lesson5")
        handler = logging.StreamHandler(StringIO())
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        logger.info("Test message")
        # If no exception, logger is working
        assert True

    def test_log_levels_are_ordered(self):
        """Log levels should be in the correct numerical order."""
        assert logging.DEBUG < logging.INFO
        assert logging.INFO < logging.WARNING
        assert logging.WARNING < logging.ERROR
        assert logging.ERROR < logging.CRITICAL

    def test_rotating_file_handler_creates_file(self, tmp_path):
        """RotatingFileHandler should create a log file."""
        log_file = tmp_path / "test.log"
        handler = logging.handlers.RotatingFileHandler(
            str(log_file),
            maxBytes=1024,
            backupCount=2
        )
        logger = logging.getLogger("test.rotation")
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        logger.info("Test message")
        handler.close()
        assert log_file.exists()

    def test_log_formatter_includes_timestamp(self):
        """Log formatter should include timestamp in output."""
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d"
        ))
        logger = logging.getLogger("test.formatter")
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        logger.info("test message")
        output = stream.getvalue()
        from datetime import datetime
        current_year = str(datetime.now().year)
        assert current_year in output  # year in timestamp


# =============================================================================
# SAFE JOB WRAPPER TESTS
# =============================================================================

class TestSafeJobWrapper:
    """Tests for the safe job wrapper pattern (from lesson 1)."""

    def _make_safe_wrapper(self, func, name=None):
        """Inline implementation of safe_wrapper for testing."""
        import functools
        job_name = name or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logging.getLogger("test.safe_wrapper").error(
                    f"Job '{job_name}' failed: {e}"
                )
                return None
        return wrapper

    def test_successful_job_returns_result(self):
        """Safe wrapper should return the function's result on success."""
        def good_job():
            return {"status": "ok", "rows": 42}

        wrapped = self._make_safe_wrapper(good_job)
        result = wrapped()
        assert result == {"status": "ok", "rows": 42}

    def test_failing_job_returns_none_not_raises(self):
        """Safe wrapper should catch exceptions and return None."""
        def bad_job():
            raise ValueError("Something went wrong")

        wrapped = self._make_safe_wrapper(bad_job)
        result = wrapped()
        assert result is None  # exception caught, not raised

    def test_safe_wrapper_preserves_function_name(self):
        """Safe wrapper should preserve the original function name."""
        def my_etl_job():
            pass

        wrapped = self._make_safe_wrapper(my_etl_job)
        assert wrapped.__name__ == "my_etl_job"

    def test_safe_wrapper_passes_arguments(self):
        """Safe wrapper should pass args and kwargs to the wrapped function."""
        received = {}

        def job_with_args(source, limit=100):
            received["source"] = source
            received["limit"] = limit
            return True

        wrapped = self._make_safe_wrapper(job_with_args)
        wrapped("customers.csv", limit=50)
        assert received["source"] == "customers.csv"
        assert received["limit"] == 50

    def test_multiple_safe_jobs_are_independent(self):
        """Failure of one safe job should not affect other jobs."""
        call_log = []

        def job_a():
            raise RuntimeError("job_a fails")

        def job_b():
            call_log.append("job_b ran")
            return True

        safe_a = self._make_safe_wrapper(job_a)
        safe_b = self._make_safe_wrapper(job_b)

        safe_a()  # should not raise
        safe_b()  # should still run

        assert "job_b ran" in call_log


# Import for rotating file handler test
import logging.handlers
