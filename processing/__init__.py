"""Processing package for data cleaning, validation, and deduplication."""

from processing.cleaning import (
    clean_text,
    strip_quotes,
    clean_price,
    clean_rating,
    clean_tags,
    normalize_url,
    clean_record,
)
from processing.validation import validate_record, validate_dataset
from processing.deduplication import make_fingerprint, find_duplicates

__all__ = [
    "clean_text",
    "strip_quotes",
    "clean_price",
    "clean_rating",
    "clean_tags",
    "normalize_url",
    "clean_record",
    "validate_record",
    "validate_dataset",
    "make_fingerprint",
    "find_duplicates",
]
