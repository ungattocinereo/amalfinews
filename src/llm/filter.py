"""
LLM-powered event filtering
"""

import logging
from typing import List
from datetime import datetime

from src.core.models import RawEvent, FilterResult
from src.llm.deepseek_client import DeepSeekClient
from src.llm.prompts import get_prompt_manager


logger = logging.getLogger(__name__)


class EventFilter:
    """Filter events using DeepSeek API"""

    def __init__(self, client: DeepSeekClient):
        self.client = client
        self.prompt_manager = get_prompt_manager()

    async def batch_filter_events(self, events: List[RawEvent],
                                  batch_size: int = 20) -> FilterResult:
        """
        Filter batch of events for tourist relevance
        Returns FilterResult with relevant event IDs
        """
        if not events:
            return FilterResult(relevant_ids=[], reasoning={})

        logger.info(f"Filtering {len(events)} events in batches of {batch_size}")

        all_relevant_ids = []
        all_reasoning = {}

        # Process in batches
        for i in range(0, len(events), batch_size):
            batch = events[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1} ({len(batch)} events)")

            try:
                result = await self._filter_batch(batch)
                all_relevant_ids.extend(result.relevant_ids)
                all_reasoning.update(result.reasoning)

            except Exception as e:
                logger.error(f"Batch filtering failed: {e}")
                continue

        logger.info(f"Filter complete: {len(all_relevant_ids)}/{len(events)} events passed")

        return FilterResult(
            relevant_ids=all_relevant_ids,
            reasoning=all_reasoning,
            timestamp=datetime.now()
        )

    async def _filter_batch(self, events: List[RawEvent]) -> FilterResult:
        """Filter a single batch of events"""

        # Prepare articles data
        articles = []
        for event in events:
            articles.append({
                'id': event.id,
                'title': event.title,
                'content': event.content[:500],  # First 500 chars
                'date': str(event.event_date) if event.event_date else 'unknown'
            })

        # Get prompt
        system_msg, user_msg = self.prompt_manager.get_batch_filter_prompt(
            articles=articles,
            today_date=datetime.now().strftime('%Y-%m-%d')
        )

        # Call DeepSeek API
        temperature = self.prompt_manager.get_temperature_for_task('filtering')

        try:
            response = await self.client.json_completion(
                system_message=system_msg,
                user_message=user_msg,
                temperature=temperature
            )

            # Validate response
            if not self.prompt_manager.validate_filter_response(response):
                logger.error(f"Invalid filter response format: {response}")
                return FilterResult(relevant_ids=[], reasoning={})

            relevant_ids = response.get('relevant_ids', [])
            reasoning = response.get('reasoning', {})

            # Convert string keys to int
            reasoning_int = {}
            if isinstance(reasoning, dict):
                for key, value in reasoning.items():
                    try:
                        reasoning_int[int(key)] = value
                    except (ValueError, TypeError):
                        continue

            logger.info(f"Batch result: {len(relevant_ids)} relevant events")

            return FilterResult(
                relevant_ids=relevant_ids,
                reasoning=reasoning_int,
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"Batch filter API call failed: {e}")
            return FilterResult(relevant_ids=[], reasoning={})

    def get_relevant_events(self, events: List[RawEvent],
                          filter_result: FilterResult) -> List[RawEvent]:
        """
        Extract relevant events based on filter result
        """
        relevant_ids_set = set(filter_result.relevant_ids)
        relevant_events = [e for e in events if e.id in relevant_ids_set]

        logger.info(f"Extracted {len(relevant_events)} relevant events")
        return relevant_events

    async def is_event_relevant(self, event: RawEvent) -> tuple[bool, str]:
        """
        Check if single event is relevant
        Returns (is_relevant, reason)
        """
        result = await self.batch_filter_events([event], batch_size=1)

        is_relevant = event.id in result.relevant_ids
        reason = result.reasoning.get(event.id, "No reason provided")

        return is_relevant, reason
