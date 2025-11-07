"""
Base crawler for web scraping
"""

import logging
import asyncio
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
import aiohttp
from bs4 import BeautifulSoup

from src.core.models import RawEvent, SourceConfig, CrawlerResult


logger = logging.getLogger(__name__)


class BaseCrawler(ABC):
    """Abstract base class for crawlers"""

    def __init__(self, source: SourceConfig, timeout: int = 10, user_agent: str = ""):
        self.source = source
        self.timeout = timeout
        self.user_agent = user_agent or "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"

    @abstractmethod
    async def crawl(self) -> CrawlerResult:
        """Crawl the source and return events"""
        pass

    async def fetch_html(self, url: str) -> Optional[str]:
        """Fetch HTML content from URL"""
        headers = {"User-Agent": self.user_agent}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=self.timeout) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        logger.warning(f"{self.source.id}: HTTP {response.status} for {url}")
                        return None

        except asyncio.TimeoutError:
            logger.error(f"{self.source.id}: Timeout fetching {url}")
            return None
        except Exception as e:
            logger.error(f"{self.source.id}: Error fetching {url}: {e}")
            return None

    def parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML with BeautifulSoup"""
        return BeautifulSoup(html, 'lxml')

    def extract_text(self, element, selector: str = None) -> str:
        """Extract text from element"""
        if selector:
            elem = element.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
            return ""
        return element.get_text(strip=True) if element else ""

    def extract_link(self, element, selector: str = None) -> str:
        """Extract href from element"""
        if selector:
            elem = element.select_one(selector)
            if elem:
                return elem.get('href', '')
            return ""
        return element.get('href', '') if element else ""

    def extract_image(self, element, selector: str = None) -> str:
        """Extract image src from element"""
        if selector:
            elem = element.select_one(selector)
            if elem:
                return elem.get('src', '') or elem.get('data-src', '')
            return ""

        if element:
            return element.get('src', '') or element.get('data-src', '')
        return ""

    def make_absolute_url(self, url: str) -> str:
        """Convert relative URL to absolute"""
        if url.startswith('http'):
            return url
        elif url.startswith('//'):
            return f"https:{url}"
        elif url.startswith('/'):
            return f"{self.source.url}{url}"
        else:
            return f"{self.source.url}/{url}"

    def clean_text(self, text: str) -> str:
        """Clean extracted text"""
        if not text:
            return ""

        # Remove extra whitespace
        text = " ".join(text.split())

        # Remove common unwanted phrases
        unwanted = [
            "Leggi tutto",
            "Read more",
            "Continua a leggere",
            "Continue reading"
        ]

        for phrase in unwanted:
            text = text.replace(phrase, "")

        return text.strip()

    def parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime"""
        if not date_str:
            return None

        # Common Italian date formats
        formats = [
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y-%m-%d",
            "%d %B %Y",
            "%d %b %Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        # Try ISO format
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            pass

        logger.warning(f"{self.source.id}: Could not parse date: {date_str}")
        return None

    async def apply_rate_limit(self):
        """Apply rate limiting delay"""
        if self.source.rate_limit > 0:
            await asyncio.sleep(self.source.rate_limit)

    def create_raw_event(self, title: str, content: str, url: str,
                        date: Optional[datetime] = None,
                        image_url: Optional[str] = None) -> RawEvent:
        """Create RawEvent object"""
        return RawEvent(
            source=self.source.id,
            title=self.clean_text(title),
            content=self.clean_text(content),
            event_date=date,
            image_url=image_url,
            source_url=self.make_absolute_url(url),
            scraped_at=datetime.now(),
            processed=False
        )
