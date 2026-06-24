# Exercise: Lesson 04 - Building a Validation Framework

## Objective

Build a reusable validation system that identifies data quality issues before loading to production.

## Scenario

You're processing customer registration data. Some records have:
- Missing required fields
- Invalid email formats
- Out-of-range ages
- Inconsistent data (e.g., birth_date in the future)

You need to:
1. Define validation rules
2. Run them against the dataset
3. Separate valid from invalid records
4. Generate a quality report

## Requirements

1. **Define ValidationRule class** with:
   - name: unique identifier
   - description: what it checks
   - check: function that returns boolean mask
   - severity: "error" (reject) or "warning" (flag)

2. **Implement validation rules** for customer data:
   - required_email (error)
   - valid_email_format (warning)
   - valid_age (error): 18-120
   - valid_birth_date (error): not in future
   - recommended_phone (warning): at least one contact method

3. **Create ValidationReport class** that:
   - Tracks total, valid, invalid, warned records
   - Summarizes results per rule
   - Generates readable report

4. **Test with sample data** and show:
   - Quality score
   - Rejection reasons
   - Warning messages

## Success Criteria

✅ Rules are applied consistently
✅ Valid and invalid records separated correctly
✅ Report shows actionable insights
✅ Severity levels (error/warning) work correctly
✅ Edge cases handled (null values, invalid dates, etc.)

## Sample Data

```
customer_id,email,age,birth_date,phone
C001,alice@example.com,28,1996-05-15,555-1234
C002,bob.example.com,31,1993-08-20,
C003,,45,1979-03-10,555-5678
C004,carol@example.com,150,1874-01-01,555-9999
C005,dave@example.com,22,2030-12-31,555-4444
C006,eve@example.com,35,1989-06-15,
```
