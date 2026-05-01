"""
Tests for Module 4: ETL Pipeline Components
=============================================
Tests cover core ETL building blocks:
  - Extract functions (CSV loading)
  - Transform functions (cleaning, enrichment, derived columns)
  - Load functions (SQLite via SQLAlchemy)
  - Validation framework
"""

import pytest
import pandas as pd
import numpy as np
from io import StringIO
from pathlib import Path
from sqlalchemy import create_engine, text

# Reference to module 4
MODULE4_DIR = Path(__file__).parent.parent / "module_4_etl_pipelines"
DATA_DIR = MODULE4_DIR / "data"


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def raw_sales_csv():
    """Path to the raw sales CSV with intentional quality issues."""
    return DATA_DIR / "raw_sales.csv"


@pytest.fixture
def clean_db():
    """Fresh in-memory SQLite database for load tests."""
    engine = create_engine("sqlite:///:memory:")
    yield engine
    engine.dispose()


@pytest.fixture
def sample_raw_df():
    """Raw sales DataFrame simulating dirty input data."""
    csv = """id,sale_date,customer_id,product_name,qty,price,discount,region
1,2024-01-05,C001,Laptop Pro,1,1299.99,0.05,North
2,2024-01-07,C002,Wireless Mouse,3,29.99,0.0,South
3,2024-01-08,C003,Office Chair,1,349.99,,East
4,2024-01-10,C001,Laptop Pro,abc,1299.99,0.1,West
5,2024-01-12,,USB Hub,2,49.99,0.0,North
6,2024-01-14,C004,Desk,1,-50.00,0.2,South
7,2024-01-15,C005,Monitor,1,99999.00,0.0,
"""
    return pd.read_csv(StringIO(csv), dtype=str).replace("", None)


@pytest.fixture
def clean_df(sample_raw_df):
    """Cleaned version of sample_raw_df."""
    df = sample_raw_df.copy()
    df["qty"] = pd.to_numeric(df["qty"], errors="coerce").fillna(1).astype(int)
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["discount"] = pd.to_numeric(df["discount"], errors="coerce").fillna(0.0).clip(0, 1)
    df["sale_date"] = pd.to_datetime(df["sale_date"], errors="coerce")
    df["customer_id"] = df["customer_id"].fillna("UNKNOWN")
    df["region"] = df["region"].fillna("Unknown")
    df = df[df["price"].notna() & (df["price"] > 0)].copy()
    df["net_amount"] = (df["qty"] * df["price"] * (1 - df["discount"])).round(2)
    return df.reset_index(drop=True)


# =============================================================================
# EXTRACT TESTS
# =============================================================================

class TestExtract:
    """Tests for data extraction."""

    def test_raw_sales_csv_exists(self, raw_sales_csv):
        """Raw sales CSV file should exist."""
        assert raw_sales_csv.exists(), f"File not found: {raw_sales_csv}"

    def test_raw_sales_csv_loads(self, raw_sales_csv):
        """Raw sales CSV should load into a DataFrame."""
        df = pd.read_csv(raw_sales_csv)
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_raw_sales_has_expected_columns(self, raw_sales_csv):
        """Raw sales should have all expected columns."""
        df = pd.read_csv(raw_sales_csv)
        expected = {"id", "sale_date", "customer_id", "product_name", "qty", "price", "discount", "region"}
        assert expected.issubset(set(df.columns))

    def test_extract_as_strings_preserves_all_values(self, raw_sales_csv):
        """Reading with dtype=str should preserve 'abc' in qty column."""
        df = pd.read_csv(raw_sales_csv, dtype=str)
        # The problematic 'abc' value should be present as a string
        problematic = df[df["qty"] == "abc"]
        assert len(problematic) >= 1

    def test_extract_missing_file_raises(self, tmp_path):
        """Extracting from a missing file should raise FileNotFoundError."""
        missing = tmp_path / "not_found.csv"
        with pytest.raises(FileNotFoundError):
            pd.read_csv(missing)


# =============================================================================
# TRANSFORM TESTS
# =============================================================================

