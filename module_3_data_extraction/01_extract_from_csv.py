"""
Module 3 - Lesson 1: Extracting Data from CSV Files
=====================================================
CSV (Comma-Separated Values) is the most common file format in data engineering.
Despite its simplicity, real-world CSVs have many quirks:
  - Different delimiters (comma, pipe, tab, semicolon)
  - Various encodings (UTF-8, Latin-1, Windows-1252)
  - Header rows at different positions
  - Inconsistent quoting
  - Large files that don't fit in memory

Topics covered:
  - Basic pd.read_csv() usage
  - Handling different encodings
  - Non-standard delimiters
  - Skipping header/footer rows
  - Specifying column names and dtypes
  - Chunked reading for large files
  - Detecting file encoding automatically
  - Reading compressed CSV files
"""

import pandas as pd
import csv
import os
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
SCRIPT_DIR = Path(__file__).parent


# =============================================================================
# 1. BASIC CSV READING
# =============================================================================

print("=" * 60)
print("1. BASIC CSV READING")
print("=" * 60)

products_csv = DATA_DIR / "products.csv"

# Most common usage — read a standard CSV
df = pd.read_csv(products_csv)
print(f"Shape: {df.shape}")
print(f"Columns: {list(df.columns)}")
print(df.head())
print(f"\nDtypes:\n{df.dtypes}")


# =============================================================================
# 2. USEFUL read_csv() PARAMETERS
# =============================================================================

print("\n" + "=" * 60)
print("2. KEY read_csv() PARAMETERS")
print("=" * 60)

# dtype — tell pandas what types to use (avoids wrong inferences)
df_typed = pd.read_csv(
    products_csv,
    dtype={
        "product_id": str,          # keep as string (IDs should not be ints)
        "price": float,
        "stock_quantity": "Int64",  # nullable int
    }
)
print(f"product_id type: {df_typed['product_id'].dtype}")
print(f"stock_quantity type: {df_typed['stock_quantity'].dtype}")

# usecols — read only specific columns (saves memory on wide files)
df_slim = pd.read_csv(
    products_csv,
    usecols=["product_id", "product_name", "price"]
)
print(f"\nSlim read (3 cols): {list(df_slim.columns)}")
print(df_slim.head(3))

# index_col — set a column as the index
df_indexed = pd.read_csv(products_csv, index_col="product_id")
print(f"\nWith product_id as index:")
print(df_indexed.head(3))
print(f"Index: {df_indexed.index.tolist()[:5]}")

# nrows — read only the first N rows (great for sampling large files)
df_sample = pd.read_csv(products_csv, nrows=5)
print(f"\nFirst 5 rows only: {len(df_sample)} rows")

# skiprows — skip specific rows at the top
# skipfooter — skip rows at the bottom
df_skip = pd.read_csv(products_csv, skiprows=1, header=None,
                      names=["id", "name", "cat", "price", "stock", "supplier"])
print(f"\nWith skipped header row (manual column names): {len(df_skip)} rows")
print(df_skip.head(3))


# =============================================================================
# 3. HANDLING DIFFERENT DELIMITERS
# =============================================================================

print("\n" + "=" * 60)
print("3. DIFFERENT DELIMITERS")
print("=" * 60)

# Create sample files with different delimiters
pipe_file = SCRIPT_DIR / "demo_pipe.csv"
tab_file = SCRIPT_DIR / "demo_tab.tsv"
semicolon_file = SCRIPT_DIR / "demo_semicolon.csv"

sample_data = "id|name|price\n1|Laptop|999.99\n2|Mouse|29.99\n3|Keyboard|79.99"
pipe_file.write_text(sample_data)

sample_data_tab = "id\tname\tprice\n1\tLaptop\t999.99\n2\tMouse\t29.99"
tab_file.write_text(sample_data_tab)

sample_data_semi = "id;name;price\n1;Laptop;999.99\n2;Mouse;29.99"
semicolon_file.write_text(sample_data_semi)

# Pipe-delimited
df_pipe = pd.read_csv(pipe_file, sep="|")
print(f"Pipe-delimited:\n{df_pipe}")

# Tab-delimited (.tsv files)
df_tab = pd.read_csv(tab_file, sep="\t")
print(f"\nTab-delimited:\n{df_tab}")

