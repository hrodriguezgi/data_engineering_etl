"""
Module 1 - Lesson 2: Control Flow
==================================
Control flow determines the *order* in which statements execute.
In data engineering, control flow is used to:
  - Filter records that meet certain criteria
  - Iterate over rows, files, or batches
  - Skip or break out of loops when conditions are met
  - Build transformation logic with conditionals

Topics covered:
  - if / elif / else statements
  - for loops (iterating over sequences)
  - while loops (iterating until a condition is false)
  - break and continue statements
  - List comprehensions
  - Dictionary comprehensions
  - Set comprehensions
  - Generator expressions
  - The walrus operator (:=) — Python 3.8+
"""

# =============================================================================
# 1. IF / ELIF / ELSE
# =============================================================================

print("--- if / elif / else ---")

# Basic if-else
temperature = 72

if temperature > 90:
    status = "hot"
elif temperature > 70:
    status = "warm"
elif temperature > 50:
    status = "cool"
else:
    status = "cold"

print(f"Temperature {temperature}°F is {status}")

# One-liner (ternary / conditional expression)
# Syntax: value_if_true if condition else value_if_false
label = "high" if temperature > 80 else "normal"
print(f"Label: {label}")

# Chained comparisons — very Pythonic
score = 85
if 80 <= score < 90:
    grade = "B"
elif 90 <= score <= 100:
    grade = "A"
else:
    grade = "C or below"
print(f"Score {score} = Grade {grade}")

# Checking types and None
def describe_value(val):
    """Describe an arbitrary value — common in data validation."""
    if val is None:
        return "null/missing"
    elif isinstance(val, bool):   # check bool before int (bool is subclass of int!)
        return f"boolean: {val}"
    elif isinstance(val, int):
        return f"integer: {val}"
    elif isinstance(val, float):
        return f"float: {val}"
    elif isinstance(val, str):
        return f"string: '{val}'"
    elif isinstance(val, (list, tuple)):
        return f"sequence with {len(val)} items"
    else:
        return f"other type: {type(val).__name__}"

for v in [None, True, 42, 3.14, "hello", [1, 2, 3]]:
    print(f"  {describe_value(v)}")


# =============================================================================
# 2. FOR LOOPS
# =============================================================================

print("\n--- for loops ---")

# Iterating over a list
products = ["laptop", "mouse", "keyboard", "monitor"]
print("Products:")
for product in products:
    print(f"  - {product.capitalize()}")

# enumerate() — get both index and value
print("\nIndexed products:")
for i, product in enumerate(products, start=1):   # start=1 for 1-based index
    print(f"  {i}. {product}")

# zip() — iterate over multiple sequences in parallel
prices = [999.99, 29.99, 79.99, 349.99]
print("\nProducts with prices:")
for product, price in zip(products, prices):
    print(f"  {product:12s} ${price:8.2f}")

# Iterating over a dict
record = {"order_id": 1001, "customer": "Alice", "amount": 250.00}
print("\nDict items:")
for key, value in record.items():
    print(f"  {key}: {value}")

# range() — generate a sequence of numbers
print("\nrange(5):", list(range(5)))          # [0, 1, 2, 3, 4]
print("range(1,6):", list(range(1, 6)))      # [1, 2, 3, 4, 5]
print("range(0,10,2):", list(range(0, 10, 2)))  # [0, 2, 4, 6, 8] (step=2)

# Processing rows in a dataset (simulated)
dataset = [
    {"id": 1, "value": 100, "status": "active"},
    {"id": 2, "value": None, "status": "inactive"},
    {"id": 3, "value": 250, "status": "active"},
    {"id": 4, "value": 75, "status": "active"},
]

print("\nProcessing active records:")
for row in dataset:
    if row["status"] == "active" and row["value"] is not None:
        print(f"  Row {row['id']}: value = {row['value'] * 1.1:.2f} (10% markup)")


# =============================================================================
# 3. WHILE LOOPS
# =============================================================================

print("\n--- while loops ---")

# While loop — use when you don't know how many iterations you need
# Common use case: polling, retrying failed operations, pagination

# Simple counter
count = 0
while count < 5:
    print(f"  count = {count}")
    count += 1   # IMPORTANT: always update the condition variable!

# Simulating a batch processing loop
batch_size = 3
total_records = 10
offset = 0

print(f"\nSimulated batch processing ({total_records} records, batch_size={batch_size}):")
while offset < total_records:
    end = min(offset + batch_size, total_records)
    print(f"  Processing records {offset} to {end - 1}")
    offset += batch_size

