"""
Tests for Module 3: Data Extraction
=====================================
Tests cover data extraction functions from:
  - CSV files (various formats and edge cases)
  - JSON files (flat and nested)
  - Databases (SQLite with SQLAlchemy)

Note: API tests are skipped in offline environments.
"""

import json
import pytest
import pandas as pd
from io import StringIO, BytesIO
from pathlib import Path
from sqlalchemy import create_engine, text

# Reference to sample data
DATA_DIR = Path(__file__).parent.parent / "module_3_data_extraction" / "data"


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def products_csv_path():
    """Path to the products sample CSV file."""
    return DATA_DIR / "products.csv"


@pytest.fixture
def transactions_json_path():
    """Path to the transactions sample JSON file."""
    return DATA_DIR / "transactions.json"


@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database with sample data."""
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE employees (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                department TEXT,
                salary REAL
            )
        """))
        conn.execute(text("""
            INSERT INTO employees (id, name, department, salary) VALUES
            (1, 'Alice', 'Engineering', 85000),
            (2, 'Bob',   'Marketing',   72000),
            (3, 'Carol', 'Engineering', 91000),
            (4, 'Dave',  'Sales',       68000),
            (5, 'Eve',   'Engineering', 78000)
        """))
        conn.execute(text("""
            CREATE TABLE departments (
                id   INTEGER PRIMARY KEY,
                name TEXT,
                budget REAL
            )
        """))
        conn.execute(text("""
            INSERT INTO departments VALUES (1,'Engineering',500000),(2,'Marketing',200000),(3,'Sales',150000)
        """))
        conn.commit()
    yield engine
    engine.dispose()


# =============================================================================
# CSV EXTRACTION TESTS
# =============================================================================

class TestCSVExtraction:
    """Tests for CSV extraction functions."""

    def test_products_csv_loads(self, products_csv_path):
        """Products CSV should load without errors."""
        df = pd.read_csv(products_csv_path)
        assert len(df) > 0
        assert "product_id" in df.columns
        assert "product_name" in df.columns
        assert "price" in df.columns

    def test_products_csv_correct_row_count(self, products_csv_path):
        """Products CSV should have exactly 15 rows."""
        df = pd.read_csv(products_csv_path)
        assert len(df) == 15

    def test_products_csv_price_column_is_numeric(self, products_csv_path):
        """Price column should be numeric (no parsing errors)."""
        df = pd.read_csv(products_csv_path, dtype={"price": float})
        assert df["price"].dtype == float
        assert (df["price"] > 0).all()

    def test_pipe_delimiter_csv(self):
        """read_csv should handle pipe-delimited files."""
        csv_data = "id|name|value\n1|Alice|100\n2|Bob|200"
        df = pd.read_csv(StringIO(csv_data), sep="|")
        assert list(df.columns) == ["id", "name", "value"]
        assert len(df) == 2
        assert df["value"].iloc[0] == 100

    def test_tab_delimiter_csv(self):
        """read_csv should handle tab-delimited files."""
        tsv_data = "id\tname\tvalue\n1\tAlice\t100\n2\tBob\t200"
        df = pd.read_csv(StringIO(tsv_data), sep="\t")
        assert list(df.columns) == ["id", "name", "value"]
        assert len(df) == 2

    def test_custom_null_values(self):
        """Custom null values should be parsed as NaN."""
        csv_data = "id,name,amount\n1,Alice,N/A\n2,,100\n3,Carol,NULL"
        df = pd.read_csv(StringIO(csv_data), na_values=["N/A", "NULL", ""])
        assert pd.isna(df.loc[0, "amount"])   # N/A → NaN
        assert pd.isna(df.loc[1, "name"])     # "" → NaN
        assert pd.isna(df.loc[2, "amount"])   # NULL → NaN

    def test_usecols_reads_subset(self, products_csv_path):
        """usecols should read only the specified columns."""
        df = pd.read_csv(products_csv_path, usecols=["product_id", "product_name", "price"])
        assert list(df.columns) == ["product_id", "product_name", "price"]
        assert "stock_quantity" not in df.columns

    def test_nrows_limits_rows(self, products_csv_path):
        """nrows should limit the number of rows read."""
        df_limited = pd.read_csv(products_csv_path, nrows=5)
        assert len(df_limited) == 5

    def test_chunked_reading_processes_all_rows(self, products_csv_path):
        """Chunked reading should process all rows."""
        total = 0
        with pd.read_csv(products_csv_path, chunksize=5) as reader:
            for chunk in reader:
                total += len(chunk)
        df_full = pd.read_csv(products_csv_path)
        assert total == len(df_full)

    def test_dtype_override_keeps_string_id(self, products_csv_path):
        """product_id with dtype=str should not be converted to int."""
        df = pd.read_csv(products_csv_path, dtype={"product_id": str})
        # IDs like "P001" should remain strings
        # pandas 2.0+ may use StringDtype instead of object for str columns
        assert pd.api.types.is_string_dtype(df["product_id"])
        assert df["product_id"].iloc[0].startswith("P")

    def test_skiprows_skips_header(self):
        """skiprows=1 should skip the first row."""
        csv_data = "ignore_this\nid,name,value\n1,Alice,100"
        df = pd.read_csv(StringIO(csv_data), skiprows=1)
        assert "id" in df.columns
        assert len(df) == 1

    def test_encoding_utf8_reads_special_chars(self):
        """UTF-8 encoded CSV should correctly read special characters."""
        csv_data = "id,name,city\n1,José,São Paulo\n2,Müller,München"
        df = pd.read_csv(StringIO(csv_data), encoding="utf-8")
        assert df["name"].iloc[0] == "José"
        assert df["city"].iloc[1] == "München"


