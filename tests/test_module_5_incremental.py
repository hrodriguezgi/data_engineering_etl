"""
Tests for Module 5: Incremental Load Patterns

Tests cover the incremental load utilities taught in module_5_incremental_loads:
  - Watermark-based extraction (01_watermark_based_extraction.py)
  - Upsert patterns (02_upsert_patterns.py)
  - SCD Type 1 and Type 2 (03_scd_type1_type2.py)
  - Full incremental pipeline (04_incremental_pipeline.py)
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd
import pytest
from sqlalchemy import create_engine, text

# ---------------------------------------------------------------------------
# Make module importable
# ---------------------------------------------------------------------------
MODULE_DIR = Path(__file__).parent.parent / "module_5_incremental_loads"
sys.path.insert(0, str(MODULE_DIR.parent))


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mem_engine():
    """In-memory SQLite engine — isolated per test, no files written."""
    return create_engine("sqlite:///:memory:", echo=False)


@pytest.fixture
def watermark_engine(mem_engine):
    """Engine with source + pipeline_state tables pre-created."""
    from module_5_incremental_loads.watermark_helpers import (
        setup_source_table_from_df,
        setup_state_table,
    )
    orders = pd.DataFrame([
        {"order_id": 1, "customer_id": "C001", "product": "Laptop",   "amount": 1200.0, "status": "completed", "created_at": "2024-01-01 08:00:00", "updated_at": "2024-01-01 08:00:00"},
        {"order_id": 2, "customer_id": "C002", "product": "Mouse",    "amount":   25.0, "status": "pending",   "created_at": "2024-01-02 09:00:00", "updated_at": "2024-01-02 09:00:00"},
        {"order_id": 3, "customer_id": "C003", "product": "Keyboard", "amount":   75.0, "status": "completed", "created_at": "2024-01-03 10:00:00", "updated_at": "2024-01-03 10:00:00"},
    ])
    setup_source_table_from_df(mem_engine, orders)
    setup_state_table(mem_engine)
    return mem_engine


@pytest.fixture
def upsert_engine(mem_engine):
    """Engine with a clean orders table ready for upsert tests."""
    with mem_engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE orders (
                order_id    INTEGER PRIMARY KEY,
                customer_id TEXT NOT NULL,
                product     TEXT NOT NULL,
                amount      REAL NOT NULL,
                status      TEXT NOT NULL,
                updated_at  TEXT NOT NULL
            )
        """))
    return mem_engine


@pytest.fixture
def scd_engine(mem_engine):
    """Engine with SCD1 and SCD2 tables pre-created."""
    from module_5_incremental_loads.scd_helpers import setup_scd1_table, setup_scd2_table
    setup_scd1_table(mem_engine)
    setup_scd2_table(mem_engine)
    return mem_engine


@pytest.fixture
def pipeline_engine(mem_engine):
    """Engine with all pipeline tables (source, target, state, log) pre-created."""
    from module_5_incremental_loads.pipeline_helpers import setup_all_tables, seed_source_from_df
    orders = pd.DataFrame([
        {"order_id": 1, "customer_id": "C001", "product": "Laptop",   "amount": 1200.0, "status": "completed", "created_at": "2024-01-01 08:00:00", "updated_at": "2024-01-01 08:00:00"},
        {"order_id": 2, "customer_id": "C002", "product": "Mouse",    "amount":   25.0, "status": "PENDING",   "created_at": "2024-01-02 09:00:00", "updated_at": "2024-01-02 09:00:00"},
        {"order_id": 3, "customer_id": "C003", "product": "Keyboard", "amount":   75.0, "status": "Completed", "created_at": "2024-01-03 10:00:00", "updated_at": "2024-01-03 10:00:00"},
    ])
    setup_all_tables(mem_engine)
    seed_source_from_df(mem_engine, orders)
    return mem_engine


# =============================================================================
# WATERMARK TESTS
# =============================================================================

