"""
Tests for Module 2: Pandas Operations
======================================
Tests cover the key pandas operations taught in module_2_pandas:
  - Data cleaning (null handling, deduplication, type conversion)
  - String operations
  - Data transformation (apply, pivot, melt)
  - Aggregations (groupby, rolling, cumulative)
  - Merging and joining
"""

import pytest
import pandas as pd
import numpy as np
from io import StringIO


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_sales_df():
    """Realistic sales DataFrame with some quality issues."""
    csv = """order_id,customer,product,category,quantity,unit_price,region
1001,Alice,Laptop,Electronics,1,999.99,North
1002,Bob,Mouse,Electronics,3,29.99,South
1003,Carol,Chair,Furniture,1,349.99,East
1004,Alice,Laptop,Electronics,2,999.99,North
1002,Bob,Mouse,Electronics,3,29.99,South
1005,,USB Hub,Accessories,2,49.99,West
1006,Dave,Desk,Furniture,1,699.99,
1007,Eve,Monitor,Electronics,,449.99,East
"""
    return pd.read_csv(StringIO(csv))


@pytest.fixture
def clean_sales_df(sample_sales_df):
    """A cleaned version of the sales DataFrame."""
    df = sample_sales_df.drop_duplicates(subset=["order_id"], keep="first").copy()
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(1).astype(int)
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    df["region"] = df["region"].fillna("Unknown")
    df["customer"] = df["customer"].fillna("Anonymous")
    df["total"] = df["quantity"] * df["unit_price"]
    return df


@pytest.fixture
def customers_df():
    """Small customers reference DataFrame."""
    return pd.DataFrame({
        "customer_id": ["C001", "C002", "C003"],
        "name": ["Alice", "Bob", "Carol"],
        "city": ["New York", "LA", "Chicago"],
        "country": ["USA", "USA", "USA"],
    })


# =============================================================================
# DATA CLEANING TESTS
# =============================================================================

class TestDataCleaning:
    """Tests for data cleaning operations."""

    def test_drop_duplicates_removes_exact_duplicate(self, sample_sales_df):
        """Order 1002 appears twice — dedup should keep one."""
        original_len = len(sample_sales_df)
        deduped = sample_sales_df.drop_duplicates(subset=["order_id"], keep="first")
        assert len(deduped) == original_len - 1
        assert deduped["order_id"].duplicated().sum() == 0

    def test_fillna_string_column(self, sample_sales_df):
        """Missing customer names should be filled with 'Anonymous'."""
        df = sample_sales_df.copy()
        df["customer"] = df["customer"].fillna("Anonymous")
        assert df["customer"].isnull().sum() == 0
        assert "Anonymous" in df["customer"].values

    def test_fillna_numeric_column(self, sample_sales_df):
        """Missing quantity should be filled with default value 1."""
        df = sample_sales_df.copy()
        df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(1)
        assert df["quantity"].isnull().sum() == 0
        # All quantities should be >= 1
        assert (df["quantity"] >= 1).all()

    def test_fillna_preserves_existing_values(self, sample_sales_df):
        """fillna should not change non-null values."""
        df = sample_sales_df.copy()
        before_fillna = df["customer"].dropna().copy()
        df["customer"] = df["customer"].fillna("Anonymous")
        # All original non-null values should still be there
        for val in before_fillna:
            assert val in df["customer"].values

    def test_type_conversion_to_numeric(self, sample_sales_df):
        """unit_price should convert to float."""
        df = sample_sales_df.copy()
        df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
        non_null = df["unit_price"].dropna()
        assert non_null.dtype in [float, np.float64]

    def test_type_conversion_errors_coerce(self):
        """Non-numeric values should become NaN with errors='coerce'."""
        series = pd.Series(["1.5", "abc", "3.0", None, "invalid"])
        converted = pd.to_numeric(series, errors="coerce")
        assert converted.iloc[0] == 1.5
        assert pd.isna(converted.iloc[1])   # "abc" → NaN
        assert converted.iloc[2] == 3.0
        assert pd.isna(converted.iloc[3])   # None → NaN
        assert pd.isna(converted.iloc[4])   # "invalid" → NaN

    def test_drop_nulls_removes_correct_rows(self, sample_sales_df):
        """dropna on unit_price should remove rows with null price."""
        df = sample_sales_df.copy()
        df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
        null_price_count = df["unit_price"].isnull().sum()
        cleaned = df.dropna(subset=["unit_price"])
        assert len(cleaned) == len(df) - null_price_count

    def test_string_strip_removes_whitespace(self):
        """str.strip() should remove leading/trailing whitespace."""
        series = pd.Series(["  Alice  ", " Bob", "Carol "])
        stripped = series.str.strip()
        assert stripped[0] == "Alice"
        assert stripped[1] == "Bob"
        assert stripped[2] == "Carol"

    def test_string_title_case(self):
        """str.title() should properly capitalize names."""
        series = pd.Series(["alice johnson", "BOB SMITH", "carol WHITE"])
        titled = series.str.title()
        assert titled[0] == "Alice Johnson"
        assert titled[1] == "Bob Smith"
        assert titled[2] == "Carol White"

    def test_rename_columns(self, sample_sales_df):
        """Renaming columns should update column names correctly."""
        df = sample_sales_df.rename(columns={"unit_price": "price_usd"})
        assert "price_usd" in df.columns
        assert "unit_price" not in df.columns

    def test_total_calculation_correct(self, clean_sales_df):
        """total = quantity * unit_price for each row."""
        for _, row in clean_sales_df.iterrows():
            expected = row["quantity"] * row["unit_price"]
            assert abs(row["total"] - expected) < 0.01, \
                f"Row {row['order_id']}: expected {expected}, got {row['total']}"

    def test_region_fillna(self, sample_sales_df):
        """Missing region should be filled with 'Unknown'."""
        df = sample_sales_df.copy()
        df["region"] = df["region"].fillna("Unknown")
        assert df["region"].isnull().sum() == 0
        assert "Unknown" in df["region"].values


