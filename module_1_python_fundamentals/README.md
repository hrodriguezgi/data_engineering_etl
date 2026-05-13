# Module 1 – Python Fundamentals

This module covers the Python concepts you'll use most in data engineering. Work through each file in order — every topic builds on the previous one.

## Files

| File | Key Concepts |
|------|-------------|
| `00_intro_python_data_engineering.py` | Python in data engineering, ETL phases (extract/transform/validate/load), mini end-to-end ETL demo |
| `01_variables_and_data_types.py` | Variables, strings, numbers, booleans, lists, dicts, tuples, sets, type conversion |
| `02_control_flow.py` | if/elif/else, for loops, while loops, comprehensions, break/continue |
| `03_functions.py` | Functions, args/kwargs, defaults, lambda, map/filter, decorators, generators |
| `04_file_handling.py` | Text files, CSV, JSON, context managers (`with` statement) |
| `05_error_handling.py` | try/except/finally, raising exceptions, custom exceptions, logging |

## Practice Assets

- Guided notebook:
  - `notebooks/00_guided_intro_python_data_engineering.ipynb`
  - `notebooks/01_guided_variables_and_data_types.ipynb`
  - `notebooks/02_guided_control_flow.ipynb`
  - `notebooks/03_guided_functions.ipynb`
  - `notebooks/04_guided_file_handling.ipynb`
  - `notebooks/05_guided_error_handling.ipynb`
- Exercises:
  - `exercises/lesson_01_data_types/` (`starter.py`)
  - `exercises/lesson_02_control_flow/` (`starter.py`)
  - `exercises/lesson_03_functions/` (`starter.py`)
  - `exercises/lesson_04_file_handling/` (`starter.py`)
  - `exercises/lesson_05_error_handling/` (`starter.py`)

## How to Run

```bash
# Run any file directly
python 01_variables_and_data_types.py

# Or run interactively to inspect variables
python -i 01_variables_and_data_types.py
```

## Learning Tips

- Read every comment — they explain the *why*, not just the *what*.
- After running a file, open the Python REPL and experiment with the concepts.
- The `if __name__ == '__main__':` block at the bottom of each file shows a practical demonstration of the concepts covered.


