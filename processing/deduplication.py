"""Duplicate detection and fingerprinting module."""

import hashlib
import re
from typing import Dict, List, Set, Tuple


def make_fingerprint(rec: dict) -> str:
    """Generate a deterministic deduplication hash for a record.

    Normalizes identifying fields by lowercasing, stripping punctuation,
    collapsing whitespace, and computing a SHA256 hex digest.

    Field rules:
        - Books to Scrape: source + name_or_title
        - Quotes to Scrape: source + author + name_or_title[:50]
        - Other sources: fallback to source + name_or_title

    Args:
        rec: Record dictionary.

    Returns:
        64-character SHA256 hex string fingerprint.
    """
    source = str(rec.get("source") or "")
    title = str(rec.get("name_or_title") or "")
    author = str(rec.get("author") or "")

    if source == "Books to Scrape":
        key = f"{source} {title}"
    elif source == "Quotes to Scrape":
        # First 50 chars of quote text prevents micro-discrepancies while uniquely identifying the quote
        truncated_text = title[:50]
        key = f"{source} {author} {truncated_text}"
    else:
        key = f"{source} {title}"

    # Lowercase and remove punctuation
    normalized_key = re.sub(r"[^\w\s]", "", key.lower())
    # Collapse consecutive whitespace characters
    normalized_key = " ".join(normalized_key.split())

    return hashlib.sha256(normalized_key.encode("utf-8")).hexdigest()


def find_duplicates(
    records: List[dict],
    flag_only: bool = False,
) -> Tuple[List[dict], List[dict]]:
    """Identify duplicate records using normalized fingerprinting.

    Args:
        records: List of record dictionaries.
        flag_only: If True, returns all records with an 'is_duplicate' boolean flag.
                   If False (default), returns unique records and duplicate records separately.

    Returns:
        Tuple of (unique_or_flagged_records, duplicate_records).
    """
    seen_fingerprints: Set[str] = set()
    unique_records: List[dict] = []
    duplicate_records: List[dict] = []
    flagged_records: List[dict] = []

    for rec in records:
        fp = make_fingerprint(rec)
        is_dupe = fp in seen_fingerprints

        if is_dupe:
            duplicate_records.append(rec)
            if flag_only:
                rec_copy = dict(rec)
                rec_copy["is_duplicate"] = True
                flagged_records.append(rec_copy)
        else:
            seen_fingerprints.add(fp)
            unique_records.append(rec)
            if flag_only:
                rec_copy = dict(rec)
                rec_copy["is_duplicate"] = False
                flagged_records.append(rec_copy)

    if flag_only:
        return flagged_records, duplicate_records
    return unique_records, duplicate_records