# =============================================================================
# TRANSFORMATION TESTS
# =============================================================================

class TestDataTransformation:
    """Tests for data transformation operations."""

    def test_apply_categorize(self, clean_sales_df):
        """apply() should correctly categorize prices."""
        def price_tier(price):
            if pd.isna(price):
                return "Unknown"
            if price < 100:
                return "Budget"
            elif price < 500:
                return "Mid"
            return "Premium"

        clean_sales_df["tier"] = clean_sales_df["unit_price"].apply(price_tier)

        assert clean_sales_df[clean_sales_df["product"] == "Mouse"]["tier"].iloc[0] == "Budget"
        assert clean_sales_df[clean_sales_df["product"] == "Laptop"]["tier"].iloc[0] == "Premium"
        assert clean_sales_df[clean_sales_df["product"] == "Chair"]["tier"].iloc[0] == "Mid"

    def test_vectorized_operations(self, clean_sales_df):
        """Vectorized arithmetic should produce correct results."""
        df = clean_sales_df.copy()
        df["with_tax"] = df["unit_price"] * 1.08
        for _, row in df.iterrows():
            assert abs(row["with_tax"] - row["unit_price"] * 1.08) < 0.001

    def test_np_where_conditional_column(self, clean_sales_df):
        """np.where should correctly apply conditions."""
        df = clean_sales_df.copy()
        df["is_high_value"] = np.where(df["total"] > 500, True, False)
        high_value_rows = df[df["is_high_value"]]
        assert all(high_value_rows["total"] > 500)
        low_value_rows = df[~df["is_high_value"]]
        assert all(low_value_rows["total"] <= 500)

    def test_pd_cut_binning(self, clean_sales_df):
        """pd.cut should assign records to correct price bins."""
        df = clean_sales_df.copy()
        bins = [0, 100, 500, float("inf")]
        labels = ["cheap", "mid", "expensive"]
        df["price_bin"] = pd.cut(df["unit_price"], bins=bins, labels=labels, include_lowest=True)
        # Mouse (29.99) should be 'cheap'
        mouse_bin = df[df["product"] == "Mouse"]["price_bin"].iloc[0]
        assert str(mouse_bin) == "cheap"
        # Laptop (999.99) should be 'expensive'
        laptop_bin = df[df["product"] == "Laptop"]["price_bin"].iloc[0]
        assert str(laptop_bin) == "expensive"

    def test_pivot_table_sums(self, clean_sales_df):
        """pivot_table should correctly sum totals by category."""
        pivot = clean_sales_df.pivot_table(
            values="total",
            index="category",
            aggfunc="sum"
        )
        electronics_total = clean_sales_df[clean_sales_df["category"] == "Electronics"]["total"].sum()
        assert abs(pivot.loc["Electronics", "total"] - electronics_total) < 0.01

    def test_melt_preserves_values(self):
        """melt should preserve all values in the long format."""
        wide = pd.DataFrame({
            "product": ["Laptop", "Mouse"],
            "Q1": [1000, 100],
            "Q2": [1200, 150],
        })
        long = wide.melt(id_vars=["product"], var_name="quarter", value_name="sales")
        assert len(long) == 4  # 2 products × 2 quarters
        laptop_q1 = long[(long["product"] == "Laptop") & (long["quarter"] == "Q1")]["sales"].iloc[0]
        assert laptop_q1 == 1000


# =============================================================================
# AGGREGATION TESTS
# =============================================================================