class TestWatermark:

    def test_get_watermark_returns_none_on_first_run(self, watermark_engine):
        from module_5_incremental_loads.watermark_helpers import get_watermark
        assert get_watermark(watermark_engine, "test_pipeline") is None

    def test_save_and_get_watermark(self, watermark_engine):
        from module_5_incremental_loads.watermark_helpers import get_watermark, save_watermark
        save_watermark(watermark_engine, "test_pipeline", "updated_at", "2024-01-03 10:00:00", 3)
        result = get_watermark(watermark_engine, "test_pipeline")
        assert result == "2024-01-03 10:00:00"

    def test_save_watermark_is_idempotent(self, watermark_engine):
        """Calling save_watermark twice with the same value must not raise or duplicate."""
        from module_5_incremental_loads.watermark_helpers import get_watermark, save_watermark
        save_watermark(watermark_engine, "test_pipeline", "updated_at", "2024-01-03 10:00:00", 3)
        save_watermark(watermark_engine, "test_pipeline", "updated_at", "2024-01-03 10:00:00", 3)
        result = get_watermark(watermark_engine, "test_pipeline")
        assert result == "2024-01-03 10:00:00"

    def test_watermark_advances_on_second_save(self, watermark_engine):
        from module_5_incremental_loads.watermark_helpers import get_watermark, save_watermark
        save_watermark(watermark_engine, "test_pipeline", "updated_at", "2024-01-02 09:00:00", 2)
        save_watermark(watermark_engine, "test_pipeline", "updated_at", "2024-01-03 10:00:00", 1)
        assert get_watermark(watermark_engine, "test_pipeline") == "2024-01-03 10:00:00"

    def test_first_run_extracts_all_rows(self, watermark_engine):
        from module_5_incremental_loads.watermark_helpers import extract_incremental
        df = extract_incremental(watermark_engine, "test_pipeline", "updated_at", "source_orders")
        assert len(df) == 3

    def test_incremental_run_extracts_only_new_rows(self, watermark_engine):
        from module_5_incremental_loads.watermark_helpers import extract_incremental, save_watermark
        # Save a watermark at the first row's timestamp
        save_watermark(watermark_engine, "test_pipeline", "updated_at", "2024-01-01 08:00:00", 1)
        df = extract_incremental(watermark_engine, "test_pipeline", "updated_at", "source_orders")
        # Should get rows 2 and 3 (updated_at > 2024-01-01 08:00:00, minus lookback buffer)
        assert len(df) >= 2
        assert 1 not in df["order_id"].values  # row 1 should NOT be re-extracted

    def test_no_new_rows_returns_empty_dataframe(self, watermark_engine):
        from module_5_incremental_loads.watermark_helpers import extract_incremental, save_watermark
        # Set watermark beyond all existing data
        save_watermark(watermark_engine, "test_pipeline", "updated_at", "2099-01-01 00:00:00", 3)
        df = extract_incremental(watermark_engine, "test_pipeline", "updated_at", "source_orders")
        assert df.empty


# =============================================================================
# UPSERT TESTS
# =============================================================================

EXISTING = [
    {"order_id": 1, "customer_id": "C001", "product": "Laptop",   "amount": 1200.0, "status": "pending",   "updated_at": "2024-01-01 08:00:00"},
    {"order_id": 2, "customer_id": "C002", "product": "Mouse",    "amount":   25.0, "status": "completed", "updated_at": "2024-01-01 09:00:00"},
]
INCOMING = [
    {"order_id": 2, "customer_id": "C002", "product": "Mouse",    "amount":   25.0, "status": "completed", "updated_at": "2024-01-01 09:00:00"},  # unchanged
    {"order_id": 3, "customer_id": "C003", "product": "Keyboard", "amount":   75.0, "status": "pending",   "updated_at": "2024-01-02 10:00:00"},  # new
    {"order_id": 1, "customer_id": "C001", "product": "Laptop",   "amount": 1200.0, "status": "completed", "updated_at": "2024-01-03 12:00:00"},  # updated
]


