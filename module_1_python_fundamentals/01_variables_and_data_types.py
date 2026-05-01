"""
Module 1 - Lesson 1: Variables and Data Types
==============================================
In Python, variables are created by assignment — no explicit declaration needed.
Python is *dynamically typed*, meaning a variable's type is determined at runtime
and can change. However, in data engineering we want *predictable* types, so we
always check and convert types when loading data.

Topics covered:
  - Variable assignment and naming conventions
  - Numeric types: int, float, complex
  - Strings and string operations
  - Booleans and truthiness
  - Lists (mutable sequences)
  - Tuples (immutable sequences)
  - Dictionaries (key-value mappings)
  - Sets (unordered unique collections)
  - Type checking and type conversion
"""

# =============================================================================
# 1. VARIABLE ASSIGNMENT
# =============================================================================

# Simple assignment — Python infers the type automatically
name = "Alice"          # str
age = 30                # int
salary = 75_000.50      # float  (underscores improve readability in large numbers)
is_active = True        # bool

# Multiple assignment on one line
x, y, z = 1, 2, 3

# Swap two variables without a temp variable (Python magic!)
x, y = y, x

# Naming conventions:
#   snake_case  → variables and functions  (PEP 8 standard)
#   UPPER_CASE  → constants
#   PascalCase  → class names

MAX_RETRY_COUNT = 5          # constant (by convention — Python doesn't enforce it)
database_connection_string = "sqlite:///mydb.db"   # snake_case variable

print("--- Variable Assignment ---")
# In production, avoid logging sensitive fields (e.g. salary) as plain text
print(f"name={name}, age={age}, annual_comp=*masked*, is_active={is_active}")
print(f"After swap: x={x}, y={y}")


# =============================================================================
# 2. NUMERIC TYPES
# =============================================================================

print("\n--- Numeric Types ---")

# int — whole numbers, no size limit in Python 3
row_count = 1_500_000
print(f"int: {row_count}, type: {type(row_count)}")

# float — 64-bit floating point (same as double in other languages)
price = 19.99
tax_rate = 0.08
total = price * (1 + tax_rate)
print(f"float: {total:.2f}, type: {type(total)}")

# Beware of floating-point precision issues!
print(f"0.1 + 0.2 = {0.1 + 0.2}")           # Not exactly 0.3!
print(f"round(0.1+0.2, 2) = {round(0.1 + 0.2, 2)}")   # Use round() for display

# Integer division vs true division
print(f"10 / 3  = {10 / 3}")       # True division → float
print(f"10 // 3 = {10 // 3}")      # Floor division → int
print(f"10 % 3  = {10 % 3}")       # Modulo (remainder)
print(f"2 ** 10 = {2 ** 10}")      # Exponentiation

# Useful built-in math functions
import math
print(f"abs(-5) = {abs(-5)}")
print(f"round(3.7) = {round(3.7)}")
print(f"math.sqrt(144) = {math.sqrt(144)}")
print(f"math.ceil(4.1) = {math.ceil(4.1)}")
print(f"math.floor(4.9) = {math.floor(4.9)}")


# =============================================================================
# 3. STRINGS
# =============================================================================

print("\n--- Strings ---")

# Strings can be single or double quoted; use triple quotes for multi-line
greeting = "Hello, World!"
query = 'SELECT * FROM orders WHERE status = "active"'
description = """This is a
multi-line string
often used for docstrings."""

# String length
print(f"Length: {len(greeting)}")

# Indexing (0-based) and slicing [start:stop:step]
print(f"First char: {greeting[0]}")         # 'H'
print(f"Last char: {greeting[-1]}")         # '!'
print(f"Slice [0:5]: {greeting[0:5]}")      # 'Hello'
print(f"Reversed: {greeting[::-1]}")        # reverse the string

# Common string methods — critical for data cleaning
raw = "  John Doe  "
print(f"strip(): '{raw.strip()}'")          # remove leading/trailing whitespace
print(f"upper(): '{raw.strip().upper()}'")
print(f"lower(): '{raw.strip().lower()}'")
print(f"replace(): '{greeting.replace('World', 'Python')}'")
print(f"split(): {greeting.split(', ')}")   # returns a list
print(f"startswith: {greeting.startswith('Hello')}")
print(f"endswith: {greeting.endswith('!')}")
print(f"in operator: {'World' in greeting}")

# String formatting — three approaches
item = "laptop"
qty = 3
unit_price = 999.99

# 1. f-strings (Python 3.6+, preferred)
print(f"f-string: {qty}x {item} @ ${unit_price:.2f} each")

# 2. .format() method
print("format(): {}x {} @ ${:.2f} each".format(qty, item, unit_price))

# 3. % formatting (older style, still seen in logging)
print("%%: %dx %s @ $%.2f each" % (qty, item, unit_price))

# Joining a list of strings
columns = ["order_id", "customer", "amount"]
csv_header = ", ".join(columns)
print(f"join: {csv_header}")

# Splitting a CSV line
csv_line = "1001,Alice,250.00,New York"
fields = csv_line.split(",")
print(f"split: {fields}")


