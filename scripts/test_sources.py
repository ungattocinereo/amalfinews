#!/usr/bin/env python3
"""
Test all news sources health
"""

import sys
import asyncio
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import get_enabled_sources
from src.crawlers.health_check import HealthChecker

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def main():
    """Test all sources"""
    logger.info("Testing news sources...")

    try:
        # Get enabled sources
        sources = get_enabled_sources()
        logger.info(f"Found {len(sources)} enabled sources")

        # Create health checker
        checker = HealthChecker(timeout=5)

        # Check all sources
        results = await checker.check_all_sources(sources)

        # Display results
        print("\n" + "="*60)
        print("SOURCE HEALTH CHECK RESULTS")
        print("="*60 + "\n")

        healthy_count = 0

        for result in results:
            source_name = next((s.name for s in sources if s.url == result.url), "Unknown")
            status = "✅ HEALTHY" if result.healthy else "❌ UNHEALTHY"

            print(f"{status} | {source_name}")
            print(f"   URL: {result.url}")

            if result.healthy:
                print(f"   Response: {result.response_time:.2f}s")
                print(f"   Articles: {result.articles_found}")
                healthy_count += 1
            else:
                print(f"   Error: {result.error}")

            print()

        print("="*60)
        print(f"Summary: {healthy_count}/{len(sources)} sources healthy")
        print("="*60)

    except Exception as e:
        logger.error(f"Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