class TestInsertOrIgnore:

    def _seed(self, engine):
        pd.DataFrame(EXISTING).to_sql("orders", con=engine, if_exists="append", index=False)

    def test_inserts_new_rows(self, upsert_engine):
        from module_5_incremental_loads.upsert_helpers import load_insert_or_ignore
        self._seed(upsert_engine)
        load_insert_or_ignore(upsert_engine, "orders", pd.DataFrame(INCOMING))
        count = pd.read_sql("SELECT COUNT(*) AS c FROM orders", con=upsert_engine).iloc[0]["c"]
        assert count == 3  # row 3 was new

    def test_does_not_overwrite_existing_rows(self, upsert_engine):
        from module_5_incremental_loads.upsert_helpers import load_insert_or_ignore
        self._seed(upsert_engine)
        load_insert_or_ignore(upsert_engine, "orders", pd.DataFrame(INCOMING))
        row = pd.read_sql("SELECT status FROM orders WHERE order_id=1", con=upsert_engine)
        assert row.iloc[0]["status"] == "pending"  # original value preserved

    def test_idempotent(self, upsert_engine):
        from module_5_incremental_loads.upsert_helpers import load_insert_or_ignore
        self._seed(upsert_engine)
        df = pd.DataFrame(INCOMING)
        load_insert_or_ignore(upsert_engine, "orders", df)
        load_insert_or_ignore(upsert_engine, "orders", df)
        count = pd.read_sql("SELECT COUNT(*) AS c FROM orders", con=upsert_engine).iloc[0]["c"]
        assert count == 3  # running twice must not duplicate


class TestInsertOrReplace:

    def _seed(self, engine):
        pd.DataFrame(EXISTING).to_sql("orders", con=engine, if_exists="append", index=False)

    def test_overwrites_existing_rows(self, upsert_engine):
        from module_5_incremental_loads.upsert_helpers import load_insert_or_replace
        self._seed(upsert_engine)
        load_insert_or_replace(upsert_engine, "orders", pd.DataFrame(INCOMING))
        row = pd.read_sql("SELECT status FROM orders WHERE order_id=1", con=upsert_engine)
        assert row.iloc[0]["status"] == "completed"  # updated

    def test_inserts_new_rows(self, upsert_engine):
        from module_5_incremental_loads.upsert_helpers import load_insert_or_replace
        self._seed(upsert_engine)
        load_insert_or_replace(upsert_engine, "orders", pd.DataFrame(INCOMING))
        count = pd.read_sql("SELECT COUNT(*) AS c FROM orders", con=upsert_engine).iloc[0]["c"]
        assert count == 3

    def test_idempotent(self, upsert_engine):
        from module_5_incremental_loads.upsert_helpers import load_insert_or_replace
        self._seed(upsert_engine)
        df = pd.DataFrame(INCOMING)
        load_insert_or_replace(upsert_engine, "orders", df)
        load_insert_or_replace(upsert_engine, "orders", df)
        count = pd.read_sql("SELECT COUNT(*) AS c FROM orders", con=upsert_engine).iloc[0]["c"]
        assert count == 3


