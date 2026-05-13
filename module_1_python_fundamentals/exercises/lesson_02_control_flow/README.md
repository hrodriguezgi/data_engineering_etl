# Exercise 02 - Control Flow and Data Routing

## Goal
Route records to different outputs using conditionals and loops.

## Files
- `starter.py`: your template to complete.
- `solution.py`: one reference implementation.

## Business Rules
Given each record:
- If `status != "active"`, ignore it.
- If `amount` is missing or invalid, send to `invalid`.
- If `amount >= 200`, send to `priority`.
- Otherwise send to `standard`.

## Acceptance Criteria
1. Return a dict with `priority`, `standard`, `invalid` lists.
2. Add `amount` as float for valid routed records.
3. Return a summary dict with counts for each list.
4. Print routed ids by bucket in `__main__`.

## Expected Count (for sample)
- `priority = 2`
- `standard = 1`
- `invalid = 1`
