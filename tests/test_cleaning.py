"""Unit tests for processing.cleaning module."""

import pytest
from processing.cleaning import (
    clean_text,
    strip_quotes,
    clean_price,
    clean_rating,
    clean_tags,
    normalize_url,
    clean_record,
)


class TestCleanText:
    """Tests for clean_text function."""

    def test_clean_text_normal(self):
        assert clean_text(" Hello   World ") == "Hello World"

    def test_clean_text_newlines_and_tabs(self):
        assert clean_text(" Hello \n \t World \r\n ") == "Hello World"

    def test_clean_text_non_breaking_spaces(self):
        assert clean_text("Hello\xa0World\xa0\xa0Again") == "Hello World Again"

    def test_clean_text_empty_and_none(self):
        assert clean_text(None) is None
        assert clean_text("") is None
        assert clean_text("   \xa0 \n ") is None


class TestStripQuotes:
    """Tests for strip_quotes function."""

    def test_strip_curly_quotes(self):
        assert strip_quotes("“The world is a stage.”") == "The world is a stage."

    def test_strip_straight_quotes(self):
        assert strip_quotes('"To be or not to be"') == "To be or not to be"
        assert strip_quotes("'Single quotes'") == "Single quotes"

    def test_strip_guillemets_and_other_quotes(self):
        assert strip_quotes("«French style quote»") == "French style quote"
        assert strip_quotes("„German style quote”") == "German style quote"

    def test_strip_quotes_none_or_empty(self):
        assert strip_quotes(None) is None
        assert strip_quotes("") is None
        assert strip_quotes(' “” ') is None


class TestCleanPrice:
    """Tests for clean_price function."""

    def test_clean_price_gbp(self):
        assert clean_price("£51.77") == 51.77

    def test_clean_price_with_mojibake(self):
        # Mojibake when UTF-8 is misread as Latin-1
        assert clean_price("Â£51.77") == 51.77

    def test_clean_price_with_comma(self):
        assert clean_price("£1,234.50") == 1234.50

    def test_clean_price_numeric(self):
        assert clean_price(42.5) == 42.5
        assert clean_price(10) == 10.0

    def test_clean_price_invalid_or_none(self):
        assert clean_price(None) is None
        assert clean_price("") is None
        assert clean_price("Free") is None
        assert clean_price("N/A") is None


class TestCleanRating:
    """Tests for clean_rating function."""

    def test_clean_rating_words(self):
        assert clean_rating("One") == 1
        assert clean_rating("Two") == 2
        assert clean_rating("Three") == 3
        assert clean_rating("Four") == 4
        assert clean_rating("Five") == 5

    def test_clean_rating_from_class_string(self):
        assert clean_rating("star-rating Three") == 3
        assert clean_rating("star-rating Five") == 5

    def test_clean_rating_numeric(self):
        assert clean_rating(4) == 4
        assert clean_rating("4") == 4

    def test_clean_rating_invalid(self):
        assert clean_rating(0) is None
        assert clean_rating(6) is None
        assert clean_rating("Ten") is None
        assert clean_rating(None) is None
        assert clean_rating("") is None


class TestCleanTags:
    """Tests for clean_tags function."""

    def test_clean_tags_list(self):
        assert clean_tags(["thinking", "Change", "  deep-thoughts  "]) == "change;deep-thoughts;thinking"

    def test_clean_tags_string(self):
        assert clean_tags("books, love, books; romance") == "books;love;romance"

    def test_clean_tags_empty_or_none(self):
        assert clean_tags(None) is None
        assert clean_tags([]) is None
        assert clean_tags("") is None
        assert clean_tags(["  ", ""]) is None


class TestNormalizeUrl:
    """Tests for normalize_url function."""

    def test_normalize_valid_urls(self):
        assert normalize_url("https://books.toscrape.com/catalogue/book_1.html") == "https://books.toscrape.com/catalogue/book_1.html"
        assert normalize_url("http://quotes.toscrape.com/author/Einstein/") == "http://quotes.toscrape.com/author/Einstein/"

    def test_normalize_with_whitespace(self):
        assert normalize_url("  https://books.toscrape.com/  ") == "https://books.toscrape.com/"

    def test_normalize_invalid_urls(self):
        assert normalize_url(None) is None
        assert normalize_url("") is None
        assert normalize_url("ftp://example.com") is None
        assert normalize_url("/relative/path/only") is None


class TestCleanRecord:
    """Tests for clean_record function."""

    def test_clean_record_books(self):
        raw = {
            "source": "Books to Scrape",
            "source_url": "https://books.toscrape.com/catalogue/test_1/index.html",
            "name_or_title": "  A Light in the Attic  ",
            "category": None,
            "price": "£51.77",
            "rating": "star-rating Three",
            "author": None,
            "tags": None,
            "description": None,
            "scraped_at": "2026-10-06T12:00:00Z",
        }
        cleaned = clean_record(raw)
        assert cleaned["source"] == "Books to Scrape"
        assert cleaned["name_or_title"] == "A Light in the Attic"
        assert cleaned["price"] == 51.77
        assert cleaned["rating"] == 3
        assert cleaned["author"] is None
        assert cleaned["tags"] is None

    def test_clean_record_quotes(self):
        raw = {
            "source": "Quotes to Scrape",
            "source_url": "https://quotes.toscrape.com/author/Albert-Einstein/",
            "name_or_title": "“The world as we have created it...”",
            "category": None,
            "price": None,
            "rating": None,
            "author": "  Albert Einstein  ",
            "tags": ["thinking", "change"],
            "description": None,
            "scraped_at": "2026-10-06T12:00:00Z",
        }
        cleaned = clean_record(raw)
        assert cleaned["source"] == "Quotes to Scrape"
        assert cleaned["name_or_title"] == "The world as we have created it..."
        assert cleaned["author"] == "Albert Einstein"
        assert cleaned["tags"] == "change;thinking"
        assert cleaned["price"] is None
        assert cleaned["rating"] is None
