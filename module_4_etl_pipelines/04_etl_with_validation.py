# %% [markdown]
# # Module 4 - Lesson 4: ETL with Data Validation
#
# Data validation ensures data meets defined quality standards
# **before** it's loaded into a target system.
#
# Bad data loaded to production causes expensive downstream problems:
# - Wrong analytics and reports
# - Failed integrations
# - Loss of trust in the data
#
# **What You'll Learn:**
# - Building a validation framework
# - Schema validation (required fields, types)
# - Business rule validation (domain logic)
# - Statistical validation (outlier detection)
# - Quality reporting and quarantine patterns

import logging
import pandas as pd
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Tuple
from sqlalchemy import create_engine

MODULE_DIR = Path(__file__).parent
DATA_DIR = MODULE_DIR / "data"
DB_PATH = MODULE_DIR / "etl_validated.db"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("etl_validation")


# %% [markdown]
# ## Problem 1: Loading Bad Data and Discovering It Too Late
#
# **Scenario:** Your pipeline loads 1 million rows with invalid data.
# Two weeks later, an analyst finds that half the prices are NULL or negative.
# Now you have to:
# - Identify which records are bad
# - Recalculate all downstream reports
# - Figure out what went wrong
#
# **The Cost:** Data corruption, lost time, reputational damage.

# %%
# WRONG: No validation — just load everything
test_sales = pd.DataFrame({
    "id": [1, 2, 3, 4],
    "product": ["Laptop", "Monitor", "Keyboard", None],  # Missing product
    "price": [999, 299, "abc", -50],  # Invalid price, negative price
    "qty": [2, 1, 0, 1],  # qty = 0 is unrealistic
})

print("WRONG: No validation, just load everything:")
print(test_sales)
print("  If this goes to production, you won't catch the problems until too late!\n")

# %%
# RIGHT: Validate before loading, quarantine bad records
print("CORRECT: Validate, report, quarantine bad records:")
print("  [More examples below with the validation framework]\n")


# %% [markdown]
# ## Validation Rules Framework
#
# A reusable system for checking data quality consistently.

# %%
@dataclass
class ValidationRule:
    """
    Represents a single validation rule.

    Attributes:
        name: Human-readable rule name
        description: What this rule checks
        check: Function that takes DataFrame and returns boolean mask
               (True = VALID, False = INVALID)
        severity: "error" = reject record; "warning" = flag but keep
    """
    name: str
    description: str
    check: Callable[[pd.DataFrame], pd.Series]
    severity: str = "error"


@dataclass
class ValidationReport:
    """Collects and summarizes validation results."""
    total_records: int = 0
    valid_records: int = 0
    invalid_records: int = 0
    warning_records: int = 0
    rule_results: List[Dict] = field(default_factory=list)

    def add_rule_result(self, rule: ValidationRule, failures: int, warning: bool = False):
        self.rule_results.append({
            "rule": rule.name,
            "description": rule.description,
            "severity": rule.severity,
            "failures": failures,
            "failure_rate": round(failures / max(self.total_records, 1) * 100, 2),
        })

    def summary(self) -> str:
        """Generate a formatted quality report."""
        lines = [
            "=" * 60,
            "DATA QUALITY REPORT",
            "=" * 60,
            f"  Total records:    {self.total_records}",
            f"  Valid records:    {self.valid_records}",
            f"  Invalid records:  {self.invalid_records}",
            f"  Warning records:  {self.warning_records}",
            f"  Quality score:    {self.valid_records/max(self.total_records,1)*100:.1f}%",
            "",
            "Rule Results:",
        ]
        for r in self.rule_results:
            icon = "✓" if r["failures"] == 0 else ("⚠" if r["severity"] == "warning" else "✗")
            lines.append(
                f"  {icon} [{r['severity'].upper():7s}] {r['rule']:30s} "
                f"{r['failures']:3d} failures ({r['failure_rate']:.1f}%)"
            )
        lines.append("=" * 60)
        return "\n".join(lines)


# %% [markdown]
# ## The DataValidator Class
#
# Runs all rules and produces: valid records, invalid records, quality report.