class TestAggregations:
    """Tests for groupby and aggregation operations."""

    def test_groupby_sum(self, clean_sales_df):
        """groupby sum should correctly total revenue per category."""
        result = clean_sales_df.groupby("category")["total"].sum()
        expected_electronics = clean_sales_df[
            clean_sales_df["category"] == "Electronics"
        ]["total"].sum()
        assert abs(result["Electronics"] - expected_electronics) < 0.01

    def test_groupby_count(self, clean_sales_df):
        """groupby count should give the right number of orders per region."""
        result = clean_sales_df.groupby("region")["order_id"].count()
        north_count = (clean_sales_df["region"] == "North").sum()
        assert result.get("North", 0) == north_count

    def test_agg_multiple_functions(self, clean_sales_df):
        """agg with multiple functions should produce correct results."""
        result = clean_sales_df.groupby("category")["unit_price"].agg(["mean", "max", "min"])
        for cat in result.index:
            subset = clean_sales_df[clean_sales_df["category"] == cat]["unit_price"]
            assert abs(result.loc[cat, "mean"] - subset.mean()) < 0.01
            assert result.loc[cat, "max"] == subset.max()
            assert result.loc[cat, "min"] == subset.min()

    def test_named_aggregation(self, clean_sales_df):
        """Named aggregations should produce correctly named columns."""
        result = clean_sales_df.groupby("category").agg(
            order_count=("order_id", "count"),
            total_revenue=("total", "sum"),
        )
        assert "order_count" in result.columns
        assert "total_revenue" in result.columns
        assert result.loc["Electronics", "order_count"] > 0

    def test_transform_adds_group_stats(self, clean_sales_df):
        """transform should add group-level stats to original df."""
        df = clean_sales_df.copy()
        df["cat_avg_price"] = df.groupby("category")["unit_price"].transform("mean")
        # Each row in Electronics should have the Electronics mean
        elec = df[df["category"] == "Electronics"]
        expected_mean = elec["unit_price"].mean()
        assert all(abs(elec["cat_avg_price"] - expected_mean) < 0.01)

    def test_cumsum(self, clean_sales_df):
        """cumsum should produce increasing values."""
        df = clean_sales_df.sort_values("order_id").copy()
        df["cumulative_revenue"] = df["total"].cumsum()
        # Each value should be >= the previous
        cumulative = df["cumulative_revenue"].reset_index(drop=True)
        for i in range(1, len(cumulative)):
            assert cumulative.iloc[i] >= cumulative.iloc[i - 1]
        # Last value should equal the total sum
        assert abs(cumulative.iloc[-1] - df["total"].sum()) < 0.01


# =============================================================================
# MERGE/JOIN TESTS
# =============================================================================

class TestMergingJoining:
    """Tests for DataFrame joining operations."""

    def test_inner_join_keeps_only_matching(self, clean_sales_df, customers_df):
        """Inner join should keep only rows matching in both DataFrames."""
        result = pd.merge(
            clean_sales_df,
            customers_df,
            left_on="customer",
            right_on="name",
            how="inner"
        )
        # All result customers must be in the customers_df
        assert set(result["customer"].unique()).issubset(set(customers_df["name"].unique()))

    def test_left_join_keeps_all_left_rows(self, clean_sales_df, customers_df):
        """Left join should keep all rows from the left DataFrame."""
        result = pd.merge(
            clean_sales_df,
            customers_df,
            left_on="customer",
            right_on="name",
            how="left"
        )
        assert len(result) == len(clean_sales_df)

    def test_left_join_fills_nans_for_unmatched(self, clean_sales_df, customers_df):
        """Left join should have NaN in right-only columns for unmatched rows."""
        result = pd.merge(
            clean_sales_df,
            customers_df,
            left_on="customer",
            right_on="name",
            how="left"
        )
        unmatched = result[~result["customer"].isin(customers_df["name"])]
        assert unmatched["city"].isnull().all()

    def test_outer_join_includes_all_records(self, clean_sales_df, customers_df):
        """Outer join should include all records from both DataFrames."""
        result = pd.merge(
            clean_sales_df,
            customers_df,
            left_on="customer",
            right_on="name",
            how="outer"
        )
        # Should have at least as many rows as either input
        assert len(result) >= len(clean_sales_df)
        assert len(result) >= len(customers_df)

    def test_concat_vertical_stacks_rows(self):
        """concat with axis=0 should stack rows."""
        df1 = pd.DataFrame({"id": [1, 2], "value": [10, 20]})
        df2 = pd.DataFrame({"id": [3, 4], "value": [30, 40]})
        combined = pd.concat([df1, df2], ignore_index=True)
        assert len(combined) == len(df1) + len(df2)
        assert list(combined["id"]) == [1, 2, 3, 4]

    def test_concat_horizontal_adds_columns(self):
        """concat with axis=1 should add columns."""
        df1 = pd.DataFrame({"id": [1, 2], "name": ["a", "b"]})
        df2 = pd.DataFrame({"score": [90, 85], "grade": ["A", "B"]})
        combined = pd.concat([df1, df2], axis=1)
        assert len(combined.columns) == 4
        assert "id" in combined.columns
        assert "score" in combined.columns

    def test_merge_suffixes_for_overlapping_columns(self):
        """Merge should add suffixes to resolve overlapping column names."""
        left = pd.DataFrame({"id": [1, 2], "value": [10, 20]})
        right = pd.DataFrame({"id": [1, 2], "value": [100, 200]})
        result = pd.merge(left, right, on="id", suffixes=("_left", "_right"))
        assert "value_left" in result.columns
        assert "value_right" in result.columns
        assert "value" not in result.columns
