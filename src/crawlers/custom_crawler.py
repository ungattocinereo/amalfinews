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

        if not articles:
            logger.warning(f"{self.source.id}: No articles found")
            return events

        for article in articles[:50]:
            try:
                # Extract all fields using selectors
                title = self.extract_text(article, self.source.selectors.get('title'))
                content = self.extract_text(article, self.source.selectors.get('content'))
                link = self.extract_link(article, self.source.selectors.get('link'))
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

            except Exception as e:
                logger.error(f"{self.source.id}: Error parsing article: {e}")
                continue

        logger.info(f"{self.source.id}: Extracted {len(events)} events")
        return events
