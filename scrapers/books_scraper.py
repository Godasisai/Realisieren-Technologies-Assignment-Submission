"""Scraper for Books to Scrape (https://books.toscrape.com/)."""

from datetime import datetime, timezone
import logging
from typing import Dict, List, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup, Tag

from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class BooksScraper(BaseScraper):
    """Scraper implementation for Books to Scrape."""

    SOURCE_NAME = "Books to Scrape"

    def __init__(
        self,
        base_url: str = "https://books.toscrape.com/",
        delay_seconds: float = 0.5,
        timeout: int = 10,
    ) -> None:
        super().__init__(base_url=base_url, delay_seconds=delay_seconds, timeout=timeout)

    def parse_book_pod(self, article: Tag, page_url: str) -> Optional[Dict]:
        """Extract raw book data from an article.product_pod element.

        Args:
            article: BeautifulSoup Tag representing the book card.
            page_url: The current page URL for resolving relative links.

        Returns:
            Dictionary with raw book fields, or None if essential fields are missing.
        """
        try:
            link_tag = article.select_one("h3 > a")
            # The full title is preserved in the title attribute, inner text may be truncated
            title = None
            product_url = None
            if link_tag:
                title = link_tag.get("title") or link_tag.get_text(strip=True)
                raw_href = link_tag.get("href")
                if raw_href:
                    product_url = urljoin(page_url, raw_href)

            price_tag = article.select_one("p.price_color")
            raw_price = price_tag.get_text(strip=True) if price_tag else None

            rating_tag = article.select_one("p.star-rating")
            raw_rating = " ".join(rating_tag.get("class", [])) if rating_tag else None

            # Timestamp of collection
            scraped_at = datetime.now(timezone.utc).isoformat()

            return {
                "source": self.SOURCE_NAME,
                "source_url": product_url,
                "name_or_title": title,
                "category": None,
                "price": raw_price,
                "rating": raw_rating,
                "author": None,
                "tags": None,
                "description": None,
                "scraped_at": scraped_at,
            }
        except Exception as exc:
            logger.warning("Error parsing book pod on %s: %s", page_url, exc)
            return None

    def scrape(self, max_pages: Optional[int] = None) -> List[Dict]:
        """Scrape book records across all pages following pagination.

        Args:
            max_pages: Optional maximum number of pages to scrape (for testing).

        Returns:
            List of raw extracted book records.
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

            # Find all book cards on the page
            articles = soup.select("article.product_pod")
            logger.debug("Found %d book pods on page %d", len(articles), page_number)

            page_records_count = 0
            for article in articles:
                record = self.parse_book_pod(article, current_url)
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