# %%
class DataValidator:
    """
    Validates a DataFrame against a set of rules.

    Usage:
        validator = DataValidator()
        validator.add_rule(ValidationRule(...))
        valid_df, invalid_df, report = validator.validate(df)
    """

    def __init__(self, name: str = "validator"):
        self.name = name
        self.rules: List[ValidationRule] = []

    def add_rule(self, rule: ValidationRule) -> "DataValidator":
        """Add a validation rule. Returns self for method chaining."""
        self.rules.append(rule)
        return self

    def validate(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, ValidationReport]:
        """
        Run all validation rules against the DataFrame.

        Returns:
            Tuple of (valid_df, invalid_df, report).
            Adds '_validation_errors' and '_validation_warnings' columns.
        """
        report = ValidationReport(total_records=len(df))
        df = df.copy()

        # Track per-row failure messages
        error_messages = {idx: [] for idx in df.index}
        warning_messages = {idx: [] for idx in df.index}

        # Run each rule
        for rule in self.rules:
            try:
                valid_mask = rule.check(df)
                failures = (~valid_mask).sum()

                report.add_rule_result(rule, failures)

                if failures > 0:
                    failing_indices = df[~valid_mask].index
                    for idx in failing_indices:
                        if rule.severity == "error":
                            error_messages[idx].append(rule.name)
                        else:
                            warning_messages[idx].append(rule.name)

                    logger.log(
                        logging.WARNING if rule.severity == "error" else logging.INFO,
                        f"[VALIDATE] Rule '{rule.name}': {failures} failures"
                    )

            except Exception as e:
                logger.error(f"[VALIDATE] Rule '{rule.name}' raised exception: {e}")

        # Build output DataFrames
        invalid_mask = pd.Series(
            {idx: len(msgs) > 0 for idx, msgs in error_messages.items()}
        )
        warning_mask = pd.Series(
            {idx: len(msgs) > 0 for idx, msgs in warning_messages.items()}
        )

        # Add error and warning columns
        df["_validation_errors"] = [
            "; ".join(error_messages[idx]) if error_messages[idx] else None
            for idx in df.index
        ]
        df["_validation_warnings"] = [
            "; ".join(warning_messages[idx]) if warning_messages[idx] else None
            for idx in df.index
        ]

        valid_df = df[~invalid_mask].copy()
        invalid_df = df[invalid_mask].copy()

        report.valid_records = len(valid_df)
        report.invalid_records = len(invalid_df)
        report.warning_records = int(warning_mask.sum())

        return valid_df, invalid_df, report


# %% [markdown]
# ## Define Validation Rules for Sales Data

# %%
def build_sales_validator() -> DataValidator:
    """
    Build a DataValidator configured with sales-specific rules.

    Rules cover:
    - Schema validation (required fields, types)
    - Business rules (positive prices, valid discounts)
    - Statistical checks (outlier detection, reasonable ranges)
    """
    validator = DataValidator("sales_validator")

    # --- Required Fields (Error) ---

    validator.add_rule(ValidationRule(
        name="required_id",
        description="'id' must be present and non-null",
        check=lambda df: df["id"].notna(),
        severity="error"
    ))

    validator.add_rule(ValidationRule(
        name="required_product_name",
        description="'product_name' must be non-null and non-empty",
        check=lambda df: df["product_name"].notna() & (df["product_name"].str.strip() != ""),
        severity="error"
    ))

    validator.add_rule(ValidationRule(
        name="required_sale_date",
        description="'sale_date' must be a valid date",
        check=lambda df: df["sale_date"].notna(),
        severity="error"
    ))

    # --- Type Rules (Error) ---

    validator.add_rule(ValidationRule(
        name="numeric_qty",
        description="'qty' must be numeric",
        check=lambda df: pd.to_numeric(df["qty"], errors="coerce").notna(),
        severity="error"
    ))

    validator.add_rule(ValidationRule(
        name="numeric_price",
        description="'price' must be numeric",
        check=lambda df: pd.to_numeric(df["price"], errors="coerce").notna(),
        severity="error"
    ))

    # --- Business Rules (Error) ---

    validator.add_rule(ValidationRule(
        name="positive_price",
        description="'price' must be > 0",
        check=lambda df: pd.to_numeric(df["price"], errors="coerce") > 0,
        severity="error"
    ))

    validator.add_rule(ValidationRule(
        name="positive_qty",
        description="'qty' must be >= 1",
        check=lambda df: pd.to_numeric(df["qty"], errors="coerce") >= 1,
        severity="error"
    ))

    # --- Business Rules (Warning) ---

    validator.add_rule(ValidationRule(
        name="valid_discount",
        description="'discount' must be between 0.0 and 1.0",
        check=lambda df: (
            pd.to_numeric(df["discount"], errors="coerce").fillna(0).between(0.0, 1.0)
        ),
        severity="warning"
    ))

    validator.add_rule(ValidationRule(
        name="valid_region",
        description="'region' must be in known values",
        check=lambda df: df["region"].str.strip().str.title().isin(
            ["North", "South", "East", "West"]
        ) | df["region"].isna(),
        severity="warning"
    ))

    validator.add_rule(ValidationRule(
        name="recommended_customer_id",
        description="'customer_id' recommended (warning if missing)",
        check=lambda df: df["customer_id"].notna() & (df["customer_id"] != ""),
        severity="warning"
    ))

    # --- Statistical Rules (Warning) ---

    validator.add_rule(ValidationRule(
        name="price_not_outlier",
        description="'price' should be <= 5000 (flag unusually high)",
        check=lambda df: pd.to_numeric(df["price"], errors="coerce") <= 5000,
        severity="warning"
    ))

    validator.add_rule(ValidationRule(
        name="qty_reasonable",
        description="'qty' should be <= 100 (flag unrealistic orders)",
        check=lambda df: pd.to_numeric(df["qty"], errors="coerce") <= 100,
        severity="warning"
    ))

    return validator