class TestTransform:
    """Tests for data transformation functions."""

    def test_negative_prices_removed(self, clean_df):
        """Cleaned DataFrame should have no negative prices."""
        assert (clean_df["price"] > 0).all()

    def test_invalid_qty_handled(self, clean_df):
        """Non-numeric quantities ('abc') should be replaced with default."""
        assert pd.to_numeric(clean_df["qty"], errors="coerce").notna().all()
        assert (clean_df["qty"] >= 1).all()

    def test_missing_customer_filled(self, clean_df):
        """Missing customer_ids should be filled with 'UNKNOWN'."""
        assert clean_df["customer_id"].notna().all()
        assert "UNKNOWN" in clean_df["customer_id"].values

    def test_discount_clipped_to_valid_range(self, sample_raw_df):
        """Discounts should be clipped to [0, 1]."""
        df = sample_raw_df.copy()
        df["discount"] = pd.to_numeric(df["discount"], errors="coerce").fillna(0.0)
        df["discount_clipped"] = df["discount"].clip(0, 1)
        assert (df["discount_clipped"] >= 0).all()
        assert (df["discount_clipped"] <= 1).all()

    def test_net_amount_calculation_correct(self, clean_df):
        """net_amount = qty * price * (1 - discount)."""
        for _, row in clean_df.iterrows():
            expected = round(row["qty"] * row["price"] * (1 - row["discount"]), 2)
            assert abs(row["net_amount"] - expected) < 0.01, \
                f"Row {row['id']}: expected {expected}, got {row['net_amount']}"

    def test_net_amount_always_non_negative(self, clean_df):
        """net_amount should never be negative after cleaning."""
        assert (clean_df["net_amount"] >= 0).all()

    def test_sale_date_parsed_to_datetime(self, clean_df):
        """sale_date should be pandas datetime type."""
        assert pd.api.types.is_datetime64_any_dtype(clean_df["sale_date"])

    def test_normalize_text_case(self, clean_df):
        """Product names should be consistently formatted."""
        df = clean_df.copy()
        df["product_name"] = df["product_name"].str.strip().str.title()
        # No leading/trailing whitespace
        assert not df["product_name"].str.startswith(" ").any()
        assert not df["product_name"].str.endswith(" ").any()

    def test_enrichment_adds_category(self, clean_df):
        """Enrichment should add a 'category' column from a lookup."""
        category_map = {
            "Laptop Pro": "Laptops",
            "Wireless Mouse": "Peripherals",
            "Office Chair": "Furniture",
            "USB Hub": "Accessories",
            "Desk": "Furniture",
            "Monitor": "Monitors",
        }
        df = clean_df.copy()
        df["category"] = df["product_name"].map(category_map).fillna("Other")
        assert "category" in df.columns
        assert df["category"].notna().all()

    def test_tax_calculation_correct(self, clean_df):
        """Tax calculation should apply the correct rate."""
        TAX_RATE = 0.08
        df = clean_df.copy()
        df["tax_amount"] = (df["net_amount"] * TAX_RATE).round(2)
        for _, row in df.iterrows():
            expected = round(row["net_amount"] * TAX_RATE, 2)
            assert abs(row["tax_amount"] - expected) < 0.001

    def test_filter_removes_correct_rows(self, sample_raw_df):
        """Filter on positive price should remove rows with price <= 0."""
        df = sample_raw_df.copy()
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
        before = len(df)
        filtered = df[df["price"] > 0]
        # Row 6 has price=-50 (negative) — should be removed
        assert len(filtered) < before
        assert (filtered["price"] > 0).all()

    def test_date_parts_extracted(self, clean_df):
        """Year, month, quarter should be correctly extracted."""
        df = clean_df.copy()
        df["year"] = df["sale_date"].dt.year
        df["month"] = df["sale_date"].dt.month
        df["quarter"] = df["sale_date"].dt.quarter
        assert (df["year"] == 2024).all()
        assert df["month"].between(1, 12).all()
        assert df["quarter"].between(1, 4).all()


# =============================================================================
# LOAD TESTS
# =============================================================================

