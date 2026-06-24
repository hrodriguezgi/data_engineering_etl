"""
Module 1 - Lesson 3: Functions
================================
Functions are the primary building block for reusable, testable code.
In data engineering, we structure ETL pipelines as chains of functions:
  extract() → transform() → validate() → load()

Each function should do ONE thing well (Single Responsibility Principle).

Topics covered:
  - Defining and calling functions (def)
  - Positional and keyword arguments
  - Default parameter values
  - *args (variable positional arguments)
  - **kwargs (variable keyword arguments)
  - Return values (single and multiple)
  - Lambda functions (anonymous functions)
  - map() and filter() built-ins
  - Decorators (function wrappers)
  - Generators and the yield keyword
  - Type hints (annotations)
  - Docstrings
"""

import time
import functools
from typing import Optional, List, Dict, Any, Generator
from typing import Union, Tuple

# =============================================================================
# 1. BASIC FUNCTION DEFINITION
# =============================================================================

print("--- Basic Functions ---")


# Simple function — no arguments, no return value
def greet():
    """Print a greeting message."""  # This is a docstring
    print("Hello, data engineer!")


greet()


# Function with arguments and a return value
def calculate_total(quantity: int, unit_price: float) -> float:
    """Calculate total price before tax.

    Args:
        quantity: Number of units.
        unit_price: Price per unit in USD.

    Returns:
        Total price (quantity * unit_price).
    """
    return quantity * unit_price


total = calculate_total(3, 29.99)
print(f"Total: ${total:.2f}")


# Multiple return values — Python returns a tuple
def min_max(numbers: List[float]):
    """Return the minimum and maximum of a list."""
    return min(numbers), max(numbers)  # returns a tuple (min, max)


low, high = min_max([5, 2, 8, 1, 9, 3])  # unpack the tuple
print(f"Min: {low}, Max: {high}")


# =============================================================================
# 2. DEFAULT PARAMETER VALUES
# =============================================================================

print("\n--- Default Parameters ---")

# Parameters with defaults are optional — callers can omit them.
# IMPORTANT: Defaults are evaluated ONCE at function definition time.
# Never use mutable objects (lists, dicts) as defaults — use None instead.


def connect_to_database(host: str, port: int = 5432, database: str = "mydb") -> str:
    """Build a database connection string."""
    return f"postgresql://{host}:{port}/{database}"


# Calling with only required args (uses defaults for the rest)
print(connect_to_database("localhost"))
# Overriding some defaults
print(connect_to_database("db.example.com", port=5433))
print(connect_to_database("db.example.com", database="testdb"))
# Override all defaults
print(connect_to_database("db.example.com", 3306, "production"))


# WRONG pattern — mutable default argument (bug: list is shared between calls!)
def bad_append(item, accumulator=[]):  # DON'T DO THIS
    accumulator.append(item)
    return accumulator


# CORRECT pattern — use None as default, create new list inside function
def good_append(item: Any, accumulator: Optional[List] = None) -> List:
    """Append item to accumulator list, creating it if not provided."""
    if accumulator is None:
        accumulator = []
    accumulator.append(item)
    return accumulator


print(good_append("a"))  # ['a']
print(good_append("b"))  # ['b']  — new list each time (correct!)


# =============================================================================
# 3. *ARGS AND **KWARGS
# =============================================================================

print("\n--- *args and **kwargs ---")


# *args — captures any number of positional arguments as a tuple
def sum_all(*numbers: float) -> float:
    """Sum any number of values."""
    print(f"  Received args: {numbers}")
    return sum(numbers)


print(f"sum_all(1, 2, 3) = {sum_all(1, 2, 3)}")
print(f"sum_all(10, 20)  = {sum_all(10, 20)}")


# **kwargs — captures any number of keyword arguments as a dict
def create_record(**fields) -> Dict:
    """Create a record dict from keyword arguments."""
    print(f"  Received kwargs: {fields}")
    return fields


rec = create_record(order_id=1001, customer="Alice", amount=250.00)
print(f"Record: {rec}")


# Combining regular params, *args, **kwargs
def etl_log(level: str, *messages: str, timestamp: bool = True, **metadata) -> str:
    """Flexible logging function combining all argument types."""
    msg = " | ".join(messages)
    ts = f"[{time.strftime('%H:%M:%S')}] " if timestamp else ""
    meta = " ".join(f"{k}={v}" for k, v in metadata.items())
    return f"{ts}[{level}] {msg} {meta}".strip()


print(etl_log("INFO", "Pipeline started", "Reading source"))
print(etl_log("ERROR", "Connection failed", timestamp=False, retry=3, host="db.local"))


# Unpacking: pass a list as *args or a dict as **kwargs
def add(a, b, c):
    return a + b + c


nums = [1, 2, 3]
params = {"a": 10, "b": 20, "c": 30}
print(f"add(*nums) = {add(*nums)}")  # unpack list
print(f"add(**params) = {add(**params)}")  # unpack dict


# =============================================================================
# 4. LAMBDA FUNCTIONS
# =============================================================================

