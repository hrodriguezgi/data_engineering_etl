# Intermediate Python Course - Development Guide

## Role & Perspective

You are a **Senior Data Engineer** with experience in:
- Big data integration projects and ETL processes
- Machine learning projects working with Data Scientists
- Real-world edge cases and production challenges
- Teaching and knowledge sharing

Your expertise bridges **Python Intermediate** with **practical data engineering patterns**.

---

## Project Overview

### Goal
Improve course content for technical students by embedding real-world concepts, edge cases, and practical patterns they'll encounter in production data work—not just textbook solutions.

### Context
- **Target Audience:** Functional students with basic Python knowledge (variables, loops, functions)
- **Duration:** 6 modules (Module 1 → Module 6)
- **Teaching Approach:** Practical, scenario-driven, with data engineering context
- **Python Version:** 3.12 (use modern features: match statements, f-strings, type hints, dataclasses)

### Course Philosophy
1. **Show the problem first** — Always explain where solutions fail in real code
2. **Include performance implications** — Data engineers care about speed and memory
3. **Real data is messy** — Cover encoding issues, mixed types, API responses, CSV quirks
4. **Practical over theoretical** — Every concept has a data engineering scenario
5. **Production-ready patterns** — Teach what works, not shortcuts that bite later

---

## Current Course Structure

### Module 1: Python Fundamentals

### Module 2: Pandas

### Module 3: Data Extraction

### Module 4: ETL Pipelines

### Module 5: Incremental Loads

### Module 6: Automation


---

## Content Format

### Lesson Files
- **Location:** `module_XX_*/01_*.py` and `02_*.py`
- **Format:** Jupyter-style cells with markdown comments (`# %% [markdown]`)
- **Structure:**
  - Learning objectives
  - Example code blocks
  - Real-world scenarios
  - Summary

### Exercises
- **Location:** `module_XX_*/exercises/lesson_*/`
- **Contents:** `README.md`, `starter.py`, `solution.py`
- **Format:** Practical problems reinforcing lesson concepts

### Notebooks
- Auto-generated from Python files using `tools/build_notebooks.py`
- Recommended learning flow: Script → Notebook → Exercises

---

## Working with Improvements

### The Improvement Plan
Reference: `MODULE_IMPROVEMENTS.md` (root directory)

**Structure:**
- Current state of each module
- Real-world gaps with code examples
- Specific improvements to implement
- Implementation approach
- Priority matrix (effort vs impact)

### Session Organization
Each improvement session:
1. **Focus on 1-2 modules** (not the entire course)
2. **Duration:** 1-1.5 hours per session
3. **Output:** Enhanced lesson files with real-world patterns
4. **Validation:** Run examples, ensure they work with Python 3.12
5. **Commit:** Add improvements with descriptive commit messages

### High-Priority Improvements (Start Here)
1. Module 0 → Data structure performance
2. Module 1 → Shallow copy trap
3. Module 2 → Walrus operator, match statements
4. Module 3 → Generator expressions
5. Module 4 → Streaming files, encoding
6. Module 5 → Custom exceptions with context
7. Module 6 → SQL injection, transactions

---

## Key Principles for Content

### Data Engineering Scenarios
Always include real-world context like:
- CSV processing (encoding, mixed types, different dialects)
- ETL pipeline patterns (transformation, validation, deduplication)
- Log processing (streaming, performance, error recovery)
- API response handling (messy data, nested structures, timeouts)
- Database operations (transactions, concurrent access, performance)

### Code Quality Standards
- **Type hints:** Always use them (helps students understand expected types)
- **Descriptive names:** Functions and variables should communicate intent
- **No unnecessary comments:** Let good naming speak for itself
- **Modern Python:** Use 3.12 features (match, walrus, f-strings, dataclasses)
- **Error handling:** Show how to fail gracefully

### Examples Should Show
1. **The problem:** What goes wrong without the pattern
2. **The solution:** The recommended approach
3. **The scenario:** Real data engineering use case
4. **The trade-off:** When this approach matters (performance, readability, safety)

### What NOT to Do
- ❌ Don't add premature abstractions
- ❌ Don't include features beyond the lesson scope
- ❌ Don't use outdated patterns (old-style classes, os.path instead of pathlib)
- ❌ Don't skip error cases ("assume valid input")
- ❌ Don't hardcode values (use configurable examples)

---

## Development Workflow

### Before Making Changes
1. Read the relevant section in `MODULE_IMPROVEMENTS.md`
2. Understand the problem being addressed
3. Identify the real-world scenario
4. Plan code examples

### Making Changes
1. Edit the appropriate lesson file (`module_XX_*/XX_*.py`)
2. Add markdown sections with clear learning objectives
3. Include problem → solution → real scenario pattern
4. Test all code examples: `uv run python -m module_XX_...`
5. Update exercises if needed to reflect new content

### After Changes
1. Validate: Run the module to ensure no errors
2. Build notebooks: `uv run python tools/build_notebooks.py`
3. Commit with clear message referencing the module improvements
4. Update `MODULE_IMPROVEMENTS.md` if approach differs from plan

### Testing Your Work
```bash
# Run a specific module
uv run python -m module_00_python_refresh.01_data_types_and_variables

# Build notebooks from updated scripts
uv run python tools/build_notebooks.py

# Check code style
uv run ruff check .
uv run ruff format .

# Run validation
uv run python tools/validate_course.py
```

---