# =============================================================================
# 4. BOOLEANS
# =============================================================================

print("\n--- Booleans ---")

is_valid = True
has_error = False

# Boolean operators
print(f"True and False = {True and False}")
print(f"True or False  = {True or False}")
print(f"not True       = {not True}")

# Comparison operators return booleans
print(f"5 > 3  : {5 > 3}")
print(f"5 == 5 : {5 == 5}")
print(f"5 != 3 : {5 != 3}")
print(f"5 >= 5 : {5 >= 5}")

# Truthiness — many values are "falsy" in Python
# Falsy: False, None, 0, 0.0, "", [], {}, set()
# Everything else is truthy
falsy_values = [False, None, 0, 0.0, "", [], {}, set()]
for val in falsy_values:
    print(f"bool({val!r:10}) = {bool(val)}")

# Practical use: checking for missing/empty data
def is_missing(value):
    """Returns True if value is None, empty string, or empty collection."""
    return not value   # uses truthiness

print(f"is_missing(None)  = {is_missing(None)}")
print(f"is_missing('')    = {is_missing('')}")
print(f"is_missing('abc') = {is_missing('abc')}")


# =============================================================================
# 5. LISTS
# =============================================================================

print("\n--- Lists ---")

# Lists are ordered, mutable sequences. They are the go-to container for
# homogeneous collections (all items of the same type).
products = ["laptop", "mouse", "keyboard", "monitor"]
prices = [999.99, 29.99, 79.99, 349.99]
mixed = [1, "two", 3.0, True, None]  # can mix types (but avoid in practice)

# Access and slicing (same as strings)
print(f"First: {products[0]}")
print(f"Last: {products[-1]}")
print(f"Slice [1:3]: {products[1:3]}")

# Modification
products.append("webcam")                   # add to end
products.insert(1, "charger")              # insert at index
products.remove("mouse")                   # remove by value
popped = products.pop()                    # remove and return last item
print(f"After modifications: {products}")

# List operations
numbers = [3, 1, 4, 1, 5, 9, 2, 6, 5]
print(f"Length: {len(numbers)}")
print(f"Sum: {sum(numbers)}")
print(f"Min: {min(numbers)}")
print(f"Max: {max(numbers)}")
print(f"Sorted: {sorted(numbers)}")         # returns new sorted list
numbers.sort()                              # sorts in place
print(f"After sort(): {numbers}")
print(f"Count of 5: {numbers.count(5)}")
print(f"Index of 9: {numbers.index(9)}")

# Checking membership
print(f"4 in numbers: {4 in numbers}")

# Nested lists (lists of lists — like a 2D table)
table = [
    ["order_id", "customer", "amount"],  # header row
    [1001, "Alice", 250.00],
    [1002, "Bob", 175.50],
    [1003, "Carol", 390.00],
]
print(f"\nTable row 1: {table[1]}")
print(f"Table[1][2] (Alice's amount): {table[1][2]}")


# =============================================================================
# 6. TUPLES
# =============================================================================

print("\n--- Tuples ---")

# Tuples are ordered, IMMUTABLE sequences. Use them for fixed data like
# coordinates, RGB values, database rows, or function return values.
point = (10.5, 20.3)            # 2D coordinate
rgb_red = (255, 0, 0)           # color value
db_row = (1001, "Alice", 250.0) # database record

# Access same as list, but no modification methods
print(f"x={point[0]}, y={point[1]}")

# Tuple unpacking — very common in Python
order_id, customer, amount = db_row
print(f"Unpacked: id={order_id}, customer={customer}, amount={amount}")

# Tuples as dictionary keys (lists can't be dict keys — they're mutable)
coordinates_map = {
    (0, 0): "origin",
    (1, 0): "right",
    (0, 1): "up",
}
print(f"Lookup (0,0): {coordinates_map[(0, 0)]}")

# Named tuples — tuples with field names (great for structured data)
from collections import namedtuple
Product = namedtuple("Product", ["id", "name", "price"])
p = Product(id=101, name="laptop", price=999.99)
print(f"Named tuple: {p.name} costs ${p.price}")


# =============================================================================
# 7. DICTIONARIES
# =============================================================================

print("\n--- Dictionaries ---")

# Dicts are unordered (Python 3.7+ maintains insertion order) key-value stores.
# Keys must be immutable (strings, numbers, tuples). Values can be anything.
# In data engineering, dicts often represent a single record/row.

record = {
    "order_id": 1001,
    "customer": "Alice",
    "amount": 250.00,
    "items": ["laptop", "mouse"],   # value can be a list
    "metadata": {"source": "web"},  # value can be a nested dict
}

# Access
print(f"customer: {record['customer']}")
print(f"Using .get() with default: {record.get('missing_key', 'N/A')}")

# Modification
record["status"] = "shipped"       # add new key
record["amount"] = 260.00          # update existing key
del record["metadata"]             # delete a key
print(f"Updated record: {record}")

# Iterating over dicts
print("\nKeys:")
for key in record.keys():
    print(f"  {key}")

