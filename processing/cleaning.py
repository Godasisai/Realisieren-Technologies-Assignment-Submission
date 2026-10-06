"""Data cleaning and normalization functions.

Pure functions with no external network or file side-effects.
"""

import re
from typing import Any, List, Optional, Union

RATING_MAP = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
}

# Regex for stripping leading/trailing quote characters (both curly and straight)
QUOTE_STRIP_REGEX = r'^[“”"\'«»„‘’\s]+|[“”"\'«»„‘’\s]+$'


def clean_text(value: Optional[str]) -> Optional[str]:
    """Remove unnecessary whitespace, newlines, tabs, and non-breaking spaces.

    Args:
        value: Input string or None.

    Returns:
        Cleaned string with single space separation, or None if empty.
    """
    if value is None:
        return None
    # Replace non-breaking spaces and collapse any whitespace
    text = " ".join(str(value).replace("\xa0", " ").split())
    return text if text else None


def strip_quotes(value: Optional[str]) -> Optional[str]:
    """Strip leading and trailing straight and typographical quotation marks.

    Args:
        value: Input quote text.

    Returns:
        Cleaned quote string without surrounding quote characters.
    """
    if value is None:
        return None
    cleaned = clean_text(value)
    if not cleaned:
        return None
    # Strip leading/trailing quotation marks
    stripped = re.sub(QUOTE_STRIP_REGEX, "", cleaned)
    return stripped if stripped else None


def clean_price(raw: Any) -> Optional[float]:
    """Extract and parse numeric price value from raw currency text.

    Args:
        raw: Raw price string (e.g., '£51.77', 'Â£19.99') or numeric.

    Returns:
        Float price or None if missing or unparseable.
    """
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return round(float(raw), 2)
    raw_str = str(raw).replace(",", "").strip()
    match = re.search(r"\d+(?:\.\d+)?", raw_str)
    if match:
        try:
            return round(float(match.group()), 2)
        except ValueError:
            return None
    return None


def clean_rating(raw: Any) -> Optional[int]:
    """Convert rating representations into an integer between 1 and 5.

    Supports word ratings ('Three', 'star-rating Three') and digits ('3', 3).

    Args:
        raw: Raw rating representation.

    Returns:
        Integer rating (1 to 5) or None if unrecognized.
    """
    if raw is None:
        return None
    if isinstance(raw, int) and 1 <= raw <= 5:
        return raw

    raw_str = str(raw).strip().lower()

    # Direct digit match
    if raw_str.isdigit():
        val = int(raw_str)
        return val if 1 <= val <= 5 else None

    # Check words against rating map
    for word in raw_str.split():
        if word in RATING_MAP:
            return RATING_MAP[word]

    return None


def clean_tags(tags: Union[None, str, List[str]]) -> Optional[str]:
    """Normalize tags list/string into a lowercase, sorted, semicolon-separated string.

    Args:
        tags: List of tag strings, comma/semicolon delimited string, or None.

    Returns:
        Semicolon-separated tags string or None.
    """
    if not tags:
        return None

    tag_list: List[str] = []
    if isinstance(tags, str):
        # Split on commas or semicolons
        parts = re.split(r"[,;]", tags)
        tag_list = [p.strip() for p in parts if p.strip()]
    elif isinstance(tags, (list, tuple, set)):
        tag_list = [str(t).strip() for t in tags if str(t).strip()]

    if not tag_list:
        return None

    # Normalize: lowercase, collapse internal whitespace, deduplicate and sort
    cleaned_set = {re.sub(r"\s+", " ", t.lower()) for t in tag_list if t}
    if not cleaned_set:
        return None

    return ";".join(sorted(cleaned_set))


def normalize_url(url: Optional[str]) -> Optional[str]:
    """Trim and validate URL structure.

    Args:
        url: Raw URL string.

    Returns:
        Cleaned URL string if valid http/https, else None.
    """
    if not url:
        return None
    trimmed = str(url).strip()
    if trimmed.startswith(("http://", "https://")):
        return trimmed
    return None


def clean_record(raw_record: dict) -> dict:
    """Standardize and clean a single raw record from any supported source.

    Args:
        raw_record: Raw dictionary collected by a scraper.

    Returns:
        Cleaned dictionary conforming to the standard schema.
    """
    source = clean_text(raw_record.get("source"))
    source_url = normalize_url(raw_record.get("source_url"))

    raw_name = raw_record.get("name_or_title")
    if source == "Quotes to Scrape":
        name_or_title = strip_quotes(raw_name)
    else:
        name_or_title = clean_text(raw_name)

    category = clean_text(raw_record.get("category"))
    price = clean_price(raw_record.get("price"))
    rating = clean_rating(raw_record.get("rating"))
    author = clean_text(raw_record.get("author"))
    tags = clean_tags(raw_record.get("tags"))
    description = clean_text(raw_record.get("description"))
    scraped_at = clean_text(raw_record.get("scraped_at"))

    return {
        "source": source,
        "name_or_title": name_or_title,
        "category": category,
        "price": price,
        "rating": rating,
        "author": author,
        "tags": tags,
        "description": description,
        "source_url": source_url,
        "scraped_at": scraped_at,
    }
