"""
LLM-powered event translation
"""

import logging
from datetime import datetime
from typing import Optional

from src.core.models import RawEvent, ProcessedEvent, TranslationResult, EventCategory, EventStatus
from src.llm.deepseek_client import DeepSeekClient
from src.llm.prompts import get_prompt_manager


logger = logging.getLogger(__name__)


class EventTranslator:
    """Translate events using DeepSeek API"""

    def __init__(self, client: DeepSeekClient):
        self.client = client
        self.prompt_manager = get_prompt_manager()

    async def translate_event(self, event: RawEvent) -> Optional[ProcessedEvent]:
        """
        Translate single event from Italian to English
        Returns ProcessedEvent or None if invalid
        """
        logger.info(f"Translating event {event.id}: {event.title[:50]}")

        try:
            # Get prompt
            system_msg, user_msg = self.prompt_manager.get_translation_prompt(
                title=event.title,
                content=event.content,
                event_date=str(event.event_date) if event.event_date else "",
                source_url=event.source_url,
                today_date=datetime.now().strftime('%Y-%m-%d')
            )

            # Call DeepSeek API
            temperature = self.prompt_manager.get_temperature_for_task('translation')

            response = await self.client.json_completion(
                system_message=system_msg,
                user_message=user_msg,
                temperature=temperature
            )

            # Validate response
            if not self.prompt_manager.validate_translation_response(response):
                logger.error(f"Invalid translation response for event {event.id}")
                return None

            # Create TranslationResult
            result = self._parse_translation_response(response)

            # Check if valid
            if not result.is_valid:
                logger.info(f"Event {event.id} rejected: {result.rejection_reason}")
                return None

            # Create ProcessedEvent
            processed = self._create_processed_event(event, result)

            logger.info(f"Event {event.id} translated successfully")
            return processed

        except Exception as e:
            logger.error(f"Translation failed for event {event.id}: {e}")
            return None

    def _parse_translation_response(self, response: dict) -> TranslationResult:
        """Parse API response into TranslationResult"""
        return TranslationResult(
            is_valid=response.get('is_valid', False),
            title_en=response.get('title_en'),
            description_en=response.get('description_en'),
            event_date=response.get('event_date'),
            event_time=response.get('event_time'),
            location=response.get('location'),
            price_info=response.get('price_info'),
            accessibility=response.get('accessibility'),
            category=response.get('category'),
            keywords=response.get('keywords', []),
            rejection_reason=response.get('rejection_reason')
        )

    def _create_processed_event(self, raw: RawEvent,
                               result: TranslationResult) -> ProcessedEvent:
        """Create ProcessedEvent from RawEvent and TranslationResult"""

        # Parse event date
        try:
            event_date = datetime.strptime(result.event_date, '%Y-%m-%d')
        except:
            event_date = raw.event_date or datetime.now()

        # Parse category
        try:
            category = EventCategory(result.category) if result.category else EventCategory.OTHER
        except ValueError:
            category = EventCategory.OTHER

        return ProcessedEvent(
            original_id=raw.id,
            title_en=result.title_en,
            description_en=result.description_en,
            event_date=event_date,
            event_time=result.event_time,
            location=result.location or "",
            price_info=result.price_info,
            accessibility=result.accessibility,
            category=category,
            image_url=raw.image_url,
            keywords=result.keywords,
            status=EventStatus.PENDING,
            created_at=datetime.now()
        )

    async def translate_multiple(self, events: list[RawEvent],
                                max_concurrent: int = 5) -> list[ProcessedEvent]:
        """
        Translate multiple events with concurrency control
        """
        import asyncio

        logger.info(f"Translating {len(events)} events (max {max_concurrent} concurrent)")

        # Create semaphore for concurrency
        semaphore = asyncio.Semaphore(max_concurrent)

        async def translate_with_limit(event):
            async with semaphore:
                return await self.translate_event(event)

        # Translate all events
        tasks = [translate_with_limit(event) for event in events]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out None and exceptions
        processed_events = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Translation exception for event {events[i].id}: {result}")
            elif result is not None:
                processed_events.append(result)

        logger.info(f"Translation complete: {len(processed_events)}/{len(events)} successful")

        return processed_events

    def validate_translation(self, processed: ProcessedEvent) -> tuple[bool, list[str]]:
        """
        Validate processed event quality
        Returns (is_valid, list_of_errors)
        """
        errors = []

        # Check required fields
        if not processed.title_en:
            errors.append("Missing title")

        if not processed.description_en:
            errors.append("Missing description")

        if not processed.location:
            errors.append("Missing location")

        # Check description length (word count)
        word_count = len(processed.description_en.split())
        if word_count < 50:
            errors.append(f"Description too short ({word_count} words)")
        elif word_count > 250:
            errors.append(f"Description too long ({word_count} words)")

        # Check event date is in future
        if processed.event_date < datetime.now():
            errors.append("Event date is in the past")

        # Check title length
        if len(processed.title_en) > 100:
            errors.append("Title too long")

        return len(errors) == 0, errors