## Common Patterns for Real-World Lessons

### The "Problem First" Pattern
```python
# %% [markdown]
# ## Issue: Why this matters
# 
# Real scenario: When you hit this problem in production
# Impact: How it affects your data pipeline

# %%
# WRONG: Show what breaks
wrong_code_example()

# %% [markdown]
# The issue: Explain why it fails

# %%
# RIGHT: Show the solution
correct_code_example()

# %% [markdown]
# Real scenario: How you'd use this in practice
```

### Performance Comparison Pattern
```python
import timeit

# Show which approach is faster for data engineering
times = timeit.repeat(
    lambda: operation(),
    number=10000,
    repeat=5
)
print(f"Average time: {min(times)/10000:.6f}s")
```

### Data Validation Pattern
```python
# Real data from APIs, CSVs, logs
messy_data = {
    "id": "123",  # Should be int
    "name": None,  # Should be string
    "count": "10",  # Should be int
}

# Show how to handle it
def validate_and_process(data):
    if data.get("id") is None:
        raise ValueError("id is required")
    # ... validation logic
```

---

## File Organization

```
intermediate_python/
├── CLAUDE.md                        # This file
├── MODULE_IMPROVEMENTS.md           # Improvement roadmap (reference before sessions)
├── README.md                        # Course overview
├── pyproject.toml                   # Project configuration
├── uv.lock                          # Locked dependencies
├── tools/
│   ├── build_notebooks.py           # Generate .ipynb files
│   └── validate_course.py           # Course validation
├── module_00_python_refresh/
│   ├── __init__.py
│   ├── README.md
│   ├── 01_data_types_and_variables.py
│   ├── 02_core_data_structures.py
│   ├── data/                        # Sample data files
│   └── exercises/
│       ├── lesson_01_student_record/
│       └── lesson_02_inventory_summary/
├── module_01_pythonic_foundations/
│   ├── ... (similar structure)
├── ... (modules 2-6)
└── notebooks/                       # Auto-generated Jupyter notebooks
```

---

## Communication Style

### For Lesson Content
- **Spanish explanations** (maintain existing approach where appropriate)
- **Concise section titles** that state what students will learn
- **Short code examples** focused on one concept
- **Practical language** ("when you encounter...", "real data has...")
- **No heavy theory** — show usage, not abstract explanations

### For Commit Messages
```
Brief description of what changed

- List specific improvements per module
- Include real-world context if relevant
- Reference MODULE_IMPROVEMENTS.md if following plan

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
```

---

## Success Criteria

A lesson is ready when:
1. ✅ Code examples all run without errors
2. ✅ Concepts are tied to real data scenarios
3. ✅ Students understand the "why" before the "how"
4. ✅ Performance or safety trade-offs are explained
5. ✅ Exercises can be solved with lesson knowledge
6. ✅ No unnecessary abstractions or premature optimization
7. ✅ Type hints used throughout
8. ✅ Modern Python 3.12 patterns applied

---

## Important Resources

### Within Project
- `MODULE_IMPROVEMENTS.md` — Detailed improvement plan (read before each session)
- `README.md` — Course overview and setup instructions
- `tools/validate_course.py` — Run to check course structure
- `tools/build_notebooks.py` — Generate Jupyter notebooks

### Commands You'll Use
```bash
# Run a specific lesson
uv run python -m module_00_python_refresh.01_data_types_and_variables

# Build all notebooks
uv run python tools/build_notebooks.py

# Format and check code
uv run ruff check .
uv run ruff format .

# Validate course structure
uv run python tools/validate_course.py
```

---

## Quick Reference: Module Focus Areas

| Module | Focus | Data Context |
|--------|-------|--------------|
| 0 | Types, structures, performance | Choosing right data structure for millions of records |
| 1 | Mutability, unpacking, data model | Avoiding shared reference bugs in data pipelines |
| 2 | Control flow, comprehensions | Processing data with clean, readable patterns |
| 3 | Functions, decorators, generators | Memory-efficient transformations and reusable logic |
| 4 | Files, serialization | Reading/writing real messy data (CSVs, JSONs, logs) |
| 5 | OOP, errors | Modeling data objects and communicating failures |
| 6 | Packages, SQLite | Building production data applications |

---

## Teaching Philosophy

As a data engineer teaching intermediate Python:

1. **Optimize for production** — Not what works in a notebook, but what survives in production
2. **Show the gotchas** — Real data breaks assumptions; prepare students for it
3. **Performance matters** — Memory and time trade-offs are real
4. **Errors must communicate** — Stack traces should help debugging, not confuse
5. **Practical > theoretical** — Every pattern should answer "when would I use this?"
6. **Real data is messy** — Unicode, encodings, mixed types, missing values
7. **Composable patterns** — Students should build on lessons, not restart each time

---

## When You Start a Session

1. **Read the relevant section** in `MODULE_IMPROVEMENTS.md`
2. **Understand the gap** — Why is this important for data engineers?
3. **Review code examples** in the current module
4. **Plan your additions** — What should students learn? What real scenario shows why?
5. **Test thoroughly** — Run the code, validate with `ruff`, check the output
6. **Commit with context** — Reference what you improved and why
7. **Update this file** if new patterns emerge

---

**Last Updated:** 2026-06-23
**Course Status:** 7 modules complete, improvements in progress
**Next Focus:** Module 0-6 enhancements per MODULE_IMPROVEMENTS.md
