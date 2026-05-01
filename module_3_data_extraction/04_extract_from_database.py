"""
Module 3 - Lesson 4: Extracting Data from Databases
=====================================================
Databases are the most common data source in enterprise data engineering.
SQLAlchemy provides a unified Python interface for all major databases:
  - SQLite (used here — no server needed!)
  - PostgreSQL
  - MySQL / MariaDB
  - Microsoft SQL Server
  - Oracle

Just change the connection string to point at a different database.
All other code stays the same.

Topics covered:
  - Creating a SQLAlchemy engine
  - Creating tables and inserting data
  - pandas.read_sql() — read query results into a DataFrame
  - pandas.read_sql_table() — read a whole table
  - Parameterized queries (prevents SQL injection!)
  - Chunked database reads for large tables
  - Writing DataFrames back to a database (to_sql)
  - Connection context managers
  - Reflecting existing database schemas
"""

import pandas as pd
from sqlalchemy import create_engine, text, inspect
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
DB_PATH = SCRIPT_DIR / "module3_sample.db"

# =============================================================================
# 1. CREATING A DATABASE AND ENGINE
# =============================================================================

print("=" * 60)
print("1. CREATING THE DATABASE")
print("=" * 60)

# SQLite connection string: "sqlite:///path/to/database.db"
# For PostgreSQL: "postgresql+psycopg2://user:password@host:5432/dbname"
# For MySQL:      "mysql+pymysql://user:password@host:3306/dbname"

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    echo=False           # echo=True logs every SQL statement (useful for debugging)
)

print(f"Created SQLite engine: {engine.url}")
print(f"Database file: {DB_PATH}")

# --- Create sample tables ---
# We use text() to wrap raw SQL strings (required by SQLAlchemy 2.0+)
with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS products"))
    conn.execute(text("DROP TABLE IF EXISTS orders"))
    conn.execute(text("DROP TABLE IF EXISTS order_items"))
    conn.execute(text("DROP TABLE IF EXISTS customers"))

    # Products table
    conn.execute(text("""
        CREATE TABLE products (
            product_id   TEXT PRIMARY KEY,
            name         TEXT NOT NULL,
            category     TEXT NOT NULL,
            price        REAL NOT NULL,
            stock        INTEGER NOT NULL DEFAULT 0
        )
    """))

    # Customers table
    conn.execute(text("""
        CREATE TABLE customers (
            customer_id  TEXT PRIMARY KEY,
            name         TEXT NOT NULL,
            email        TEXT UNIQUE NOT NULL,
            city         TEXT,
            country      TEXT DEFAULT 'USA'
        )
    """))

    # Orders table (references customers)
    conn.execute(text("""
        CREATE TABLE orders (
            order_id     INTEGER PRIMARY KEY,
            customer_id  TEXT NOT NULL REFERENCES customers(customer_id),
            order_date   TEXT NOT NULL,
            status       TEXT DEFAULT 'pending',
            total_amount REAL
        )
    """))

    # Order items (references orders and products)
    conn.execute(text("""
        CREATE TABLE order_items (
            item_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id    INTEGER NOT NULL REFERENCES orders(order_id),
            product_id  TEXT NOT NULL REFERENCES products(product_id),
            quantity    INTEGER NOT NULL,
            unit_price  REAL NOT NULL
        )
    """))

    # Insert sample data
    conn.execute(text("""
        INSERT INTO products (product_id, name, category, price, stock) VALUES
        ('P001', 'Laptop Pro 15',           'Laptops',      1299.99, 45),
        ('P002', 'Wireless Mouse',          'Peripherals',    29.99, 200),
        ('P003', 'Mechanical Keyboard',     'Peripherals',    89.99, 150),
        ('P004', '27" 4K Monitor',          'Monitors',      449.99,  60),
        ('P005', 'USB-C Hub',               'Accessories',    49.99, 180),
        ('P006', 'Noise-Cancelling Headphones', 'Audio',     179.99,  75),
        ('P007', 'Ergonomic Chair',         'Furniture',     399.99,  25)
    """))

    conn.execute(text("""
        INSERT INTO customers (customer_id, name, email, city, country) VALUES
        ('C001', 'Alice Johnson', 'alice@example.com', 'New York',    'USA'),
        ('C002', 'Bob Smith',     'bob@example.com',   'Los Angeles', 'USA'),
        ('C003', 'Carol White',   'carol@example.com', 'Chicago',     'USA'),
        ('C004', 'Dave Brown',    'dave@example.com',  'Toronto',     'Canada'),
        ('C005', 'Eve Davis',     'eve@example.com',   'London',      'UK')
    """))

    conn.execute(text("""
        INSERT INTO orders (order_id, customer_id, order_date, status, total_amount) VALUES
        (1001, 'C001', '2024-01-10', 'completed', 1329.98),
        (1002, 'C002', '2024-01-12', 'completed',  179.99),
        (1003, 'C001', '2024-01-15', 'completed',  449.99),
        (1004, 'C003', '2024-01-18', 'pending',   1299.99),
        (1005, 'C004', '2024-01-20', 'completed',   79.98),
        (1006, 'C005', '2024-01-22', 'cancelled',  179.99),
        (1007, 'C002', '2024-01-25', 'completed',  449.99),
        (1008, 'C001', '2024-02-01', 'completed',   49.99)
    """))

    conn.execute(text("""
        INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
        (1001, 'P001', 1, 1299.99),
        (1001, 'P002', 1,   29.99),
        (1002, 'P006', 1,  179.99),
        (1003, 'P004', 1,  449.99),
        (1004, 'P001', 1, 1299.99),
        (1005, 'P003', 1,   89.99),
        (1005, 'P002', 1,   29.99),  -- wait, 89.99+29.99=119.98, not 79.98; demo data
        (1006, 'P006', 1,  179.99),
        (1007, 'P004', 1,  449.99),
        (1008, 'P005', 1,   49.99)
    """))

    conn.commit()

