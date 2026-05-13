"""Exercise 05 starter: error handling and logging."""

import logging
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

RAW_RECORDS = [
    {"id": 1, "amount": "250"},
    {"id": 2, "amount": "-10"},
    {"id": 3, "amount": "abc"},
    {"id": 4, "amount": None},
    {"id": 5, "amount": "30.5"},
]


def safe_parse_amount(value) -> Optional[float]:
    """Parse amount safely, return None if invalid."""
    # TODO
    return None


def process_records(records: List[Dict]) -> Dict:
    """Return summary with valid, invalid, and errors."""
    valid_count = 0
    errors = []

    # TODO

    summary = {
        "valid_count": valid_count,
        "invalid_count": len(errors),
        "errors": errors,
    }

    logger.info("valid=%s invalid=%s", summary["valid_count"], summary["invalid_count"])
    return summary


if __name__ == "__main__":
    print(process_records(RAW_RECORDS))