# =============================================================================
# JSON EXTRACTION TESTS
# =============================================================================

class TestJSONExtraction:
    """Tests for JSON extraction functions."""

    def test_transactions_json_loads(self, transactions_json_path):
        """Transactions JSON should load without errors."""
        with open(transactions_json_path) as f:
            data = json.load(f)
        assert isinstance(data, list)
        assert len(data) > 0

    def test_transactions_json_correct_structure(self, transactions_json_path):
        """Each transaction should have required fields."""
        with open(transactions_json_path) as f:
            data = json.load(f)
        required_fields = {"transaction_id", "timestamp", "customer_id", "product_id", "amount", "status"}
        for txn in data:
            missing = required_fields - set(txn.keys())
            assert len(missing) == 0, f"Transaction missing fields: {missing}"

    def test_json_array_to_dataframe(self, transactions_json_path):
        """JSON array should convert to DataFrame correctly."""
        with open(transactions_json_path) as f:
            data = json.load(f)
        df = pd.DataFrame(data)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == len(data)
        assert "transaction_id" in df.columns

    def test_flat_json_normalization(self):
        """json_normalize should flatten a simple nested JSON."""
        data = [
            {"id": 1, "customer": {"name": "Alice", "city": "NY"}, "amount": 100},
            {"id": 2, "customer": {"name": "Bob",   "city": "LA"}, "amount": 200},
        ]
        df = pd.json_normalize(data)
        assert "customer.name" in df.columns
        assert "customer.city" in df.columns
        assert df["customer.name"].iloc[0] == "Alice"

    def test_deeply_nested_json_normalization(self):
        """json_normalize should handle deeply nested structures."""
        data = [{"id": 1, "a": {"b": {"c": "deep_value"}}}]
        df = pd.json_normalize(data)
        assert "a.b.c" in df.columns
        assert df["a.b.c"].iloc[0] == "deep_value"

    def test_json_normalize_with_record_path(self):
        """json_normalize with record_path should expand nested arrays."""
        data = [
            {"order_id": 1, "items": [{"product": "A", "qty": 1}, {"product": "B", "qty": 2}]},
            {"order_id": 2, "items": [{"product": "C", "qty": 3}]},
        ]
        df = pd.json_normalize(data, record_path="items", meta=["order_id"])
        assert len(df) == 3   # total items across all orders
        assert "product" in df.columns
        assert "order_id" in df.columns

    def test_json_string_parsing(self):
        """json.loads should correctly parse a JSON string."""
        json_str = '{"status": "ok", "count": 5, "data": [1, 2, 3]}'
        parsed = json.loads(json_str)
        assert parsed["status"] == "ok"
        assert parsed["count"] == 5
        assert parsed["data"] == [1, 2, 3]

    def test_jsonl_parsing(self):
        """JSONL format (one JSON per line) should parse correctly."""
        jsonl = '{"id": 1, "value": 10}\n{"id": 2, "value": 20}\n{"id": 3, "value": 30}'
        df = pd.read_json(StringIO(jsonl), lines=True)
        assert len(df) == 3
        assert list(df["id"]) == [1, 2, 3]

    def test_pd_read_json_from_string(self):
        """pd.read_json should work with a JSON string."""
        json_str = '[{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]'
        df = pd.read_json(StringIO(json_str))
        assert len(df) == 2
        assert df["name"].iloc[0] == "Alice"

    def test_transactions_amounts_positive(self, transactions_json_path):
        """All transaction amounts should be positive."""
        with open(transactions_json_path) as f:
            data = json.load(f)
        df = pd.DataFrame(data)
        assert (df["amount"] > 0).all()


