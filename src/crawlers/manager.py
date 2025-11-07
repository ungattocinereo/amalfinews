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


logger = logging.getLogger(__name__)


class CrawlerManager:
    """Manage crawling across multiple sources"""

    def __init__(self, timeout: int = 10, user_agent: str = ""):
        self.timeout = timeout
        self.user_agent = user_agent

    def create_crawler(self, source: SourceConfig):
        """Create appropriate crawler for source type"""
        if source.type == SourceType.WORDPRESS:
            return WordPressCrawler(source, self.timeout, self.user_agent)
        else:
            return CustomCrawler(source, self.timeout, self.user_agent)

    async def crawl_source(self, source: SourceConfig) -> CrawlerResult:
        """Crawl a single source"""
        logger.info(f"Crawling {source.id}...")

        crawler = self.create_crawler(source)
        result = await crawler.crawl()

        if result.success:
            logger.info(f"{source.id}: Found {len(result.events)} events in {result.duration_seconds:.1f}s")
        else:
            logger.error(f"{source.id}: Crawl failed - {result.error}")

        return result

    async def crawl_all(self, sources: List[SourceConfig],
                       max_concurrent: int = 3) -> List[CrawlerResult]:
        """
        Crawl all sources with concurrency limit
        """
        logger.info(f"Starting crawl of {len(sources)} sources (max {max_concurrent} concurrent)")
        start_time = datetime.now()

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

        return crawler_results

    def get_all_events(self, results: List[CrawlerResult]) -> List[RawEvent]:
        """Extract all events from crawler results"""
        all_events = []

        for result in results:
            if result.success:
                all_events.extend(result.events)

        return all_events