# While with a flag variable — useful for complex exit conditions
print("\nWhile with exit flag:")
attempts = 0
max_attempts = 3
success = False

while not success and attempts < max_attempts:
    attempts += 1
    print(f"  Attempt {attempts}...")
    if attempts == 2:   # simulate success on attempt 2
        success = True

if success:
    print(f"  Succeeded on attempt {attempts}")
else:
    print(f"  Failed after {max_attempts} attempts")


# =============================================================================
# 4. BREAK AND CONTINUE
# =============================================================================

print("\n--- break and continue ---")

# break — exit the loop immediately
print("break example (find first negative):")
numbers = [5, 12, -3, 8, -1, 20]
for num in numbers:
    if num < 0:
        print(f"  Found first negative: {num}")
        break   # stop searching once found
    print(f"  {num} is positive")

# continue — skip the rest of the current iteration, go to next
print("\ncontinue example (skip None values):")
data = [10, None, 30, None, 50]
total = 0
for item in data:
    if item is None:
        print("  Skipping None value")
        continue    # skip None, go to next iteration
    total += item
print(f"  Total (ignoring None): {total}")

# for-else and while-else — the else block runs if the loop completed normally
# (i.e., was NOT exited by break). Useful for search patterns.
print("\nfor-else example (search for a value):")
target = 7
numbers_to_search = [1, 3, 5, 9, 11]
for num in numbers_to_search:
    if num == target:
        print(f"  Found {target}!")
        break
else:
    # This executes only if the loop finished without hitting 'break'
    print(f"  {target} not found in {numbers_to_search}")


# =============================================================================
# 5. LIST COMPREHENSIONS
# =============================================================================

print("\n--- List Comprehensions ---")

# Basic syntax: [expression for item in iterable]
# Optional filter: [expression for item in iterable if condition]
#
# List comprehensions are faster and more Pythonic than equivalent for-loops.

# Traditional for-loop approach:
squares_loop = []
for n in range(1, 6):
    squares_loop.append(n ** 2)

# Equivalent list comprehension:
squares_comp = [n ** 2 for n in range(1, 6)]
print(f"Squares: {squares_comp}")

# With a filter condition
even_squares = [n ** 2 for n in range(1, 11) if n % 2 == 0]
print(f"Even squares: {even_squares}")

# String transformation
names = ["  alice  ", "BOB", " Carol"]
cleaned_names = [name.strip().title() for name in names]
print(f"Cleaned names: {cleaned_names}")

# Extracting a column from a list of dicts (very common in ETL)
records = [
    {"id": 1, "name": "Alice", "amount": 250.0},
    {"id": 2, "name": "Bob", "amount": 175.5},
    {"id": 3, "name": "Carol", "amount": 390.0},
]
amounts = [r["amount"] for r in records]
print(f"Amounts: {amounts}, Total: {sum(amounts):.2f}")

# Filter records by condition
high_value = [r for r in records if r["amount"] > 200]
print(f"High-value records: {[r['name'] for r in high_value]}")

# Nested list comprehension (flatten a 2D list)
matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
flat = [cell for row in matrix for cell in row]
print(f"Flattened matrix: {flat}")


# =============================================================================
# 6. DICTIONARY COMPREHENSIONS
# =============================================================================

print("\n--- Dictionary Comprehensions ---")

# Syntax: {key_expr: value_expr for item in iterable if condition}

# Build a price lookup dict from two lists
product_names = ["laptop", "mouse", "keyboard"]
product_prices = [999.99, 29.99, 79.99]
price_lookup = {name: price for name, price in zip(product_names, product_prices)}
print(f"Price lookup: {price_lookup}")

# Apply a 10% discount to all prices
discounted = {name: round(price * 0.9, 2) for name, price in price_lookup.items()}
print(f"Discounted prices: {discounted}")

# Invert a dictionary (swap keys and values)
original = {"a": 1, "b": 2, "c": 3}
inverted = {v: k for k, v in original.items()}
print(f"Inverted dict: {inverted}")

# Extract specific keys from a dict
full_record = {"id": 1, "name": "Alice", "email": "alice@example.com", "age": 30, "city": "NY"}
keep_keys = {"id", "name", "city"}
subset = {k: v for k, v in full_record.items() if k in keep_keys}
print(f"Subset: {subset}")


# =============================================================================
# 7. SET COMPREHENSIONS
# =============================================================================

print("\n--- Set Comprehensions ---")

# Syntax: {expression for item in iterable if condition}
# Results in a set — automatically de-duplicated