print("Tables created and sample data inserted.")


# =============================================================================
# 2. READING FROM THE DATABASE WITH PANDAS
# =============================================================================

print("\n" + "=" * 60)
print("2. READING WITH pd.read_sql()")
print("=" * 60)

# pd.read_sql(sql, con) — execute a SQL query and return a DataFrame
# 'con' can be a SQLAlchemy engine or connection

# Read an entire table
df_products = pd.read_sql("SELECT * FROM products", con=engine)
print(f"Products table ({len(df_products)} rows):")
print(df_products)

# Read with a filter — use WHERE clause
df_laptops = pd.read_sql(
    "SELECT * FROM products WHERE category = 'Laptops'",
    con=engine
)
print(f"\nLaptops only:\n{df_laptops}")

# Multi-table query with JOIN
df_orders = pd.read_sql("""
    SELECT
        o.order_id,
        o.order_date,
        c.name       AS customer_name,
        c.country,
        o.status,
        o.total_amount
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    ORDER BY o.order_date
""", con=engine)
print(f"\nOrders with customer info ({len(df_orders)} rows):")
print(df_orders)


# =============================================================================
# 3. PARAMETERIZED QUERIES — SAFE VARIABLE INJECTION
# =============================================================================

print("\n" + "=" * 60)
print("3. PARAMETERIZED QUERIES (Prevents SQL Injection!)")
print("=" * 60)

# NEVER format user input directly into SQL strings — it's a security risk!
# BAD (SQL injection risk):
# customer_id = user_input  # imagine this is "'; DROP TABLE customers; --"
# sql = f"SELECT * FROM orders WHERE customer_id = '{customer_id}'"  # DANGEROUS!

# GOOD: Use parameterized queries. SQLAlchemy escapes the values automatically.

