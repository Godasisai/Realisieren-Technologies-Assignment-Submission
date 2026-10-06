"""Unit tests for processing.deduplication module."""

import pytest
from processing.deduplication import make_fingerprint, find_duplicates


def test_duplicates_ignore_case_and_spaces():
    """Verify duplicate detection collapses whitespace and ignores casing."""
    base = {"source": "Books to Scrape", "author": None}
    records = [
        {**base, "name_or_title": "Example Book Title"},
        {**base, "name_or_title": " Example Book Title "},
        {**base, "name_or_title": "EXAMPLE BOOK TITLE"},
    ]
    unique, dupes = find_duplicates(records)
    assert len(unique) == 1
    assert len(dupes) == 2


def test_duplicates_ignore_punctuation():
    """Verify punctuation differences do not create duplicate records."""
    base = {"source": "Books to Scrape", "author": None}
    records = [
        {**base, "name_or_title": "Harry Potter: Philosopher's Stone!"},
        {**base, "name_or_title": "Harry Potter Philosophers Stone"},
    ]
    unique, dupes = find_duplicates(records)
    assert len(unique) == 1
    assert len(dupes) == 1


def test_quotes_deduplication_rule():
    """Verify quotes deduplication utilizes author and first 50 characters."""
    base = {"source": "Quotes to Scrape", "author": "Albert Einstein"}
    records = [
        {
            **base,
            "name_or_title": "Life is like riding a bicycle. To keep your balance you must keep moving.",
        },
        {
            **base,
            "name_or_title": "Life is like riding a bicycle. To keep your balance you must keep moving! (Variant)",
        },
    ]
    # First 50 chars of both match: "Life is like riding a bicycle. To keep your balanc"
    unique, dupes = find_duplicates(records)
    assert len(unique) == 1
    assert len(dupes) == 1


def test_quotes_different_author_different_fingerprint():
    """Verify quotes with identical text but different authors are not considered duplicates."""
    records = [
        {"source": "Quotes to Scrape", "author": "Author A", "name_or_title": "Common saying"},
        {"source": "Quotes to Scrape", "author": "Author B", "name_or_title": "Common saying"},
    ]
    unique, dupes = find_duplicates(records)
    assert len(unique) == 2
    assert len(dupes) == 0


def test_find_duplicates_flag_only():
    """Verify flag_only preserves all records and appends is_duplicate boolean."""
    base = {"source": "Books to Scrape", "author": None}
    records = [
        {**base, "name_or_title": "Original Title"},
        {**base, "name_or_title": "Original Title"},
    ]
    flagged, dupes = find_duplicates(records, flag_only=True)
    assert len(flagged) == 2
    assert flagged[0]["is_duplicate"] is False
    assert flagged[1]["is_duplicate"] is True
    assert len(dupes) == 1