class TestLoad:
    """Tests for loading data to SQLite database."""

    def test_load_writes_all_rows(self, clean_df, clean_db):
        """to_sql should write the correct number of rows."""
        clean_df.to_sql("sales", con=clean_db, if_exists="replace", index=False)
        result = pd.read_sql("SELECT COUNT(*) AS cnt FROM sales", con=clean_db)
        assert result["cnt"].iloc[0] == len(clean_df)

    def test_load_is_idempotent(self, clean_df, clean_db):
        """Loading the same data twice with if_exists='replace' gives same result."""
        clean_df.to_sql("sales", con=clean_db, if_exists="replace", index=False)
        clean_df.to_sql("sales", con=clean_db, if_exists="replace", index=False)
        result = pd.read_sql("SELECT COUNT(*) AS cnt FROM sales", con=clean_db)
        assert result["cnt"].iloc[0] == len(clean_df)  # not doubled

    def test_load_preserves_values(self, clean_df, clean_db):
        """Loaded data should match the source DataFrame."""
        clean_df.to_sql("sales", con=clean_db, if_exists="replace", index=False)
        loaded = pd.read_sql("SELECT * FROM sales ORDER BY id", con=clean_db)
        # Check net_amount values match (within floating-point tolerance)
        for i, row in clean_df.reset_index(drop=True).iterrows():
            loaded_row = loaded[loaded["id"] == row["id"]]
            if len(loaded_row) > 0:
                assert abs(loaded_row["net_amount"].iloc[0] - row["net_amount"]) < 0.01

    def test_load_append_adds_rows(self, clean_df, clean_db):
        """Append mode should add rows without dropping existing ones."""
        clean_df.to_sql("sales", con=clean_db, if_exists="replace", index=False)
        clean_df.to_sql("sales", con=clean_db, if_exists="append", index=False)
        result = pd.read_sql("SELECT COUNT(*) AS cnt FROM sales", con=clean_db)
        assert result["cnt"].iloc[0] == len(clean_df) * 2

    def test_db_query_after_load(self, clean_df, clean_db):
        """SQL queries against loaded data should return correct results."""
        clean_df.to_sql("sales", con=clean_db, if_exists="replace", index=False)
        result = pd.read_sql(
            "SELECT customer_id, SUM(net_amount) AS total FROM sales GROUP BY customer_id",
            con=clean_db
        )
        # C001 should have orders in the data
        assert "C001" in result["customer_id"].values

    def test_rejected_records_saved_separately(self, sample_raw_df, clean_db):
        """Rejected records should be loadable to a separate table."""
        df = sample_raw_df.copy()
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
        rejected = df[df["price"] <= 0].copy()
        rejected["_rejection_reason"] = "negative_price"

        rejected.to_sql("sales_rejected", con=clean_db, if_exists="replace", index=False)
        result = pd.read_sql("SELECT * FROM sales_rejected", con=clean_db)
        assert len(result) >= 1
        assert "_rejection_reason" in result.columns


# =============================================================================
# VALIDATION TESTS
# =============================================================================

class TestValidation:
    """Tests for ETL validation functions."""

    def test_required_field_validation(self, sample_raw_df):
        """Required field check should detect missing values."""
        df = sample_raw_df.copy()
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
        # product_name should never be null
        invalid_mask = df["product_name"].isna()
        assert invalid_mask.sum() == 0, "product_name should not have nulls"

    def test_positive_value_validation(self, sample_raw_df):
        """Price validation should flag negative values."""
        df = sample_raw_df.copy()
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
        invalid = df[df["price"] <= 0]
        assert len(invalid) >= 1  # our test data has a negative price

    def test_range_validation_discount(self, sample_raw_df):
        """Discount should be validated as [0, 1]."""
        df = sample_raw_df.copy()
        df["discount"] = pd.to_numeric(df["discount"], errors="coerce").fillna(0.0)
        invalid = df[~df["discount"].between(0, 1)]
        # No discount in sample_raw_df is outside [0,1] range (0.2 is valid)
        assert len(invalid) == 0

    def test_type_validation_numeric_id(self, sample_raw_df):
        """id column should be parseable as numeric."""
        df = sample_raw_df.copy()
        numeric_ids = pd.to_numeric(df["id"], errors="coerce")
        assert numeric_ids.notna().all(), "All id values should be numeric"

    def test_uniqueness_validation(self, sample_raw_df):
        """Duplicate IDs should be detected."""
        df = sample_raw_df.copy()
        # This dataset doesn't have duplicate IDs, but we can check the logic
        duplicate_mask = df["id"].duplicated()
        # Even if 0 duplicates, the function should work without error
        assert isinstance(duplicate_mask, pd.Series)

    def test_schema_validation_detects_wrong_type(self):
        """Schema validation should detect wrong-type columns."""
        df = pd.DataFrame({
            "id": [1, 2, "three"],   # "three" is wrong type
            "price": [10.0, 20.0, 30.0],
        })
        errors = []
        numeric_ids = pd.to_numeric(df["id"], errors="coerce")
        if numeric_ids.isna().any():
            errors.append("id has non-numeric values")
        assert len(errors) > 0

    def test_rejection_rate_calculation(self):
        """Rejection rate should be calculated correctly."""
        total = 100
        rejected = 15
        rate = rejected / total * 100
        assert rate == 15.0

    def test_valid_records_all_pass_rules(self, clean_df):
        """All records in clean_df should pass basic validation rules."""
        assert (clean_df["price"] > 0).all()
        assert (clean_df["qty"] >= 1).all()
        assert clean_df["product_name"].notna().all()
        assert clean_df["sale_date"].notna().all()
        assert (clean_df["discount"].between(0, 1)).all()
