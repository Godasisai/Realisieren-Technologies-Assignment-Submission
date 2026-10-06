"""Base scraper module providing resilient HTTP session management, rate limiting, and dynamic pagination."""

import logging
import time
from typing import Dict, Iterator, List, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

logger = logging.getLogger(__name__)


class BaseScraper:
    """Base class for web scrapers handling resilient networking and pagination."""

    def __init__(
        self,
        base_url: str,
        delay_seconds: float = 0.5,
        timeout: int = 10,
        user_agent: Optional[str] = None,
    ) -> None:
        """Initialize the scraper with base configuration.

        Args:
            base_url: The starting URL for the scraper.
            delay_seconds: Polite delay interval between HTTP requests.
            timeout: Network request timeout in seconds.
            user_agent: Custom User-Agent header string.
        """
        self.base_url = base_url
        self.delay_seconds = delay_seconds
        self.timeout = timeout
        self.user_agent = user_agent or "ScrapingAssignment/1.0 (Python Web Scraper Assessment)"
        self.session = self._create_resilient_session()

    def _create_resilient_session(self) -> requests.Session:
        """Create a requests Session with exponential backoff retries.

        Returns:
            A configured requests.Session instance.
        """
        session = requests.Session()
        session.headers.update({"User-Agent": self.user_agent})

        retries = Retry(
            total=3,
            backoff_factor=1.0,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def fetch_soup(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch a page and return a parsed BeautifulSoup object.

        Args:
            url: The page URL to fetch.

        Returns:
            BeautifulSoup parsed document or None if request fails.
        """
        try:
            logger.debug("Requesting URL: %s", url)
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            # Ensure correct character encoding for symbols like currency
            response.encoding = "utf-8"
            return BeautifulSoup(response.text, "lxml")
        except requests.RequestException as exc:
            logger.error("Failed to fetch %s: %s", url, exc)
            return None

    def polite_pause(self) -> None:
        """Pause execution between requests to respect server load."""
        if self.delay_seconds > 0:
            time.sleep(self.delay_seconds)

    def scrape(self, max_pages: Optional[int] = None) -> List[Dict]:
        """Scrape all available pages following next links dynamically.

        Args:
            max_pages: Optional limit on the number of pages to scrape.

        Returns:
            A list of raw scraped record dictionaries.
        """
        raise NotImplementedError("Subclasses must implement the scrape method.")
