"""Unit tests for processing.validation module."""

import pytest
from processing.validation import validate_record, validate_dataset


class TestValidateRecord:
    """Tests for individual record validation."""

    def test_valid_book_record(self):
        rec = {
            "source": "Books to Scrape",
            "source_url": "https://books.toscrape.com/catalogue/book_1.html",
            "name_or_title": "A Light in the Attic",
            "category": None,
            "price": 51.77,
            "rating": 3,
            "author": None,
            "tags": None,
            "description": None,
            "scraped_at": "2026-10-06T12:00:00Z",
        }
        problems = validate_record(rec)
        assert problems == []

    def test_valid_quote_record(self):
        rec = {
            "source": "Quotes to Scrape",
            "source_url": "https://quotes.toscrape.com/author/Albert-Einstein/",
            "name_or_title": "The world as we have created it...",
            "category": None,
            "price": None,
            "rating": None,
            "author": "Albert Einstein",
            "tags": "change;thinking",
            "description": None,
            "scraped_at": "2026-10-06T12:00:00Z",
        }
        problems = validate_record(rec)
        assert problems == []

    def test_unknown_source(self):
        rec = {
            "source": "Random Website",
            "source_url": "https://example.com/item",
            "name_or_title": "Random Title",
            "price": None,
            "rating": None,
        }
        problems = validate_record(rec)
        assert "unknown_source" in problems

    def test_missing_name(self):
        rec = {
            "source": "Books to Scrape",
            "source_url": "https://books.toscrape.com/catalogue/book_1.html",
            "name_or_title": "",
            "price": 20.0,
            "rating": 4,
        }
        assert "missing_name" in validate_record(rec)

        rec["name_or_title"] = None
        assert "missing_name" in validate_record(rec)

    def test_invalid_url(self):
        rec = {
            "source": "Books to Scrape",
            "source_url": "ftp://books.toscrape.com/catalogue/book_1.html",
            "name_or_title": "Book Title",
            "price": 20.0,
            "rating": 4,
        }
        assert "invalid_url" in validate_record(rec)

        rec["source_url"] = ""
        assert "invalid_url" in validate_record(rec)

    def test_invalid_price(self):
        rec = {
            "source": "Books to Scrape",
            "source_url": "https://books.toscrape.com/catalogue/book_1.html",
            "name_or_title": "Book Title",
            "price": -5.0,
            "rating": 4,
        }
        assert "invalid_price" in validate_record(rec)

        rec["price"] = "not-a-number"
        assert "invalid_price" in validate_record(rec)

    def test_invalid_rating(self):
        rec = {
            "source": "Books to Scrape",
            "source_url": "https://books.toscrape.com/catalogue/book_1.html",
            "name_or_title": "Book Title",
            "price": 10.0,
            "rating": 6,
        }
        assert "invalid_rating" in validate_record(rec)

        rec["rating"] = 0
        assert "invalid_rating" in validate_record(rec)


class TestValidateDataset:
    """Tests for dataset-level validation and reason tallying."""

    def test_validate_dataset_partitioning(self):
        records = [
            {
                "source": "Books to Scrape",
                "source_url": "https://books.toscrape.com/book1",
                "name_or_title": "Book 1",
                "price": 10.0,
                "rating": 3,
            },
            {
                "source": "Invalid Source",
                "source_url": "https://books.toscrape.com/book2",
                "name_or_title": "Book 2",
                "price": 10.0,
                "rating": 3,
            },
            {
                "source": "Books to Scrape",
                "source_url": "invalid-url",
                "name_or_title": "",
                "price": -1.0,
                "rating": 10,
            },
        ]

        valid, rejected, reason_counts = validate_dataset(records)
        assert len(valid) == 1
        assert len(rejected) == 2
        assert reason_counts["unknown_source"] == 1
        assert reason_counts["missing_name"] == 1
        assert reason_counts["invalid_url"] == 1
        assert reason_counts["invalid_price"] == 1
        assert reason_counts["invalid_rating"] == 1
