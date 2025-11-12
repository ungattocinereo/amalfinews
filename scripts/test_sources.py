#!/usr/bin/env python3
"""
Test script to diagnose source parsing issues
"""

import sys
import asyncio
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import get_enabled_sources
from src.crawlers.manager import CrawlerManager

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_source(source_id: str):
    """Test a specific source"""
    sources = get_enabled_sources()
    source = next((s for s in sources if s.id == source_id), None)

    if not source:
        logger.error(f"Source {source_id} not found!")
        return

    logger.info(f"\n{'='*60}")
    logger.info(f"Testing source: {source.name} ({source.id})")
    logger.info(f"URL: {source.url}")
    logger.info(f"Type: {source.type}")
    logger.info(f"RSS Feed: {source.rss_feed}")
    logger.info(f"{'='*60}\n")

    manager = CrawlerManager(timeout=15, user_agent="Mozilla/5.0")
    result = await manager.crawl_source(source)

    logger.info(f"\n{'='*60}")
    logger.info(f"RESULT for {source.id}:")
    logger.info(f"Success: {result.success}")
    logger.info(f"Events found: {len(result.events)}")
    logger.info(f"Duration: {result.duration_seconds:.2f}s")
    if result.error:
        logger.error(f"Error: {result.error}")
    logger.info(f"{'='*60}\n")

    # Show first few events
    for i, event in enumerate(result.events[:3]):
        logger.info(f"\nEvent {i+1}:")
        logger.info(f"  Title: {event.title[:100]}")
        logger.info(f"  URL: {event.url}")
        logger.info(f"  Date: {event.date}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test specific source
        asyncio.run(test_source(sys.argv[1]))
    else:
        print("Usage: python test_sources.py <source_id>")
        print("Example: python test_sources.py maiorinews")
