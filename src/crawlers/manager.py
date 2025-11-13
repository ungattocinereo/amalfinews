"""
Crawler manager - orchestrates crawling across sources
"""

import asyncio
import logging
from typing import List
from datetime import datetime

from src.core.models import SourceConfig, SourceType, RawEvent, CrawlerResult
from src.crawlers.wordpress_crawler import WordPressCrawler
from src.crawlers.custom_crawler import CustomCrawler
from src.crawlers.playwright_crawler import PlaywrightCrawler
from src.monitoring.progress_tracker import progress_tracker


logger = logging.getLogger(__name__)


class CrawlerManager:
    """Manage crawling across multiple sources"""

    def __init__(self, timeout: int = 10, user_agent: str = ""):
        self.timeout = timeout
        self.user_agent = user_agent
        self.use_progress_tracking = True

    def create_crawler(self, source: SourceConfig):
        """Create appropriate crawler for source type"""
        # Use Playwright for sources with bot protection
        if source.use_playwright:
            logger.info(f"{source.id}: Using Playwright (bot protection detected)")
            return PlaywrightCrawler(source, self.timeout, self.user_agent)
        # Otherwise use standard crawlers
        elif source.type == SourceType.WORDPRESS:
            return WordPressCrawler(source, self.timeout, self.user_agent)
        else:
            return CustomCrawler(source, self.timeout, self.user_agent)

    async def crawl_source(self, source: SourceConfig) -> CrawlerResult:
        """Crawl a single source"""
        logger.info(f"Crawling {source.id}...")

        # Update progress tracker
        if self.use_progress_tracking:
            progress_tracker.update_source(source.id, source.name)

        try:
            crawler = self.create_crawler(source)
            result = await crawler.crawl()

            if result.success:
                logger.info(f"{source.id}: Found {len(result.events)} events in {result.duration_seconds:.1f}s")
                if self.use_progress_tracking:
                    progress_tracker.complete_source(source.id, len(result.events), success=True)
            else:
                logger.error(f"{source.id}: Crawl failed - {result.error}")
                if self.use_progress_tracking:
                    progress_tracker.complete_source(source.id, 0, success=False, error=result.error)

            return result

        except Exception as e:
            logger.error(f"{source.id}: Unexpected error - {e}", exc_info=True)
            if self.use_progress_tracking:
                progress_tracker.complete_source(source.id, 0, success=False, error=str(e))
            raise

    async def crawl_all(self, sources: List[SourceConfig],
                       max_concurrent: int = 3) -> List[CrawlerResult]:
        """
        Crawl all sources with concurrency limit
        """
        logger.info(f"Starting crawl of {len(sources)} sources (max {max_concurrent} concurrent)")
        start_time = datetime.now()

        # Initialize progress tracking
        if self.use_progress_tracking:
            progress_tracker.start_operation(len(sources))

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)

        async def crawl_with_limit(source):
            async with semaphore:
                return await self.crawl_source(source)

        # Crawl all sources
        tasks = [crawl_with_limit(source) for source in sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        crawler_results = []
        total_events = 0

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"{sources[i].id}: Exception during crawl: {result}")
                crawler_results.append(CrawlerResult(
                    source_id=sources[i].id,
                    success=False,
                    error=str(result),
                    events=[],
                    duration_seconds=0
                ))
            else:
                crawler_results.append(result)
                total_events += len(result.events)

        duration = (datetime.now() - start_time).total_seconds()
        successful = sum(1 for r in crawler_results if r.success)

        logger.info(f"Crawl complete: {successful}/{len(sources)} successful, "
                   f"{total_events} total events in {duration:.1f}s")

        # Finish progress tracking
        if self.use_progress_tracking:
            progress_tracker.finish_operation()

        return crawler_results

    def get_all_events(self, results: List[CrawlerResult]) -> List[RawEvent]:
        """Extract all events from crawler results"""
        all_events = []

        for result in results:
            if result.success:
                all_events.extend(result.events)

        return all_events

    async def cleanup(self):
        """Cleanup resources (close Playwright browser if used)"""
        try:
            await PlaywrightCrawler.close_browser()
            logger.info("Crawler manager cleanup complete")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