print("\n--- Lambda Functions ---")

# Lambdas are anonymous, single-expression functions.
# Syntax: lambda arguments: expression
# Use lambdas for short, throwaway functions — especially with map/filter/sorted.


# Regular function
def double(x):
    return x * 2


# Equivalent lambda
double_lambda = lambda x: x * 2
print(f"double(5) = {double(5)}")
print(f"double_lambda(5) = {double_lambda(5)}")

# Multi-argument lambda
multiply = lambda x, y: x * y
print(f"multiply(4, 5) = {multiply(4, 5)}")

# Using lambda with sorted() — sort records by a field
records = [
    {"name": "Carol", "amount": 390.00},
    {"name": "Alice", "amount": 250.00},
    {"name": "Bob", "amount": 175.50},
]
sorted_by_amount = sorted(records, key=lambda r: r["amount"])
print("Sorted by amount:", [r["name"] for r in sorted_by_amount])

sorted_by_name = sorted(records, key=lambda r: r["name"])
print("Sorted by name:", [r["name"] for r in sorted_by_name])

# Sort descending
sorted_desc = sorted(records, key=lambda r: r["amount"], reverse=True)
print("Sorted descending:", [r["name"] for r in sorted_desc])


# =============================================================================
# 5. MAP() AND FILTER()
# =============================================================================

print("\n--- map() and filter() ---")

# map(function, iterable) — apply a function to every item in an iterable
# Returns a map object (lazy iterator); use list() to materialize.

prices = [10.5, 25.0, 8.75, 30.0, 15.25]

# Apply 15% tax to all prices
with_tax = list(map(lambda p: round(p * 1.15, 2), prices))
print(f"Original prices: {prices}")
print(f"With 15% tax:    {with_tax}")

# Clean a list of strings (strip whitespace + uppercase)
raw_names = ["  alice  ", " BOB", "carol "]
cleaned = list(map(str.strip, raw_names))  # str.strip is a method reference
print(f"Cleaned names: {cleaned}")

# filter(function, iterable) — keep items where function returns True
high_prices = list(filter(lambda p: p > 15, prices))
print(f"Prices > 15: {high_prices}")

# Combining map + filter: get discounted prices for high-priced items
discounted_high = list(
    map(lambda p: round(p * 0.9, 2), filter(lambda p: p > 15, prices))
)
print(f"Discounted (10% off) high prices: {discounted_high}")

# Note: List comprehensions are often more readable than map/filter
discounted_comp = [round(p * 0.9, 2) for p in prices if p > 15]
print(f"Same result with comprehension:   {discounted_comp}")


# =============================================================================
# 6. DECORATORS
# =============================================================================

print("\n--- Decorators ---")

# A decorator is a function that wraps another function to add behavior.
# Common uses in data engineering: timing, logging, retry logic, caching.
# Syntax: @decorator_name above a function definition.


# --- Decorator 1: Timer ---
def timer(func):
    """Measure and print the execution time of a function."""

    @functools.wraps(func)  # preserve the original function's metadata
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"  [{func.__name__}] executed in {elapsed:.4f}s")
        return result

    return wrapper


@timer
def slow_query(n: int) -> int:
    """Simulate a slow database query."""
    time.sleep(0.01)  # simulate 10ms query
    return sum(range(n))


result = slow_query(10_000)
print(f"  Query result: {result}")


# --- Decorator 2: Logger ---
def log_call(func):
    """Log function calls with arguments and return values."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        args_repr = [repr(a) for a in args]
        kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
        all_args = ", ".join(args_repr + kwargs_repr)
        print(f"  Calling {func.__name__}({all_args})")
        result = func(*args, **kwargs)
        print(f"  {func.__name__} returned {result!r}")
        return result

    return wrapper


@log_call
def load_records(source: str, limit: int = 100) -> int:
    """Simulate loading records from a source."""
    return limit  # pretend we loaded `limit` records


load_records("customers.csv", limit=50)


# --- Decorator 3: Retry ---
def retry(max_attempts: int = 3, delay: float = 0.1):
    """Retry a function on exception, up to max_attempts times."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    print(f"  Attempt {attempt} failed: {e}")
                    if attempt < max_attempts:
                        time.sleep(delay)
            raise last_error  # re-raise after all attempts exhausted

        return wrapper

    return decorator


# Simulated flaky function (fails first 2 times, succeeds on 3rd)
_attempt_count = 0


@retry(max_attempts=3, delay=0.05)
def flaky_api_call() -> str:
    """Simulate an unreliable API call."""
    global _attempt_count
    _attempt_count += 1
    if _attempt_count < 3:
        raise ConnectionError(f"Connection refused (attempt {_attempt_count})")
    return "{'status': 'ok', 'data': [...]}"


try:
    result = flaky_api_call()
    print(f"  API call succeeded: {result}")
except ConnectionError as e:
    print(f"  API call failed: {e}")


# Stacking decorators
@timer
@log_call
def transform_data(records: list) -> list:
    """Apply transformations to a list of records."""
    return [r * 2 for r in records]


