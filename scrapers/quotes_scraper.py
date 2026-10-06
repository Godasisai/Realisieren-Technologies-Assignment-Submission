"""Scraper for Quotes to Scrape (https://quotes.toscrape.com/)."""

from datetime import datetime, timezone
import logging
from typing import Dict, List, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup, Tag

from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class QuotesScraper(BaseScraper):
    """Scraper implementation for Quotes to Scrape."""

    SOURCE_NAME = "Quotes to Scrape"

    def __init__(
        self,
        base_url: str = "https://quotes.toscrape.com/",
        delay_seconds: float = 0.5,
        timeout: int = 10,
    ) -> None:
        super().__init__(base_url=base_url, delay_seconds=delay_seconds, timeout=timeout)

    def parse_quote_card(self, quote_elem: Tag, page_url: str) -> Optional[Dict]:
        """Extract raw quote data from a div.quote element.

        Args:
            quote_elem: BeautifulSoup Tag representing the quote card.
            page_url: The current page URL for resolving relative links.

        Returns:
            Dictionary with raw quote fields, or None if essential fields are missing.
        """
        try:
            text_tag = quote_elem.select_one("span.text")
            raw_text = text_tag.get_text() if text_tag else None

            author_tag = quote_elem.select_one("small.author")
            author = author_tag.get_text(strip=True) if author_tag else None

            # Resolve author biography or quote reference link
            author_link = quote_elem.select_one('a[href*="/author/"]')
            source_url = page_url
            if author_link and author_link.get("href"):
                source_url = urljoin(page_url, author_link["href"])

            # Extract tags
            tag_elements = quote_elem.select("a.tag")
            tags = [t.get_text(strip=True) for t in tag_elements if t.get_text(strip=True)]

            scraped_at = datetime.now(timezone.utc).isoformat()

            return {
                "source": self.SOURCE_NAME,
                "source_url": source_url,
                "name_or_title": raw_text,
                "category": None,
                "price": None,
                "rating": None,
                "author": author,
                "tags": tags,
                "description": None,
                "scraped_at": scraped_at,
            }
        except Exception as exc:
            logger.warning("Error parsing quote card on %s: %s", page_url, exc)
            return None

    def scrape(self, max_pages: Optional[int] = None) -> List[Dict]:
        """Scrape quote records across all pages following pagination.

        Args:
            max_pages: Optional maximum number of pages to scrape (for testing).

        Returns:
            List of raw extracted quote records.
        """
        current_url: Optional[str] = self.base_url
        page_number = 1
        all_records: List[Dict] = []

        logger.info("Starting scrape for %s at %s", self.SOURCE_NAME, current_url)

        while current_url:
            if max_pages is not None and page_number > max_pages:
                logger.info("Reached maximum requested pages (%d) for %s", max_pages, self.SOURCE_NAME)
                break

            logger.info("Scraping %s - Page %d: %s", self.SOURCE_NAME, page_number, current_url)
            soup = self.fetch_soup(current_url)
            if not soup:
                logger.error("Failed to retrieve page %d (%s). Stopping pagination.", page_number, current_url)
                break

            # Find all quote elements on the page
            quote_cards = soup.select("div.quote")
            logger.debug("Found %d quote cards on page %d", len(quote_cards), page_number)

            page_records_count = 0
            for card in quote_cards:
                record = self.parse_quote_card(card, current_url)
                if record:
                    all_records.append(record)
                    page_records_count += 1

            logger.info("Extracted %d records from page %d", page_records_count, page_number)

            # Locate next link
            next_link_tag = soup.select_one("li.next > a")
            if next_link_tag and next_link_tag.get("href"):
                next_href = next_link_tag["href"]
                current_url = urljoin(current_url, next_href)
                page_number += 1
                self.polite_pause()
            else:
                logger.info("No next page link found. Finished all pages for %s.", self.SOURCE_NAME)
                current_url = None

        logger.info("Finished %s scrape. Total raw records collected: %d", self.SOURCE_NAME, len(all_records))
        return all_records
