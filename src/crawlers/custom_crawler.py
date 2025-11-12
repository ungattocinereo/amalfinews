"""
Custom crawler for non-WordPress sites
"""

import logging
from datetime import datetime
from typing import List

from src.crawlers.base_crawler import BaseCrawler
from src.core.models import RawEvent, CrawlerResult


logger = logging.getLogger(__name__)


class CustomCrawler(BaseCrawler):
    """Crawler for custom CMS sites"""

    async def crawl(self) -> CrawlerResult:
        """Crawl custom site using configured selectors"""
        start_time = datetime.now()
        events = []
        error = None

        try:
            logger.info(f"{self.source.id}: Crawling {self.source.url}")
            html = await self.fetch_html(self.source.url)

            if not html:
                error = "Failed to fetch HTML"
                success = False
            else:
                events = self.parse_events(html)
                success = len(events) > 0
                if not success:
                    error = "No events found"

        except Exception as e:
            logger.error(f"{self.source.id}: Crawl error: {e}")
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

    def parse_events(self, html: str) -> List[RawEvent]:
        """Parse events from HTML"""
        events = []
        soup = self.parse_html(html)

        # Find article/event elements
        articles_selector = self.source.selectors.get('articles', 'article')
        articles = soup.select(articles_selector)

        logger.info(f"{self.source.id}: Found {len(articles)} elements with selector '{articles_selector}'")

        if not articles:
            logger.warning(f"{self.source.id}: No articles found with selector '{articles_selector}'")
            # Try to find what's actually on the page
            for fallback_selector in ['article', '.post', '[class*="event"]', '[class*="news"]', '.item']:
                fallback = soup.select(fallback_selector)
                if fallback:
                    logger.info(f"{self.source.id}: Found {len(fallback)} elements with fallback selector '{fallback_selector}'")
            return events

        parsed_count = 0
        for article in articles[:10]:  # Limit to 10 most recent
            try:
                # Extract all fields using selectors
                title = self.extract_text(article, self.source.selectors.get('title'))
                content = self.extract_text(article, self.source.selectors.get('content'))
                link = self.extract_link(article, self.source.selectors.get('link'))

                # If no link found with selector, try to find any link
                if not link:
                    any_link = article.find('a')
                    if any_link:
                        link = any_link.get('href', '')

                date_str = self.extract_text(article, self.source.selectors.get('date'))
                image_url = self.extract_image(article, self.source.selectors.get('image'))

                # Parse date
                event_date = self.parse_date(date_str) if date_str else None

                # Create event
                if title and link:
                    event = self.create_raw_event(
                        title=title,
                        content=content or title,
                        url=link,
                        date=event_date,
                        image_url=image_url
                    )
                    events.append(event)
                    parsed_count += 1
                else:
                    logger.debug(f"{self.source.id}: Skipping element - missing title or link (title: {bool(title)}, link: {bool(link)})")

            except Exception as e:
                logger.error(f"{self.source.id}: Error parsing article: {e}", exc_info=True)
                continue

        logger.info(f"{self.source.id}: Successfully parsed {parsed_count}/{len(articles)} events")
        return events
