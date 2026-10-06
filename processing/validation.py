"""Record validation module.

Checks records against business rules and identifies validation failures with detailed reasons.
"""

from typing import Dict, List, Set, Tuple

VALID_SOURCES: Set[str] = {"Books to Scrape", "Quotes to Scrape"}


def validate_record(rec: dict) -> List[str]:
    """Validate a single cleaned record and return a list of failure reasons.

    An empty list indicates that the record is valid.

    Args:
        rec: Dictionary representing a cleaned record.

    Returns:
        List of problem identifier strings.
    """
    problems: List[str] = []

    # 1. Source verification
    source = rec.get("source")
    if source not in VALID_SOURCES:
        problems.append("unknown_source")

    # 2. Required title / text check
    name_or_title = rec.get("name_or_title")
    if not name_or_title or not str(name_or_title).strip():
        problems.append("missing_name")

    # 3. Source URL verification
    source_url = rec.get("source_url")
    if not source_url or not str(source_url).startswith(("http://", "https://")):
        problems.append("invalid_url")

    # 4. Numeric price check (if price exists)
    price = rec.get("price")
    if price is not None:
        if not isinstance(price, (int, float)) or price < 0:
            problems.append("invalid_price")

    # 5. Rating range check (if rating exists)
    rating = rec.get("rating")
    if rating is not None:
        if not isinstance(rating, int) or rating not in (1, 2, 3, 4, 5):
            problems.append("invalid_rating")

    return problems


def validate_dataset(
    records: List[dict],
) -> Tuple[List[dict], List[Tuple[dict, List[str]]], Dict[str, int]]:
    """Validate a collection of records, partitioning into valid and rejected.

    Args:
        records: List of cleaned record dictionaries.

    Returns:
        Tuple of (valid_records, rejected_records_with_reasons, reason_counts).
    """
    valid: List[dict] = []
    rejected: List[Tuple[dict, List[str]]] = []
    reason_counts: Dict[str, int] = {
        "unknown_source": 0,
        "missing_name": 0,
        "invalid_url": 0,
        "invalid_price": 0,
        "invalid_rating": 0,
    }

    for rec in records:
        problems = validate_record(rec)
        if not problems:
            valid.append(rec)
        else:
            rejected.append((rec, problems))
            for p in problems:
                reason_counts[p] = reason_counts.get(p, 0) + 1

    return valid, rejected, reason_counts
