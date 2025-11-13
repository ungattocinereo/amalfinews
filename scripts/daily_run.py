#!/usr/bin/env python3
"""
Daily automated run - main workflow
"""

import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import get_config, get_enabled_sources
from src.core.database import get_database
from src.crawlers.health_check import HealthChecker
from src.crawlers.manager import CrawlerManager
from src.llm.deepseek_client import DeepSeekClient
from src.llm.batch_processor import BatchArticleProcessor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./logs/daily_run.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """Main daily workflow"""
    start_time = datetime.now()
    logger.info("="*60)
    logger.info("🚀 STARTING DAILY RUN")
    logger.info("="*60)

    config = get_config()
    db = get_database(config.database_path)

    try:
        # ===== STAGE 1: Health Check =====
        logger.info("\n📋 Stage 1: Source Health Check")
        sources = get_enabled_sources()
        logger.info(f"Checking {len(sources)} sources...")

        checker = HealthChecker(timeout=10)
        health_results = await checker.check_all_sources(sources)

        healthy_sources = [
            s for s, h in zip(sources, health_results)
            if h.healthy
        ]

        logger.info(f"✅ {len(healthy_sources)}/{len(sources)} sources healthy")

        if not healthy_sources:
            logger.error("❌ No healthy sources found. Aborting.")
            return

        # ===== STAGE 2: Web Crawling =====
        logger.info("\n📋 Stage 2: Web Crawling")

        crawler_manager = CrawlerManager(
            timeout=config.crawl_timeout,
            user_agent=config.user_agent
        )

        crawl_results = await crawler_manager.crawl_all(
            healthy_sources,
            max_concurrent=3
        )

        # Cleanup Playwright resources
        await crawler_manager.cleanup()

        # Extract all events
        all_events = crawler_manager.get_all_events(crawl_results)
        logger.info(f"Scraped {len(all_events)} total articles")

        if not all_events:
            logger.warning("⚠️ No articles scraped. Ending run.")
            return

        # ===== STAGE 3: Save Raw Articles =====
        logger.info("\n📋 Stage 3: Saving Raw Articles")

        deepseek_client = DeepSeekClient(
            api_key=config.deepseek_api_key,
            endpoint=config.deepseek_endpoint,
            model=config.deepseek_model,
            temperature=config.deepseek_temperature,
            max_tokens=config.deepseek_max_tokens,
            timeout=config.deepseek_timeout
        )

        batch_processor = BatchArticleProcessor(deepseek_client)
        raw_file = batch_processor.save_raw_articles(all_events, output_dir="./data/raw")

        if raw_file:
            logger.info(f"✅ Raw articles saved to: {raw_file}")

        # ===== STAGE 4: Batch AI Processing =====
        logger.info("\n📋 Stage 4: AI Batch Processing (Filter + Translate)")

        processed_events = await batch_processor.process_batch(all_events)

        if not processed_events:
            logger.warning("⚠️ No tourist-relevant events found after AI analysis.")
            logger.info(f"Processed 0/{len(all_events)} articles successfully")
            return

        logger.info(f"✅ {len(processed_events)}/{len(all_events)} articles identified as tourist-relevant events")

        # ===== STAGE 5: Save Processed Events =====
        logger.info("\n📋 Stage 5: Saving Processed Events")

        output_file = batch_processor.save_to_file(processed_events, output_dir="./data/processed")

        if output_file:
            logger.info(f"✅ Processed events saved to: {output_file}")

            # Print sample of results
            logger.info("\n📋 Sample Results (first 3 events):")
            for i, event in enumerate(processed_events[:3], 1):
                logger.info(f"\n--- Event {i} ---")
                logger.info(f"Title: {event['title']}")
                logger.info(f"URL: {event['source_url']}")
                logger.info(f"Category: {event.get('category', 'N/A')}")
                logger.info(f"Date: {event.get('event_date', 'N/A')}")
                logger.info(f"Content: {event['content'][:150]}...")

        # ===== STAGE 6: Summary =====
        logger.info("\n📋 Stage 6: Results Ready")
        logger.info(f"✅ {len(processed_events)} tourist-relevant events processed")
        logger.info(f"📁 Raw articles: {raw_file}")
        logger.info(f"📁 Processed events: {output_file}")
        logger.info("💡 Events are ready for review and publishing")

        # ===== FINAL SUMMARY =====
        duration = (datetime.now() - start_time).total_seconds()

        logger.info("\n" + "="*60)
        logger.info("✅ DAILY RUN COMPLETE")
        logger.info("="*60)
        logger.info(f"Duration: {duration:.1f}s ({duration/60:.1f} minutes)")
        logger.info(f"Sources checked: {len(sources)}")
        logger.info(f"Healthy sources: {len(healthy_sources)}")
        logger.info(f"Articles scraped: {len(all_events)}")
        logger.info(f"Tourist events found: {len(processed_events)}")
        logger.info(f"Conversion rate: {len(processed_events)/len(all_events)*100:.1f}%")

        # API usage
        usage = deepseek_client.get_total_usage()
        logger.info(f"DeepSeek API calls: {usage['total_calls']}")
        logger.info(f"DeepSeek tokens used: {usage['total_tokens']}")
        logger.info(f"DeepSeek cost: ${usage['total_cost']:.3f}")

        logger.info("="*60)

    except Exception as e:
        logger.error(f"❌ Daily run failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