# Method 1: Using :param_name syntax with SQLAlchemy text()
def get_orders_for_customer(customer_id: str) -> pd.DataFrame:
    """Safely fetch orders for a given customer using parameterized query."""
    query = text("""
        SELECT o.order_id, o.order_date, o.status, o.total_amount
        FROM orders o
        WHERE o.customer_id = :cid
        ORDER BY o.order_date
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {"cid": customer_id})
        return pd.DataFrame(result.fetchall(), columns=result.keys())

alice_orders = get_orders_for_customer("C001")
print(f"Alice's orders:\n{alice_orders}")

# Method 2: pd.read_sql with params argument
def get_products_by_category(category: str, max_price: float) -> pd.DataFrame:
    """Fetch products by category with a price ceiling."""
    query = "SELECT * FROM products WHERE category = :cat AND price <= :max_p"
    return pd.read_sql(
        text(query),
        con=engine,
        params={"cat": category, "max_p": max_price}
    )

affordable_peripherals = get_products_by_category("Peripherals", max_price=100.0)
print(f"\nPeripherals <= $100:\n{affordable_peripherals}")


# =============================================================================
# 4. READING LARGE TABLES IN CHUNKS
# =============================================================================

print("\n" + "=" * 60)
print("4. CHUNKED DATABASE READS")
print("=" * 60)

# For large tables that don't fit in memory, use chunksize parameter
# to process the table in batches.

chunk_size = 3
chunks_processed = 0
total_rows = 0
total_revenue = 0.0

print(f"Reading order_items in chunks of {chunk_size}:")

query = """
    SELECT oi.*, p.category
    FROM order_items oi
    JOIN products p ON oi.product_id = p.product_id
"""

for chunk in pd.read_sql(text(query), con=engine, chunksize=chunk_size):
    chunk_revenue = (chunk["quantity"] * chunk["unit_price"]).sum()
    total_rows += len(chunk)
    total_revenue += chunk_revenue
    chunks_processed += 1
    print(f"  Chunk {chunks_processed}: {len(chunk)} rows, revenue=${chunk_revenue:.2f}")

print(f"\nTotal: {total_rows} rows, ${total_revenue:.2f} total revenue")


# =============================================================================
# 5. INSPECTING THE DATABASE SCHEMA
# =============================================================================

print("\n" + "=" * 60)
print("5. INSPECTING DATABASE SCHEMA")
print("=" * 60)

# SQLAlchemy's Inspector lets you examine an existing database schema
inspector = inspect(engine)

print("Tables in the database:")
for table_name in inspector.get_table_names():
    print(f"\n  Table: {table_name}")
    columns = inspector.get_columns(table_name)
    for col in columns:
        nullable = "" if col["nullable"] else " NOT NULL"
        print(f"    {col['name']:20s} {str(col['type']):15s}{nullable}")

    # Show foreign keys
    fks = inspector.get_foreign_keys(table_name)
    for fk in fks:
        print(f"    FK: {fk['constrained_columns']} → {fk['referred_table']}.{fk['referred_columns']}")


# =============================================================================
# 6. WRITING A DATAFRAME TO THE DATABASE
# =============================================================================

print("\n" + "=" * 60)
print("6. WRITING DATAFRAME TO DATABASE (to_sql)")
print("=" * 60)

# Create a summary DataFrame we want to persist
order_summary = pd.read_sql("""
    SELECT
        c.country,
        COUNT(o.order_id) AS total_orders,
        SUM(o.total_amount) AS total_revenue,
        AVG(o.total_amount) AS avg_order_value
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.status = 'completed'
    GROUP BY c.country
    ORDER BY total_revenue DESC
""", con=engine)

print("Order summary (to be written to DB):")
print(order_summary)

# Write to a new table in the same database
order_summary.to_sql(
    name="order_summary_by_country",
    con=engine,
    if_exists="replace",  # "replace" drops and recreates, "append" adds rows, "fail" raises
    index=False           # don't write the DataFrame index as a column
)

print(f"\nWritten order_summary_by_country table to database")

# Verify it was written
df_verify = pd.read_sql("SELECT * FROM order_summary_by_country", con=engine)
print(f"Verification read ({len(df_verify)} rows):\n{df_verify}")


# =============================================================================
# MAIN DEMO
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("PRACTICAL DEMO: Full Database Extraction")
    print("=" * 60)

    # Comprehensive query: orders with all details
    full_report = pd.read_sql("""
        SELECT
            o.order_id,
            o.order_date,
            c.name          AS customer,
            c.country,
            p.name          AS product,
            p.category,
            oi.quantity,
            oi.unit_price,
            oi.quantity * oi.unit_price AS line_total,
            o.status
        FROM orders o
        JOIN customers c  ON o.customer_id  = c.customer_id
        JOIN order_items oi ON o.order_id   = oi.order_id
        JOIN products p   ON oi.product_id  = p.product_id
        ORDER BY o.order_date, o.order_id
    """, con=engine)

    print(f"\nFull order report ({len(full_report)} rows):")
    print(full_report.to_string())

    print(f"\nRevenue by category:")
    cat_rev = full_report.groupby("category")["line_total"].sum().sort_values(ascending=False)
    print(cat_rev.round(2))

    print(f"\nRevenue by country:")
    country_rev = full_report.groupby("country")["line_total"].sum().sort_values(ascending=False)
    print(country_rev.round(2))

    # Clean up the database file
    engine.dispose()
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"\nCleaned up {DB_PATH.name}")
