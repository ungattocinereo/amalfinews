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
from src.llm.filter import EventFilter
from src.llm.translator import EventTranslator

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

        checker = HealthChecker(timeout=5)
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

        # Save raw events to database
        all_events = crawler_manager.get_all_events(crawl_results)
        logger.info(f"Scraped {len(all_events)} total events")

        for event in all_events:
            try:
                event_id = db.insert_raw_event(event)
                event.id = event_id
            except Exception as e:
                logger.error(f"Error saving event: {e}")

        if not all_events:
            logger.warning("⚠️ No events scraped. Ending run.")
            return

        # ===== STAGE 3: LLM Filtering =====
        logger.info("\n📋 Stage 3: AI Filtering")

        deepseek_client = DeepSeekClient(
            api_key=config.deepseek_api_key,
            endpoint=config.deepseek_endpoint,
            model=config.deepseek_model,
            temperature=config.deepseek_temperature,
            max_tokens=config.deepseek_max_tokens,
            timeout=config.deepseek_timeout
        )

        event_filter = EventFilter(deepseek_client)
        filter_result = await event_filter.batch_filter_events(
            all_events,
            batch_size=config.batch_size
        )

        relevant_events = event_filter.get_relevant_events(all_events, filter_result)
        logger.info(f"✅ {len(relevant_events)}/{len(all_events)} events passed filter")

        if not relevant_events:
            logger.warning("⚠️ No relevant events found. Ending run.")
            return

        # ===== STAGE 4: Translation =====
        logger.info("\n📋 Stage 4: Translation to English")

        translator = EventTranslator(deepseek_client)
        processed_events = await translator.translate_multiple(
            relevant_events,
            max_concurrent=5
        )

        logger.info(f"✅ {len(processed_events)} events translated successfully")

        # Save processed events
        for event in processed_events:
            try:
                event_id = db.insert_processed_event(event)
                logger.info(f"Saved processed event {event_id}: {event.title_en}")
            except Exception as e:
                logger.error(f"Error saving processed event: {e}")

        # Mark raw events as processed
        for event in relevant_events:
            db.mark_raw_event_processed(event.id, "Filtered and translated")

        # ===== STAGE 5: Events ready for moderation =====
        logger.info("\n📋 Stage 5: Events ready")
        logger.info(f"✅ {len(processed_events)} events waiting in database")
        logger.info("📱 Check Telegram bot to review and moderate events")
        logger.info("💡 Approved events can be published manually from database")

        # ===== FINAL SUMMARY =====
        duration = (datetime.now() - start_time).total_seconds()

        logger.info("\n" + "="*60)
        logger.info("✅ DAILY RUN COMPLETE")
        logger.info("="*60)
        logger.info(f"Duration: {duration:.1f}s ({duration/60:.1f} minutes)")
        logger.info(f"Sources checked: {len(sources)}")
        logger.info(f"Healthy sources: {len(healthy_sources)}")
        logger.info(f"Events scraped: {len(all_events)}")
        logger.info(f"Events filtered: {len(relevant_events)}")
        logger.info(f"Events translated: {len(processed_events)}")

        # API usage
        usage = deepseek_client.get_total_usage()
        logger.info(f"DeepSeek calls: {usage['total_calls']}")
        logger.info(f"DeepSeek tokens: {usage['total_tokens']}")
        logger.info(f"DeepSeek cost: ${usage['total_cost']:.3f}")

        logger.info("="*60)

    except Exception as e:
        logger.error(f"❌ Daily run failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
