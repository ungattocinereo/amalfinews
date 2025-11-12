"""
WordPress-specific crawler
Handles WordPress sites with RSS feed support
"""

import logging
import feedparser
from datetime import datetime
from typing import List

from src.crawlers.base_crawler import BaseCrawler
from src.core.models import RawEvent, CrawlerResult


logger = logging.getLogger(__name__)


class WordPressCrawler(BaseCrawler):
    """Crawler for WordPress sites"""

    async def crawl(self) -> CrawlerResult:
        """
        Crawl WordPress site using RSS feed if available,
        otherwise fall back to HTML parsing
        """
        start_time = datetime.now()
        events = []
        error = None

        try:
            # Try RSS feed first
            if self.source.rss_feed:
                logger.info(f"{self.source.id}: Trying RSS feed {self.source.rss_feed}")
                events = await self.crawl_rss()

                # Fallback to HTML if RSS fails
                if not events:
                    logger.info(f"{self.source.id}: RSS feed returned no events, falling back to HTML parsing")
                    events = await self.crawl_html()
            else:
                logger.info(f"{self.source.id}: No RSS feed configured, using HTML parsing")
                events = await self.crawl_html()

            success = len(events) > 0
            if not success:
                error = "No events found after trying all methods"
                logger.warning(f"{self.source.id}: {error}")
            else:
                logger.info(f"{self.source.id}: Successfully extracted {len(events)} events")

        except Exception as e:
            logger.error(f"{self.source.id}: Crawl error: {e}", exc_info=True)
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

    async def crawl_rss(self) -> List[RawEvent]:
        """Crawl WordPress RSS feed"""
        events = []

        try:
            # Fetch RSS feed with proper headers
            rss_content = await self.fetch_html(self.source.rss_feed)
            if not rss_content:
                logger.warning(f"{self.source.id}: Failed to fetch RSS feed")
                return events

            # Parse RSS content
            feed = feedparser.parse(rss_content)

            if not feed.entries:
                logger.warning(f"{self.source.id}: No entries in RSS feed")
                return events

            for entry in feed.entries[:10]:  # Limit to 10 most recent
                try:
                    # Extract data
                    title = entry.get('title', '')
                    link = entry.get('link', '')
                    summary = entry.get('summary', '') or entry.get('description', '')

                    # Parse date
                    pub_date = None
                    if hasattr(entry, 'published_parsed'):
                        pub_date = datetime(*entry.published_parsed[:6])

                    # Extract image
                    image_url = None
                    if hasattr(entry, 'media_content'):
                        image_url = entry.media_content[0].get('url')
                    elif 'media_thumbnail' in entry:
                        image_url = entry.media_thumbnail[0].get('url')

                    # Fetch full content if available
                    content = summary
                    if link:
                        full_content = await self.fetch_article_content(link)
                        if full_content:
                            content = full_content

                    # Create event
                    if title and link:
                        event = self.create_raw_event(
                            title=title,
                            content=content,
                            url=link,
                            date=pub_date,
                            image_url=image_url
                        )
                        events.append(event)

                    await self.apply_rate_limit()

                except Exception as e:
                    logger.error(f"{self.source.id}: Error parsing RSS entry: {e}")
                    continue

            logger.info(f"{self.source.id}: Extracted {len(events)} events from RSS")

        except Exception as e:
            logger.error(f"{self.source.id}: RSS feed error: {e}")

        return events

    async def fetch_article_content(self, url: str) -> str:
        """Fetch full article content from URL"""
        html = await self.fetch_html(url)
        if not html:
            return ""

        soup = self.parse_html(html)

        # Try common WordPress content selectors
        content_selectors = [
            self.source.selectors.get('content', ''),
            '.entry-content',
            '.post-content',
            'article .content',
            '[itemprop="articleBody"]'
        ]

        for selector in content_selectors:
            if selector:
                content_elem = soup.select_one(selector)
                if content_elem:
                    return content_elem.get_text(strip=True)

        return ""

    async def crawl_html(self) -> List[RawEvent]:
        """Crawl WordPress site by parsing HTML"""
        events = []

        try:
            # Fetch homepage or blog page
            html = await self.fetch_html(self.source.url)
            if not html:
                logger.error(f"{self.source.id}: Failed to fetch HTML from {self.source.url}")
                return events

            soup = self.parse_html(html)

            # Find article elements
            articles_selector = self.source.selectors.get('articles', '.post, article')
            articles = soup.select(articles_selector)

            logger.info(f"{self.source.id}: Found {len(articles)} articles with selector '{articles_selector}'")

            if not articles:
                logger.warning(f"{self.source.id}: No articles found with selector '{articles_selector}'")
                # Try to find what's actually on the page
                for fallback_selector in ['article', '.post', '[class*="post"]', '.entry', '.article']:
                    fallback = soup.select(fallback_selector)
                    if fallback:
                        logger.info(f"{self.source.id}: Found {len(fallback)} elements with fallback selector '{fallback_selector}'")
                return events

            parsed_count = 0
            for article in articles[:10]:  # Limit to 10 most recent
                try:
                    # Extract title
                    title_selector = self.source.selectors.get('title', 'h2.entry-title')
                    title_elem = article.select_one(title_selector)
                    title = self.extract_text(title_elem) if title_elem else ""

                    # Extract link - try multiple methods
                    link_selector = self.source.selectors.get('link', 'a')
                    link = ""
                    if title_elem:
                        # Try to find link in title element
                        link_tag = title_elem.find('a') if hasattr(title_elem, 'find') else None
                        if link_tag:
                            link = link_tag.get('href', '')

                    if not link:
                        # Try configured selector
                        link_elem = article.select_one(link_selector)
                        link = self.extract_link(link_elem) if link_elem else ""

                    if not link:
                        # Try to find any link in the article
                        any_link = article.find('a')
                        if any_link:
                            link = any_link.get('href', '')

                    # Extract content/excerpt
                    content_selector = self.source.selectors.get('content', '.entry-content')
                    content_elem = article.select_one(content_selector)
                    content = self.extract_text(content_elem) if content_elem else ""

                    # If no content found, try excerpt
                    if not content:
                        excerpt_elem = article.select_one('.entry-summary, .excerpt, .post-excerpt')
                        content = self.extract_text(excerpt_elem) if excerpt_elem else title

                    # Extract date
                    date_selector = self.source.selectors.get('date', 'time.entry-date')
                    date_elem = article.select_one(date_selector)
                    date_str = ""
                    if date_elem:
                        date_str = date_elem.get('datetime', '') or self.extract_text(date_elem)
                    event_date = self.parse_date(date_str) if date_str else None

                    # Extract image
                    image_selector = self.source.selectors.get('image', '.wp-post-image')
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
                        parsed_count += 1
                    else:
                        logger.debug(f"{self.source.id}: Skipping article - missing title or link (title: {bool(title)}, link: {bool(link)})")

                except Exception as e:
                    logger.error(f"{self.source.id}: Error parsing article: {e}", exc_info=True)
                    continue

            logger.info(f"{self.source.id}: Successfully parsed {parsed_count}/{len(articles)} articles from HTML")

        except Exception as e:
            logger.error(f"{self.source.id}: HTML crawl error: {e}")

        return events