data_with_dupes = ["Electronics", "Clothing", "Electronics", "Food", "Clothing"]
unique_categories = {cat.upper() for cat in data_with_dupes}
print(f"Unique categories: {unique_categories}")

# Find unique lengths of words
words = ["data", "engineering", "ETL", "pipeline", "transform", "data"]
unique_lengths = {len(w) for w in words}
print(f"Unique word lengths: {sorted(unique_lengths)}")


# =============================================================================
# 8. GENERATOR EXPRESSIONS
# =============================================================================

print("\n--- Generator Expressions ---")

# Generator expressions look like list comprehensions but use () instead of [].
# They are LAZY — they compute one item at a time and don't store all items
# in memory at once. This is critical when processing large datasets.

# List comprehension — creates the entire list in memory immediately
squares_list = [n ** 2 for n in range(10)]

# Generator expression — computes values on-demand
squares_gen = (n ** 2 for n in range(10))

print(f"List: {squares_list}")
print(f"Generator: {squares_gen}")   # just shows <generator object>
print(f"Generator sum (no full list in memory): {sum(squares_gen)}")

# Practical example: summing a large file without loading everything into memory
# Here we simulate with a list, but imagine this is a file with millions of lines
large_data = range(1_000_000)
total = sum(x * 2 for x in large_data if x % 3 == 0)  # generator expression
print(f"Sum of 2x for multiples of 3 up to 1M: {total}")


# =============================================================================
# 9. THE WALRUS OPERATOR (:=) — Python 3.8+
# =============================================================================

print("\n--- Walrus Operator (:=) ---")

# The walrus operator assigns AND returns a value in a single expression.
# Useful to avoid computing a value twice or making code more concise.

# Without walrus: compute length twice
data_list = [1, 2, 3, 4, 5]
if len(data_list) > 3:
    print(f"Long list with {len(data_list)} items")  # len() called twice

# With walrus: compute once, use in condition and body
if (n := len(data_list)) > 3:
    print(f"Long list with {n} items")   # n already computed

# Common use case: reading a file in chunks (simulated here)
print("\nSimulated chunked reading with walrus:")
source = iter(range(12))  # imagine this is a file reader
chunk_size = 4
chunk_num = 0
while chunk := list(item for _, item in zip(range(chunk_size), source)):
    chunk_num += 1
    print(f"  Chunk {chunk_num}: {chunk}")


# =============================================================================
# MAIN DEMO
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("PRACTICAL DEMO: ETL Data Filtering and Routing")
    print("=" * 60)

    # Simulated raw data records with various quality issues
    raw_data = [
        {"id": 1, "region": "North", "amount": 1500.00, "status": "complete"},
        {"id": 2, "region": "South", "amount": None,    "status": "complete"},
        {"id": 3, "region": "North", "amount": 200.00,  "status": "cancelled"},
        {"id": 4, "region": "East",  "amount": 9999.00, "status": "complete"},  # outlier
        {"id": 5, "region": "West",  "amount": 450.00,  "status": "complete"},
        {"id": 6, "region": "South", "amount": 325.00,  "status": "complete"},
        {"id": 7, "region": "East",  "amount": -50.00,  "status": "complete"},  # invalid
        {"id": 8, "region": "North", "amount": 780.00,  "status": "pending"},
    ]

    # Route records into different buckets using control flow
    valid_records = []
    invalid_records = []
    outliers = []
    AMOUNT_THRESHOLD = 5000  # business rule: flag as outlier above this

    for record in raw_data:
        # Skip non-complete records
        if record["status"] not in ("complete", "pending"):
            continue

        amount = record["amount"]

        # Validate: amount must not be None and must be non-negative
        if amount is None or amount < 0:
            invalid_records.append({**record, "rejection_reason": "invalid_amount"})
            continue

        # Flag outliers
        if amount > AMOUNT_THRESHOLD:
            outliers.append(record)
            continue

        valid_records.append(record)

    print(f"\nTotal raw records:   {len(raw_data)}")
    print(f"Valid records:       {len(valid_records)}")
    print(f"Invalid records:     {len(invalid_records)}")
    print(f"Outliers:            {len(outliers)}")

    # Group valid records by region using a dict comprehension + for loop
    regions = {r["region"] for r in valid_records}
    by_region = {
        region: [r for r in valid_records if r["region"] == region]
        for region in regions
    }

    print("\nValid records by region:")
    for region, recs in sorted(by_region.items()):
        total = sum(r["amount"] for r in recs)
        print(f"  {region:6s}: {len(recs)} records, total=${total:.2f}")