class TestStagedMerge:

    def _seed(self, engine):
        pd.DataFrame(EXISTING).to_sql("orders", con=engine, if_exists="append", index=False)

    def test_inserts_new_rows(self, upsert_engine):
        from module_5_incremental_loads.upsert_helpers import load_staged_merge
        self._seed(upsert_engine)
        result = load_staged_merge(upsert_engine, "orders", pd.DataFrame(INCOMING))
        assert result["inserted"] == 1  # only order_id=3 is new

    def test_updates_changed_rows(self, upsert_engine):
        from module_5_incremental_loads.upsert_helpers import load_staged_merge
        self._seed(upsert_engine)
        load_staged_merge(upsert_engine, "orders", pd.DataFrame(INCOMING))
        row = pd.read_sql("SELECT status FROM orders WHERE order_id=1", con=upsert_engine)
        assert row.iloc[0]["status"] == "completed"

    def test_does_not_count_unchanged_rows(self, upsert_engine):
        from module_5_incremental_loads.upsert_helpers import load_staged_merge
        self._seed(upsert_engine)
        result = load_staged_merge(upsert_engine, "orders", pd.DataFrame(INCOMING))
        # order_id=2 is unchanged — should NOT be counted as updated
        assert result["updated"] == 1  # only order_id=1 changed

    def test_idempotent(self, upsert_engine):
        from module_5_incremental_loads.upsert_helpers import load_staged_merge
        self._seed(upsert_engine)
        df = pd.DataFrame(INCOMING)
        load_staged_merge(upsert_engine, "orders", df)
        result2 = load_staged_merge(upsert_engine, "orders", df)
        assert result2["inserted"] == 0
        assert result2["updated"] == 0
        count = pd.read_sql("SELECT COUNT(*) AS c FROM orders", con=upsert_engine).iloc[0]["c"]
        assert count == 3


# =============================================================================
# SCD TESTS
# =============================================================================

CUSTOMER = {
    "customer_id": "C001",
    "full_name":   "Alice Johnson",
    "email":       "alice@example.com",
    "loyalty_tier": "bronze",
    "country":     "US",
}
CUSTOMER_UPDATED = {**CUSTOMER, "loyalty_tier": "gold"}


class TestSCD1:

    def test_insert_new_customer(self, scd_engine):
        from module_5_incremental_loads.scd_helpers import apply_scd1
        action = apply_scd1(scd_engine, {**CUSTOMER})
        assert action == "inserted"
        count = pd.read_sql("SELECT COUNT(*) AS c FROM dim_customers_scd1", con=scd_engine).iloc[0]["c"]
        assert count == 1

    def test_update_existing_customer(self, scd_engine):
        from module_5_incremental_loads.scd_helpers import apply_scd1
        apply_scd1(scd_engine, {**CUSTOMER})
        action = apply_scd1(scd_engine, {**CUSTOMER_UPDATED})
        assert action == "updated"

    def test_history_is_lost_after_update(self, scd_engine):
        """SCD1 overwrites — only the latest value should remain."""
        from module_5_incremental_loads.scd_helpers import apply_scd1
        apply_scd1(scd_engine, {**CUSTOMER})
        apply_scd1(scd_engine, {**CUSTOMER_UPDATED})
        row = pd.read_sql("SELECT loyalty_tier FROM dim_customers_scd1 WHERE customer_id='C001'", con=scd_engine)
        assert row.iloc[0]["loyalty_tier"] == "gold"
        # Only one row — no history
        count = pd.read_sql("SELECT COUNT(*) AS c FROM dim_customers_scd1 WHERE customer_id='C001'", con=scd_engine).iloc[0]["c"]
        assert count == 1