# Semicolon-delimited (common in European locales where comma is decimal separator)
df_semi = pd.read_csv(semicolon_file, sep=";")
print(f"\nSemicolon-delimited:\n{df_semi}")

# sep=None with engine="python" — auto-detect delimiter
df_auto = pd.read_csv(pipe_file, sep=None, engine="python")
print(f"\nAuto-detected delimiter:\n{df_auto}")

# Clean up demo files
for f in [pipe_file, tab_file, semicolon_file]:
    f.unlink(missing_ok=True)


# =============================================================================
# 4. HANDLING ENCODINGS
# =============================================================================

print("\n" + "=" * 60)
print("4. HANDLING FILE ENCODINGS")
print("=" * 60)

# Common encodings you'll encounter:
#   UTF-8      — modern standard, handles all Unicode characters
#   Latin-1    — common in older European data
#   CP1252     — Windows encoding, superset of Latin-1
#   UTF-16     — common in some enterprise systems (has BOM marker)

# Create a file with special characters (UTF-8)
utf8_file = SCRIPT_DIR / "demo_utf8.csv"
with open(utf8_file, "w", encoding="utf-8") as f:
    f.write("id,name,city\n")
    f.write("1,José García,São Paulo\n")
    f.write("2,Müller Hans,München\n")
    f.write("3,Pierre Dupont,Montréal\n")

# Read UTF-8
df_utf8 = pd.read_csv(utf8_file, encoding="utf-8")
print(f"UTF-8 read:\n{df_utf8}")

# Create a Latin-1 encoded file
latin1_file = SCRIPT_DIR / "demo_latin1.csv"
with open(latin1_file, "w", encoding="latin-1") as f:
    f.write("id,name,city\n")
    f.write("1,José García,São Paulo\n")

# Reading with wrong encoding causes UnicodeDecodeError
try:
    pd.read_csv(latin1_file, encoding="utf-8")
except UnicodeDecodeError as e:
    print(f"\nUnicodeDecodeError (as expected): {str(e)[:80]}...")

# Read with correct encoding
df_latin1 = pd.read_csv(latin1_file, encoding="latin-1")
print(f"Latin-1 read (correct encoding): {df_latin1['name'].tolist()}")

# encoding_errors="replace" — replace invalid chars instead of crashing
df_fallback = pd.read_csv(latin1_file, encoding="utf-8", encoding_errors="replace")
print(f"UTF-8 with replace: {df_fallback['name'].tolist()}")

# Clean up
for f in [utf8_file, latin1_file]:
    f.unlink(missing_ok=True)


# =============================================================================
# 5. READING CSV WITH NULL VALUES
# =============================================================================

print("\n" + "=" * 60)
print("5. NULL VALUE HANDLING")
print("=" * 60)

# Create a CSV with various null representations
nulls_file = SCRIPT_DIR / "demo_nulls.csv"
nulls_file.write_text(
    "id,name,amount,status\n"
    "1,Alice,250.00,active\n"
    "2,Bob,,inactive\n"          # empty = NaN
    "3,Carol,N/A,active\n"       # N/A = NaN (pandas default)
    "4,,175.50,active\n"         # empty string = NaN
    "5,Eve,NULL,active\n"        # NULL = NaN (pandas default)
    "6,Frank,none,inactive\n"    # 'none' — not null by default!
    "7,Grace,0,active\n"         # 0 is NOT null (be careful!)
)

df_nulls = pd.read_csv(nulls_file)
print("Default null handling:")
print(df_nulls)
print(f"\nNull counts: {df_nulls.isnull().sum().to_dict()}")

# Custom null values
df_custom_nulls = pd.read_csv(
    nulls_file,
    na_values=["N/A", "NULL", "none", "null", "NaN", ""],  # treat these as NaN
    keep_default_na=True   # also keep pandas defaults (NaN, NA, n/a, etc.)
)
print(f"\nWith custom na_values:\n{df_custom_nulls}")
print(f"Null counts: {df_custom_nulls.isnull().sum().to_dict()}")

nulls_file.unlink(missing_ok=True)


# =============================================================================
# 6. CHUNKED READING FOR LARGE FILES
# =============================================================================

print("\n" + "=" * 60)
print("6. CHUNKED READING (for large files)")
print("=" * 60)

