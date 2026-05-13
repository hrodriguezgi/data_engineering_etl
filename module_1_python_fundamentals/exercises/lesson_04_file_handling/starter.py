"""Exercise 04 starter: file handling with CSV and JSON."""

from pathlib import Path
from typing import Dict, List


def transform_rows(rows: List[Dict]) -> List[Dict]:
    """Add total field to each row."""
    transformed = []
    # TODO
    return transformed


def run() -> Dict:
    base_dir = Path(__file__).parent
    input_path = base_dir / "sales_input.csv"
    output_path = base_dir / "sales_output.csv"
    summary_path = base_dir / "run_summary.json"

    # TODO: read input CSV, transform rows, write output CSV, write JSON summary

    return {"rows_processed": 0, "grand_total": 0.0}


if __name__ == "__main__":
    summary = run()
    print(summary)
