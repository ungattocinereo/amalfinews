"""
Batch processor for analyzing and translating articles with DeepSeek
Processes all articles in one API call for efficiency
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

from src.llm.deepseek_client import DeepSeekClient
from src.core.models import RawEvent
from src.core.config import get_config_loader


logger = logging.getLogger(__name__)


class BatchArticleProcessor:
    """Process articles in batch: filter + translate in one DeepSeek call"""

    def __init__(self, deepseek_client: DeepSeekClient):
        self.client = deepseek_client
        self.config_loader = get_config_loader()

    def prepare_articles_for_batch(self, raw_events: List[RawEvent]) -> List[Dict[str, Any]]:
        """Convert raw events to simple format for DeepSeek"""
        articles = []
        
        for idx, event in enumerate(raw_events):
            articles.append({
                "id": idx + 1,
                "title": event.title,
                "content": event.content[:1000],  # Limit content length
                "url": event.url,
                "date_scraped": event.scraped_at.strftime("%Y-%m-%d") if event.scraped_at else None,
                "source": event.source_id
            })
        
        return articles

    async def process_batch(self, raw_events: List[RawEvent]) -> List[Dict[str, Any]]:
        """
        Process all articles in one batch call to DeepSeek
        Returns list of processed events ready for output
        """
        if not raw_events:
            logger.info("No articles to process")
            return []

        logger.info(f"Processing batch of {len(raw_events)} articles...")

        # Prepare articles
        articles = self.prepare_articles_for_batch(raw_events)
        articles_json = json.dumps(articles, ensure_ascii=False, indent=2)

        # Get prompt
        prompt_config = self.config_loader.get_prompt("batch_filter_translate")
        system_message = prompt_config.get("system_message", "")
        user_template = prompt_config.get("user_template", "")

        # Format prompt
        user_message = user_template.format(
            count=len(articles),
            articles_json=articles_json,
            today_date=datetime.now().strftime("%Y-%m-%d")
        )

        try:
            # Call DeepSeek
            logger.info(f"Calling DeepSeek API with {len(articles)} articles...")
            response = await self.client.chat_completion(
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.2,
                max_tokens=4000
            )

            # Parse response
            content = response.get("content", "")
            logger.debug(f"DeepSeek response: {content[:500]}...")

            # Extract JSON from response
            processed_events = self._parse_response(content)
            
            logger.info(f"✅ Processed {len(processed_events)}/{len(articles)} articles successfully")
            
            return processed_events

        except Exception as e:
            logger.error(f"Batch processing failed: {e}", exc_info=True)
            return []

    def _parse_response(self, content: str) -> List[Dict[str, Any]]:
        """Parse DeepSeek JSON response"""
        try:
            # Try to find JSON array in response
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1
            
            if start_idx == -1 or end_idx == 0:
                logger.error("No JSON array found in response")
                return []
            
            json_str = content[start_idx:end_idx]
            events = json.loads(json_str)
            
            if not isinstance(events, list):
                logger.error("Response is not a JSON array")
                return []
            
            # Validate each event
            valid_events = []
            for event in events:
                if self._validate_event(event):
                    valid_events.append(event)
                else:
                    logger.warning(f"Invalid event format: {event.get('title', 'Unknown')}")
            
            return valid_events

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response content: {content}")
            return []
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            return []

    def _validate_event(self, event: Dict[str, Any]) -> bool:
        """Validate event has required fields"""
        required_fields = ["source_url", "title", "content"]
        
        for field in required_fields:
            if field not in event or not event[field]:
                logger.warning(f"Event missing required field: {field}")
                return False
        
        # Validate URL format
        if not event["source_url"].startswith("http"):
            logger.warning(f"Invalid URL: {event['source_url']}")
            return False
        
        return True

    def save_to_file(self, events: List[Dict[str, Any]], output_dir: str = "./data/processed"):
        """Save processed events to JSON file with timestamp"""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = output_path / f"processed_events_{timestamp}.json"
            
            output_data = {
                "processed_at": datetime.now().isoformat(),
                "total_events": len(events),
                "events": events
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Saved {len(events)} processed events to {filename}")
            
            return str(filename)

        except Exception as e:
            logger.error(f"Failed to save processed events: {e}")
            return None

    def save_raw_articles(self, raw_events: List[RawEvent], output_dir: str = "./data/raw"):
        """Save raw scraped articles to JSON file"""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = output_path / f"raw_articles_{timestamp}.json"
            
            articles = []
            for event in raw_events:
                articles.append({
                    "source_id": event.source_id,
                    "title": event.title,
                    "content": event.content,
                    "url": event.url,
                    "scraped_at": event.scraped_at.isoformat() if event.scraped_at else None,
                    "date": event.date.isoformat() if event.date else None
                })
            
            output_data = {
                "scraped_at": datetime.now().isoformat(),
                "total_articles": len(articles),
                "articles": articles
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Saved {len(articles)} raw articles to {filename}")
            
            return str(filename)

        except Exception as e:
            logger.error(f"Failed to save raw articles: {e}")
            return None