transform_data([1, 2, 3])


# =============================================================================
# 7. GENERATORS
# =============================================================================

print("\n--- Generators ---")

# Generators are functions that use 'yield' instead of 'return'.
# They produce values ONE AT A TIME and pause between yields.
# Perfect for processing large datasets without loading everything into memory.


# Simple generator
def countdown(n: int) -> Generator[int, None, None]:
    """Yield numbers from n down to 1."""
    while n > 0:
        yield n
        n -= 1


print("Countdown:")
for num in countdown(5):
    print(f"  {num}", end=" ")
print()


# Generator for processing data in batches
def read_in_batches(data: List, batch_size: int) -> Generator[List, None, None]:
    """Yield successive batches of `batch_size` items from `data`."""
    for i in range(0, len(data), batch_size):
        yield data[i : i + batch_size]


all_records = list(range(1, 18))  # 17 records
print("\nBatch processing:")
for batch_num, batch in enumerate(read_in_batches(all_records, batch_size=5), start=1):
    print(f"  Batch {batch_num}: {batch}")


# Generator pipeline — chain generators for memory-efficient ETL
def read_numbers(limit: int):
    """Simulate reading numbers from a data source."""
    for i in range(1, limit + 1):
        yield i


def filter_even(numbers):
    """Keep only even numbers."""
    for n in numbers:
        if n % 2 == 0:
            yield n


def square(numbers):
    """Square each number."""
    for n in numbers:
        yield n**2


# Chain generators — nothing is computed until we consume the pipeline
pipeline = square(filter_even(read_numbers(10)))
print("\nGenerator pipeline (even squares 1-10):")
print(list(pipeline))

# Generator expressions (lazy list comprehensions using ())
large_sum = sum(x**2 for x in range(1_000_000) if x % 7 == 0)
print(f"\nSum of squares of multiples of 7 up to 1M: {large_sum}")


# =============================================================================
# 8. TYPE HINTS
# =============================================================================

print("\n--- Type Hints ---")

# Type hints (PEP 484) annotate function signatures for documentation and tooling.
# They are NOT enforced at runtime, but tools like mypy can check them statically.


def parse_amount(value: Union[str, float, int]) -> Optional[float]:
    """
    Parse an amount value to float.

    Handles strings like "$1,234.56", "1234.56", and numeric types.
    Returns None if parsing fails.
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        # Remove currency symbols and commas
        cleaned = value.replace("$", "").replace(",", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


test_values = ["$1,234.56", "250.00", 100, 75.5, "N/A", None, "  $99.9  "]
for v in test_values:
    parsed = parse_amount(v)
    print(f"  parse_amount({v!r:15}) = {parsed}")


# =============================================================================
# MAIN DEMO
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("PRACTICAL DEMO: ETL Functions Pipeline")
    print("=" * 60)

    # Define each ETL phase as a separate function

    def extract(source: List[Dict]) -> List[Dict]:
        """Extract: return a copy of raw source data."""
        print(f"\n[EXTRACT] Reading {len(source)} records from source")
        return source.copy()

    def transform(records: List[Dict]) -> List[Dict]:
        """
        Transform phase:
          - Remove records with missing amounts
          - Parse amounts to float
          - Add a 'total_with_tax' computed column
          - Uppercase the region field
        """
        transformed = []
        skipped = 0
        for rec in records:
            amount = parse_amount(rec.get("amount"))
            if amount is None:
                skipped += 1
                continue
            transformed.append(
                {
                    "id": rec["id"],
                    "region": rec["region"].upper(),
                    "amount": amount,
                    "total_with_tax": round(amount * 1.08, 2),
                }
            )
        print(f"[TRANSFORM] {len(transformed)} records transformed, {skipped} skipped")
        return transformed

    def validate(records: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """Validate: separate valid and invalid records."""
        valid, invalid = [], []
        for rec in records:
            if rec["amount"] <= 0:
                invalid.append({**rec, "error": "non-positive amount"})
            else:
                valid.append(rec)
        print(f"[VALIDATE] {len(valid)} valid, {len(invalid)} invalid")
        return valid, invalid

    def load(records: List[Dict], destination: str = "output") -> int:
        """Load: simulate writing records to a destination."""
        print(f"[LOAD] Writing {len(records)} records to '{destination}'")
        for rec in records:
            print(f"  → {rec}")
        return len(records)

    # Raw source data
    source_data = [
        {"id": 1, "region": "north", "amount": "$1,500.00"},
        {"id": 2, "region": "south", "amount": "N/A"},
        {"id": 3, "region": "east", "amount": "250.75"},
        {"id": 4, "region": "west", "amount": -100},  # invalid
        {"id": 5, "region": "north", "amount": 890.00},
    ]

    # Run the pipeline
    raw = extract(source_data)
    transformed = transform(raw)
    valid_recs, invalid_recs = validate(transformed)
    loaded_count = load(valid_recs, "sales_db")

    print(f"\nPipeline complete. {loaded_count} records loaded.")