# %% [markdown]
# ## Extract, Transform, and Load

# %%
def extract_raw(filepath: Path) -> pd.DataFrame:
    """Extract raw data — read everything as strings."""
    df = pd.read_csv(filepath, dtype=str, keep_default_na=False).replace("", None)
    logger.info(f"[EXTRACT] {len(df)} rows from {filepath.name}")
    return df


def minimal_transform(df: pd.DataFrame) -> pd.DataFrame:
    """
    Minimal transforms before validation.
    Only type parsing — no business logic.
    """
    df = df.copy()
    df["qty"] = pd.to_numeric(df["qty"], errors="coerce")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["discount"] = pd.to_numeric(df["discount"], errors="coerce").fillna(0.0)
    df["sale_date"] = pd.to_datetime(df["sale_date"], errors="coerce")
    return df


def enrich_valid(df: pd.DataFrame) -> pd.DataFrame:
    """Apply enrichment only to records that passed validation."""
    df = df.copy()
    df["qty"] = df["qty"].astype(int)
    df["net_amount"] = (df["qty"] * df["price"] * (1 - df["discount"])).round(2)
    df["_loaded_at"] = datetime.now(timezone.utc).isoformat()
    return df


# %% [markdown]
# ## Load Validated and Quarantined Records

# %%
def load_to_db(valid_df: pd.DataFrame, invalid_df: pd.DataFrame, engine) -> dict:
    """
    Load valid and quarantined records to separate tables.

    - validated_sales: passed all validation
    - quarantine_sales: failed validation (for investigation)
    """
    stats = {}

    # Load valid records
    clean_cols = [c for c in valid_df.columns if not c.startswith("_validation")]
    valid_clean = valid_df[clean_cols].copy()
    valid_clean.to_sql("validated_sales", con=engine, if_exists="replace", index=False)
    stats["valid_rows"] = len(valid_clean)

    # Load quarantine (invalid records)
    if len(invalid_df) > 0:
        invalid_df.to_sql("quarantine_sales", con=engine, if_exists="replace", index=False)
    stats["quarantine_rows"] = len(invalid_df)

    logger.info(f"[LOAD] {stats['valid_rows']} → validated_sales, "
                f"{stats['quarantine_rows']} → quarantine_sales")
    return stats


# %% [markdown]
# ## Run the Full Validation Pipeline

# %%
if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("ETL WITH VALIDATION PIPELINE")
    logger.info("=" * 60)

    # 1. Extract
    raw_df = extract_raw(DATA_DIR / "raw_sales.csv")

    # 2. Minimal transform (parse types)
    df = minimal_transform(raw_df)

    # 3. Validate
    validator = build_sales_validator()
    valid_df, invalid_df, report = validator.validate(df)

    # %% [markdown]
    # ## Quality Report

    # %%
    print("\n" + report.summary())

    # %% [markdown]
    # ## Quarantined Records

    # %%
    if len(invalid_df) > 0:
        print(f"\n[Quarantined Records] ({len(invalid_df)} rows):")
        quarantine_view = invalid_df[["id", "product_name", "qty", "price",
                                       "discount", "_validation_errors",
                                       "_validation_warnings"]].copy()
        print(quarantine_view.to_string())

    # %% [markdown]
    # ## Valid Records with Warnings

    # %%
    warned = valid_df[valid_df["_validation_warnings"].notna()]
    if len(warned) > 0:
        print(f"\n[Valid Records with Warnings] ({len(warned)} rows):")
        print(warned[["id", "product_name", "price", "_validation_warnings"]].to_string())

    # %% [markdown]
    # ## Load and Verify

    # %%
    # Enrich the valid records before loading
    valid_enriched = enrich_valid(valid_df)

    # Load to database
    engine = create_engine(f"sqlite:///{DB_PATH}")
    load_stats = load_to_db(valid_enriched, invalid_df, engine)
    print(f"\n[Load Stats]: {load_stats}")

    # Verify
    validated = pd.read_sql("SELECT * FROM validated_sales ORDER BY id", con=engine)
    print(f"\n[Validated Sales] ({len(validated)} rows):")
    print(validated[["id", "product_name", "qty", "price", "net_amount"]].to_string())

    # %% [markdown]
    # ## Final Quality Metrics

    # %%
    print("\n[Data Quality Summary]")
    print(f"  Input rows:        {len(raw_df)}")
    print(f"  Valid rows:        {len(valid_df)} ({len(valid_df)/len(raw_df)*100:.0f}%)")
    print(f"  Quarantined:       {len(invalid_df)} ({len(invalid_df)/len(raw_df)*100:.0f}%)")
    print(f"  Warnings issued:   {report.warning_records}")

    # Cleanup
    engine.dispose()
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"\n✓ Cleaned up {DB_PATH.name}")