class TestSCD2:

    def test_insert_new_customer(self, scd_engine):
        from module_5_incremental_loads.scd_helpers import apply_scd2
        action = apply_scd2(scd_engine, {**CUSTOMER}, effective_date="2024-01-01")
        assert action == "inserted"

    def test_first_row_is_current(self, scd_engine):
        from module_5_incremental_loads.scd_helpers import apply_scd2, get_current_scd2_record
        apply_scd2(scd_engine, {**CUSTOMER}, effective_date="2024-01-01")
        current = get_current_scd2_record(scd_engine, "C001")
        assert current is not None
        assert current["is_current"] == 1
        assert current["valid_to"] == "9999-12-31"

    def test_change_creates_new_row(self, scd_engine):
        from module_5_incremental_loads.scd_helpers import apply_scd2
        apply_scd2(scd_engine, {**CUSTOMER},         effective_date="2024-01-01")
        action = apply_scd2(scd_engine, {**CUSTOMER_UPDATED}, effective_date="2024-03-01")
        assert action == "versioned"
        count = pd.read_sql("SELECT COUNT(*) AS c FROM dim_customers_scd2 WHERE customer_id='C001'", con=scd_engine).iloc[0]["c"]
        assert count == 2

    def test_old_row_is_closed(self, scd_engine):
        from module_5_incremental_loads.scd_helpers import apply_scd2
        apply_scd2(scd_engine, {**CUSTOMER},         effective_date="2024-01-01")
        apply_scd2(scd_engine, {**CUSTOMER_UPDATED}, effective_date="2024-03-01")
        rows = pd.read_sql(
            "SELECT * FROM dim_customers_scd2 WHERE customer_id='C001' ORDER BY surrogate_key",
            con=scd_engine,
        )
        old = rows.iloc[0]
        assert old["is_current"] == 0
        assert old["valid_to"] == "2024-02-29"  # day before new version

    def test_new_row_is_current(self, scd_engine):
        from module_5_incremental_loads.scd_helpers import apply_scd2, get_current_scd2_record
        apply_scd2(scd_engine, {**CUSTOMER},         effective_date="2024-01-01")
        apply_scd2(scd_engine, {**CUSTOMER_UPDATED}, effective_date="2024-03-01")
        current = get_current_scd2_record(scd_engine, "C001")
        assert current["loyalty_tier"] == "gold"
        assert current["valid_to"] == "9999-12-31"

    def test_no_change_returns_no_change(self, scd_engine):
        from module_5_incremental_loads.scd_helpers import apply_scd2
        apply_scd2(scd_engine, {**CUSTOMER}, effective_date="2024-01-01")
        action = apply_scd2(scd_engine, {**CUSTOMER}, effective_date="2024-01-01")
        assert action == "no_change"

    def test_idempotent_no_duplicate_rows(self, scd_engine):
        """Applying the same change twice must not create extra rows."""
        from module_5_incremental_loads.scd_helpers import apply_scd2
        apply_scd2(scd_engine, {**CUSTOMER},         effective_date="2024-01-01")
        apply_scd2(scd_engine, {**CUSTOMER_UPDATED}, effective_date="2024-03-01")
        apply_scd2(scd_engine, {**CUSTOMER_UPDATED}, effective_date="2024-03-01")
        count = pd.read_sql("SELECT COUNT(*) AS c FROM dim_customers_scd2 WHERE customer_id='C001'", con=scd_engine).iloc[0]["c"]
        assert count == 2  # still only 2 rows

    def test_history_is_never_deleted(self, scd_engine):
        from module_5_incremental_loads.scd_helpers import apply_scd2
        apply_scd2(scd_engine, {**CUSTOMER},         effective_date="2024-01-01")
        apply_scd2(scd_engine, {**CUSTOMER_UPDATED}, effective_date="2024-03-01")
        # All rows in the table — historical rows are never physically deleted
        total = pd.read_sql("SELECT COUNT(*) AS c FROM dim_customers_scd2", con=scd_engine).iloc[0]["c"]
        assert total == 2

    def test_point_in_time_query_before_change(self, scd_engine):
        from module_5_incremental_loads.scd_helpers import apply_scd2, get_record_at_date
        apply_scd2(scd_engine, {**CUSTOMER},         effective_date="2024-01-01")
        apply_scd2(scd_engine, {**CUSTOMER_UPDATED}, effective_date="2024-03-01")
        rec = get_record_at_date(scd_engine, "C001", "2024-02-01")
        assert rec is not None
        assert rec["loyalty_tier"] == "bronze"

    def test_point_in_time_query_after_change(self, scd_engine):
        from module_5_incremental_loads.scd_helpers import apply_scd2, get_record_at_date
        apply_scd2(scd_engine, {**CUSTOMER},         effective_date="2024-01-01")
        apply_scd2(scd_engine, {**CUSTOMER_UPDATED}, effective_date="2024-03-01")
        rec = get_record_at_date(scd_engine, "C001", "2024-04-01")
        assert rec is not None
        assert rec["loyalty_tier"] == "gold"