print("\nValues:")
for value in record.values():
    print(f"  {value}")

print("\nKey-Value pairs:")
for key, value in record.items():
    print(f"  {key}: {value}")

# Dict comprehension — build a dict from iterables
products_list = ["laptop", "mouse", "keyboard"]
prices_list = [999.99, 29.99, 79.99]
price_map = {product: price for product, price in zip(products_list, prices_list)}
print(f"\nPrice map: {price_map}")

# Merging dicts (Python 3.9+: use | operator; 3.5+: use **)
defaults = {"region": "US", "currency": "USD", "tax_rate": 0.08}
overrides = {"region": "EU", "currency": "EUR"}
merged = {**defaults, **overrides}    # overrides wins for duplicate keys
print(f"Merged: {merged}")


# =============================================================================
# 8. SETS
# =============================================================================

print("\n--- Sets ---")

# Sets are unordered collections of UNIQUE elements. They are extremely fast
# for membership testing and de-duplication operations.

raw_categories = ["Electronics", "Clothing", "Electronics", "Food", "Clothing", "Food", "Food"]
unique_categories = set(raw_categories)   # automatically de-duplicates
print(f"Unique categories: {unique_categories}")

# Set operations (like mathematical set operations)
a = {1, 2, 3, 4, 5}
b = {3, 4, 5, 6, 7}

print(f"Union (a | b):        {a | b}")          # all elements in either
print(f"Intersection (a & b): {a & b}")          # elements in both
print(f"Difference (a - b):   {a - b}")          # in a but not b
print(f"Symmetric diff (a^b): {a ^ b}")          # in either but not both

# Membership test — O(1) average, much faster than list.
valid_statuses = {"pending", "processing", "shipped", "delivered", "cancelled"}
status = "shipped"
print(f"Is '{status}' valid? {status in valid_statuses}")

# Use case: find duplicate order IDs in a dataset
order_ids = [1001, 1002, 1003, 1001, 1004, 1002]
duplicates = {oid for oid in order_ids if order_ids.count(oid) > 1}
print(f"Duplicate order IDs: {duplicates}")


# =============================================================================
# 9. TYPE CHECKING AND CONVERSION
# =============================================================================

print("\n--- Type Checking and Conversion ---")

# type() returns the exact type; isinstance() checks including inheritance
value = 42
print(f"type(42) = {type(value)}")
print(f"isinstance(42, int) = {isinstance(value, int)}")
print(f"isinstance(42, (int, float)) = {isinstance(value, (int, float))}")

# Type conversion (casting)
# int() — truncates floats, parses numeric strings
print(f"int(3.9) = {int(3.9)}")          # 3 (truncates, does NOT round)
print(f"int('42') = {int('42')}")        # 42

# float() — converts to float
print(f"float('3.14') = {float('3.14')}")
print(f"float(10) = {float(10)}")

# str() — convert to string
print(f"str(100) = '{str(100)}'")
print(f"str(3.14) = '{str(3.14)}'")

# bool() — convert to boolean (uses truthiness rules)
print(f"bool(0) = {bool(0)}, bool(1) = {bool(1)}, bool('') = {bool('')}")

# list(), tuple(), set() — convert between sequence types
my_tuple = (1, 2, 3)
my_list = list(my_tuple)
my_set = set(my_list)
print(f"tuple→list: {my_list}, list→set: {my_set}")

# IMPORTANT: Safe conversion with error handling
def safe_to_int(value, default=None):
    """Convert value to int; return default if conversion fails."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

print(f"\nsafe_to_int('42')   = {safe_to_int('42')}")
print(f"safe_to_int('abc')  = {safe_to_int('abc', default=-1)}")
print(f"safe_to_int(None)   = {safe_to_int(None)}")
print(f"safe_to_int('3.14') = {safe_to_int('3.14')}")  # Note: fails! '3.14' is not int


# =============================================================================
# MAIN DEMO
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("PRACTICAL DEMO: Representing a Sales Record")
    print("=" * 60)

    # A typical data record in data engineering is a dict
    sale = {
        "order_id": "ORD-2024-001",
        "date": "2024-01-15",
        "customer": "Alice Johnson",
        "items": [
            {"product": "Laptop Pro", "qty": 1, "unit_price": 1299.99},
            {"product": "Mouse", "qty": 2, "unit_price": 29.99},
        ],
        "region": "North America",
        "is_complete": True,
    }

    # Calculate total
    total = sum(item["qty"] * item["unit_price"] for item in sale["items"])
    sale["total_amount"] = round(total, 2)

    # Display formatted record
    print(f"\nOrder: {sale['order_id']}")
    print(f"Customer: {sale['customer'].upper()}")
    print(f"Date: {sale['date']}")
    print(f"Region: {sale['region']}")
    print(f"Items ({len(sale['items'])}):")
    for item in sale["items"]:
        print(f"  - {item['product']}: {item['qty']} x ${item['unit_price']:.2f}")
    print(f"Total: ${sale['total_amount']:.2f}")
    print(f"Complete: {sale['is_complete']}")
