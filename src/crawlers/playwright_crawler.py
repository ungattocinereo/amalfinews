"""
Playwright-based crawler for sites with anti-bot protection
Uses headless browser to bypass Cloudflare and other JavaScript challenges
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from src.crawlers.base_crawler import BaseCrawler
from src.core.models import RawEvent, CrawlerResult


logger = logging.getLogger(__name__)


class PlaywrightCrawler(BaseCrawler):
    """Crawler using Playwright headless browser"""

    # Shared browser instance for better performance
    _browser: Optional[Browser] = None
    _browser_lock = asyncio.Lock()

    async def get_browser(self) -> Browser:
        """Get or create shared browser instance"""
        async with self._browser_lock:
            if self._browser is None or not self._browser.is_connected():
                playwright = await async_playwright().start()
                self._browser = await playwright.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-blink-features=AutomationControlled'
                    ]
                )
                logger.info("Playwright browser launched")
            return self._browser

    async def fetch_with_browser(self, url: str) -> Optional[str]:
        """Fetch page content using Playwright browser"""
        try:
            browser = await self.get_browser()
            
            # Create new context with realistic settings
            context: BrowserContext = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=self.user_agent,
                locale='it-IT',
                timezone_id='Europe/Rome',
                extra_http_headers={
                    'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7'
                }
            )

            page: Page = await context.new_page()
            
            # Block unnecessary resources to speed up loading
            await page.route("**/*.{png,jpg,jpeg,gif,svg,css,font,woff,woff2}", lambda route: route.abort())
            
            logger.info(f"{self.source.id}: Fetching {url} with Playwright...")
            
            # Navigate and wait for network idle
            await page.goto(url, wait_until='networkidle', timeout=self.timeout * 1000)
            
            # Wait a bit for any JS to execute
            await page.wait_for_timeout(1000)
            
            # Get page content
            content = await page.content()
            
            await context.close()
            
            logger.info(f"{self.source.id}: Successfully fetched {len(content)} bytes with Playwright")
            return content

        except Exception as e:
            logger.error(f"{self.source.id}: Playwright fetch error: {e}")
            return None

    async def crawl(self) -> CrawlerResult:
        """Crawl source using Playwright"""
        start_time = datetime.now()
        events = []
        error = None

        try:
            logger.info(f"{self.source.id}: Starting Playwright crawl of {self.source.url}")
            
            # Fetch HTML with browser
            html = await self.fetch_with_browser(self.source.url)
            
            if not html:
                error = "Failed to fetch HTML with Playwright"
                success = False
            else:
                # Parse HTML same way as WordPress crawler
                soup = self.parse_html(html)
                
                # Find articles
                articles_selector = self.source.selectors.get('articles', '.post, article')
                articles = soup.select(articles_selector)
                
                logger.info(f"{self.source.id}: Found {len(articles)} articles with Playwright")
                
                if not articles:
                    # Try fallback selectors
                    for fallback_selector in ['article', '.post', '[class*="post"]', '.entry', '.item']:
                        articles = soup.select(fallback_selector)
                        if articles:
                            logger.info(f"{self.source.id}: Found {len(articles)} with fallback '{fallback_selector}'")
                            break
                
                # Parse articles
                for article in articles[:10]:  # Limit to 10
                    try:
                        # Extract title
                        title_selector = self.source.selectors.get('title', 'h2')
                        title_elem = article.select_one(title_selector)
                        title = self.extract_text(title_elem) if title_elem else ""
                        
                        # Extract link
                        link = ""
                        if title_elem:
                            link_tag = title_elem.find('a')
                            if link_tag:
                                link = link_tag.get('href', '')
                        
                        if not link:
                            link_selector = self.source.selectors.get('link', 'a')
                            link_elem = article.select_one(link_selector)
                            link = self.extract_link(link_elem) if link_elem else ""
                        
                        if not link:
                            any_link = article.find('a')
                            if any_link:
                                link = any_link.get('href', '')
                        
                        # Make absolute URL
                        if link:
                            link = self.make_absolute_url(link)
                        
                        # Extract content
                        content_selector = self.source.selectors.get('content', '.entry-content')
                        content_elem = article.select_one(content_selector)
                        content = self.extract_text(content_elem) if content_elem else title
                        
                        # Extract date
                        date_selector = self.source.selectors.get('date', 'time')
                        date_elem = article.select_one(date_selector)
                        date_str = ""
                        if date_elem:
                            date_str = date_elem.get('datetime', '') or self.extract_text(date_elem)
                        event_date = self.parse_date(date_str) if date_str else None
                        
                        # Extract image
                        image_selector = self.source.selectors.get('image', 'img')
                        image_elem = article.select_one(image_selector)
                        image_url = self.extract_image(image_elem) if image_elem else None
                        
                        # Create event
                        if title and link:
                            event = self.create_raw_event(
                                title=title,
                                content=content,
                                url=link,
                                date=event_date,
                                image_url=image_url
                            )
                            events.append(event)
                        
                    except Exception as e:
                        logger.error(f"{self.source.id}: Error parsing article: {e}")
                        continue
                
                success = len(events) > 0
                if not success:
                    error = "No articles found"
                else:
                    logger.info(f"{self.source.id}: Successfully extracted {len(events)} events with Playwright")

        except Exception as e:
            logger.error(f"{self.source.id}: Playwright crawl error: {e}", exc_info=True)
            error = str(e)
            success = False

        duration = (datetime.now() - start_time).total_seconds()

        return CrawlerResult(
            source_id=self.source.id,
            success=success,
            events=events,
            error=error,
            duration_seconds=duration
        )

    @classmethod
    async def close_browser(cls):
        """Close shared browser instance"""
        async with cls._browser_lock:
            if cls._browser:
                await cls._browser.close()
                cls._browser = None
                logger.info("Playwright browser closed")