# =============================================================================
# INCREMENTAL PIPELINE TESTS
# =============================================================================

class TestIncrementalPipeline:

    def test_first_run_loads_all_rows(self, pipeline_engine):
        from module_5_incremental_loads.pipeline_helpers import run_pipeline
        result = run_pipeline(pipeline_engine)
        assert result["status"] == "success"
        assert result["rows_extracted"] == 3
        assert result["rows_loaded"] == 3

    def test_second_run_with_no_new_data_loads_zero_rows(self, pipeline_engine):
        from module_5_incremental_loads.pipeline_helpers import run_pipeline
        run_pipeline(pipeline_engine)
        result = run_pipeline(pipeline_engine)
        assert result["status"] == "success"
        assert result["rows_extracted"] == 0
        assert result["rows_loaded"] == 0

    def test_watermark_advances_after_successful_run(self, pipeline_engine):
        from module_5_incremental_loads.pipeline_helpers import run_pipeline, get_watermark
        run_pipeline(pipeline_engine)
        wm = get_watermark(pipeline_engine)
        assert wm is not None
        assert wm >= "2024-01-03"  # at least as late as the latest row

    def test_incremental_run_picks_up_new_rows(self, pipeline_engine):
        from module_5_incremental_loads.pipeline_helpers import run_pipeline
        run_pipeline(pipeline_engine)
        # Add a new row to source
        new = pd.DataFrame([{
            "order_id": 99, "customer_id": "C099", "product": "NewItem",
            "amount": 50.0, "status": "pending",
            "created_at": "2024-02-01 08:00:00", "updated_at": "2024-02-01 08:00:00",
        }])
        new.to_sql("source_orders", con=pipeline_engine, if_exists="append", index=False)
        result = run_pipeline(pipeline_engine)
        assert result["rows_extracted"] == 1
        assert result["rows_loaded"] == 1

    def test_transform_normalises_status_to_lowercase(self, pipeline_engine):
        from module_5_incremental_loads.pipeline_helpers import run_pipeline
        run_pipeline(pipeline_engine)
        statuses = pd.read_sql("SELECT DISTINCT status FROM target_orders", con=pipeline_engine)["status"].tolist()
        for s in statuses:
            assert s == s.lower(), f"Status '{s}' is not lowercase"

    def test_transform_adds_amount_category(self, pipeline_engine):
        from module_5_incremental_loads.pipeline_helpers import run_pipeline
        run_pipeline(pipeline_engine)
        df = pd.read_sql("SELECT amount_category FROM target_orders", con=pipeline_engine)
        assert df["amount_category"].notna().all()
        assert set(df["amount_category"].unique()).issubset({"low", "medium", "high", "premium"})

    def test_pipeline_run_log_records_each_run(self, pipeline_engine):
        from module_5_incremental_loads.pipeline_helpers import run_pipeline
        run_pipeline(pipeline_engine)
        run_pipeline(pipeline_engine)
        logs = pd.read_sql("SELECT * FROM pipeline_run_log", con=pipeline_engine)
        assert len(logs) == 2

    def test_pipeline_run_log_status_is_success(self, pipeline_engine):
        from module_5_incremental_loads.pipeline_helpers import run_pipeline
        run_pipeline(pipeline_engine)
        logs = pd.read_sql("SELECT status FROM pipeline_run_log", con=pipeline_engine)
        assert (logs["status"] == "success").all()

    def test_idempotency_running_pipeline_five_times(self, pipeline_engine):
        """Running the pipeline multiple times must not duplicate target rows."""
        from module_5_incremental_loads.pipeline_helpers import run_pipeline
        for _ in range(5):
            run_pipeline(pipeline_engine)
        count = pd.read_sql("SELECT COUNT(*) AS c FROM target_orders", con=pipeline_engine).iloc[0]["c"]
        assert count == 3  # always exactly the number of source rows