# =============================================================================
# DATABASE EXTRACTION TESTS
# =============================================================================

class TestDatabaseExtraction:
    """Tests for database extraction using SQLAlchemy."""

    def test_read_full_table(self, in_memory_db):
        """read_sql should load an entire table."""
        df = pd.read_sql("SELECT * FROM employees", con=in_memory_db)
        assert len(df) == 5
        assert "name" in df.columns
        assert "salary" in df.columns

    def test_read_with_where_clause(self, in_memory_db):
        """read_sql with WHERE should filter rows."""
        df = pd.read_sql(
            "SELECT * FROM employees WHERE department = 'Engineering'",
            con=in_memory_db
        )
        assert len(df) == 3
        assert set(df["department"].unique()) == {"Engineering"}

    def test_read_with_join(self, in_memory_db):
        """read_sql should handle JOINs between tables."""
        df = pd.read_sql("""
            SELECT e.name, e.department, d.budget
            FROM employees e
            JOIN departments d ON e.department = d.name
        """, con=in_memory_db)
        assert "name" in df.columns
        assert "budget" in df.columns
        assert len(df) > 0

    def test_parameterized_query(self, in_memory_db):
        """Parameterized query should filter correctly and safely."""
        df = pd.read_sql(
            text("SELECT * FROM employees WHERE department = :dept"),
            con=in_memory_db,
            params={"dept": "Marketing"}
        )
        assert len(df) == 1
        assert df["name"].iloc[0] == "Bob"

    def test_read_sql_returns_dataframe(self, in_memory_db):
        """read_sql result should be a pandas DataFrame."""
        result = pd.read_sql("SELECT 1 AS test", con=in_memory_db)
        assert isinstance(result, pd.DataFrame)

    def test_aggregation_query(self, in_memory_db):
        """SQL aggregation should compute correct stats."""
        df = pd.read_sql("""
            SELECT department,
                   COUNT(*) AS employee_count,
                   AVG(salary) AS avg_salary
            FROM employees
            GROUP BY department
            ORDER BY department
        """, con=in_memory_db)
        assert "employee_count" in df.columns
        eng_row = df[df["department"] == "Engineering"].iloc[0]
        assert eng_row["employee_count"] == 3

    def test_to_sql_writes_correctly(self, in_memory_db):
        """DataFrame.to_sql should write data to the database."""
        new_data = pd.DataFrame({
            "name": ["Frank", "Grace"],
            "score": [95, 87]
        })
        new_data.to_sql("test_table", con=in_memory_db, if_exists="replace", index=False)
        result = pd.read_sql("SELECT * FROM test_table", con=in_memory_db)
        assert len(result) == 2
        assert "name" in result.columns

    def test_to_sql_if_exists_replace(self, in_memory_db):
        """to_sql with if_exists='replace' should truncate existing data."""
        df1 = pd.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})
        df2 = pd.DataFrame({"id": [4, 5], "value": [40, 50]})

        df1.to_sql("replace_test", con=in_memory_db, if_exists="replace", index=False)
        df2.to_sql("replace_test", con=in_memory_db, if_exists="replace", index=False)

        result = pd.read_sql("SELECT * FROM replace_test", con=in_memory_db)
        assert len(result) == 2   # only df2 rows

    def test_to_sql_if_exists_append(self, in_memory_db):
        """to_sql with if_exists='append' should add rows to existing table."""
        df1 = pd.DataFrame({"id": [1, 2], "value": [10, 20]})
        df2 = pd.DataFrame({"id": [3, 4], "value": [30, 40]})

        df1.to_sql("append_test", con=in_memory_db, if_exists="replace", index=False)
        df2.to_sql("append_test", con=in_memory_db, if_exists="append", index=False)

        result = pd.read_sql("SELECT * FROM append_test", con=in_memory_db)
        assert len(result) == 4

    def test_chunked_db_read(self, in_memory_db):
        """Chunked read should process all rows without missing any."""
        total = 0
        for chunk in pd.read_sql("SELECT * FROM employees", con=in_memory_db, chunksize=2):
            total += len(chunk)
        assert total == 5