# For files too large to fit in memory, use chunksize to process in batches.
# read_csv with chunksize returns a TextFileReader iterator — lazy evaluation.

# Generate a moderately large demo CSV
large_file = SCRIPT_DIR / "demo_large.csv"
print("Generating demo large file...")
with open(large_file, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["id", "customer", "amount", "region"])
    regions = ["North", "South", "East", "West"]
    for i in range(1, 1001):   # 1000 rows
        writer.writerow([i, f"Customer_{i}", round(i * 1.5, 2), regions[i % 4]])

print(f"Generated {large_file.name} (1000 rows)")

# Process in chunks of 100 rows
chunk_size = 100
total_rows = 0
total_amount = 0.0
region_counts = {}

# Use the iterator as a context manager so it's properly closed
with pd.read_csv(large_file, chunksize=chunk_size) as reader:
    for chunk_num, chunk in enumerate(reader, start=1):
        # Process each chunk
        chunk_total = chunk["amount"].sum()
        total_rows += len(chunk)
        total_amount += chunk_total

        for region, count in chunk["region"].value_counts().items():
            region_counts[region] = region_counts.get(region, 0) + count

        print(f"  Chunk {chunk_num:2d}: {len(chunk):4d} rows, "
              f"chunk_total=${chunk_total:>8,.2f}, running_total=${total_amount:>10,.2f}")

print(f"\nTotal rows processed: {total_rows}")
print(f"Total amount: ${total_amount:,.2f}")
print(f"Region distribution: {region_counts}")

# Alternatively, collect filtered chunks into a list then concat
filtered_chunks = []
with pd.read_csv(large_file, chunksize=200) as reader:
    for chunk in reader:
        filtered = chunk[chunk["region"] == "North"]
        filtered_chunks.append(filtered)

north_df = pd.concat(filtered_chunks, ignore_index=True)
print(f"\nNorth region records extracted via chunking: {len(north_df)}")

large_file.unlink(missing_ok=True)


# =============================================================================
# MAIN DEMO
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("PRACTICAL DEMO: Robust CSV Extraction")
    print("=" * 60)

    def extract_csv(
        filepath: str | Path,
        delimiter: str = ",",
        encoding: str = "utf-8",
        dtype: dict = None,
        null_values: list = None,
        chunk_size: int = None,
    ) -> pd.DataFrame:
        """
        Robust CSV extraction function with configurable options.

        Args:
            filepath: Path to the CSV file.
            delimiter: Column delimiter (default ',').
            encoding: File encoding (default 'utf-8').
            dtype: Dict of column name to dtype.
            null_values: List of strings to treat as NaN.
            chunk_size: If set, process in chunks (for large files).

        Returns:
            DataFrame with extracted data.
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {path}")

        read_kwargs = {
            "sep": delimiter,
            "encoding": encoding,
            "encoding_errors": "replace",
        }
        if dtype:
            read_kwargs["dtype"] = dtype
        if null_values:
            read_kwargs["na_values"] = null_values
            read_kwargs["keep_default_na"] = True

        print(f"  Extracting: {path.name}")

        if chunk_size:
            chunks = []
            with pd.read_csv(path, chunksize=chunk_size, **read_kwargs) as reader:
                for chunk in reader:
                    chunks.append(chunk)
            df = pd.concat(chunks, ignore_index=True)
        else:
            df = pd.read_csv(path, **read_kwargs)

        print(f"  Loaded {len(df)} rows × {df.shape[1]} columns")
        return df

    # Extract the products catalog
    products_df = extract_csv(
        DATA_DIR / "products.csv",
        dtype={"product_id": str, "price": float, "stock_quantity": "Int64"},
        null_values=["N/A", "NULL", "-"]
    )
    print(f"\n  Products loaded:")
    print(products_df.to_string())

    # Summary
    print(f"\n  Catalog Stats:")
    print(f"    Categories:     {products_df['category'].nunique()}")
    print(f"    Price range:    ${products_df['price'].min():.2f} - ${products_df['price'].max():.2f}")
    print(f"    Total stock:    {products_df['stock_quantity'].sum()} units")
    print(f"    Inventory value: ${(products_df['price'] * products_df['stock_quantity']).sum():,.2f}")
