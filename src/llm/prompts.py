"""
Prompt templates and management
"""

import logging
from datetime import datetime
from typing import Dict, List
import json

from src.core.config import get_config_loader


logger = logging.getLogger(__name__)


class PromptManager:
    """Manage and format LLM prompts"""

    def __init__(self):
        self.prompts = get_config_loader().get_prompts()

    def get_batch_filter_prompt(self, articles: List[Dict], today_date: str = None) -> tuple[str, str]:
        """
        Create batch filtering prompt
        Returns (system_message, user_message)
        """
        prompt_config = self.prompts.get('batch_filter', {})

        system_message = prompt_config.get('system_message', '')
        user_template = prompt_config.get('user_template', '')

        if not today_date:
            today_date = datetime.now().strftime('%Y-%m-%d')

        # Format articles as JSON
        articles_json = json.dumps(articles, ensure_ascii=False, indent=2)

        # Format user message
        user_message = user_template.format(
            count=len(articles),
            articles_json=articles_json,
            today_date=today_date
        )

        return system_message, user_message

    def get_translation_prompt(self, title: str, content: str,
                              event_date: str = "", source_url: str = "",
                              today_date: str = None) -> tuple[str, str]:
        """
        Create translation prompt
        Returns (system_message, user_message)
        """
        prompt_config = self.prompts.get('translate', {})

        system_message = prompt_config.get('system_message', '')
        user_template = prompt_config.get('user_template', '')

        if not today_date:
            today_date = datetime.now().strftime('%Y-%m-%d')

        # Format user message
        user_message = user_template.format(
            title=title,
            content=content[:2000],  # Limit content length
            event_date=event_date or "Unknown",
            source_url=source_url,
            today_date=today_date
        )

        return system_message, user_message

    def get_duplicate_check_prompt(self, event_a: Dict, event_b: Dict) -> tuple[str, str]:
        """
        Create duplicate checking prompt
        Returns (system_message, user_message)
        """
        prompt_config = self.prompts.get('duplicate_check', {})

        system_message = prompt_config.get('system_message', '')
        user_template = prompt_config.get('user_template', '')

        user_message = user_template.format(
            title_a=event_a.get('title', ''),
            date_a=event_a.get('date', ''),
            location_a=event_a.get('location', ''),
            description_a=event_a.get('description', '')[:500],
            title_b=event_b.get('title', ''),
            date_b=event_b.get('date', ''),
            location_b=event_b.get('location', ''),
            description_b=event_b.get('description', '')[:500]
        )

        return system_message, user_message

    def get_enhancement_prompt(self, title_en: str, description_en: str,
                              location: str, event_date: str) -> tuple[str, str]:
        """
        Create content enhancement prompt
        Returns (system_message, user_message)
        """
        prompt_config = self.prompts.get('enhance', {})

        system_message = prompt_config.get('system_message', '')
        user_template = prompt_config.get('user_template', '')

        user_message = user_template.format(
            title_en=title_en,
            description_en=description_en,
            location=location,
            event_date=event_date
        )

        return system_message, user_message

    def validate_filter_response(self, response: Dict) -> bool:
        """Validate filter response structure"""
        return (
            isinstance(response, dict) and
            'relevant_ids' in response and
            isinstance(response['relevant_ids'], list)
        )

    def validate_translation_response(self, response: Dict) -> bool:
        """Validate translation response structure"""
        if not isinstance(response, dict):
            return False

        if not response.get('is_valid'):
            return 'rejection_reason' in response

        required_fields = ['title_en', 'description_en', 'event_date']
        return all(field in response for field in required_fields)

    def get_temperature_for_task(self, task: str) -> float:
        """Get recommended temperature for task type"""
        config = self.prompts.get('config', {})
        temperatures = config.get('temperature', {})

        task_temps = {
            'filtering': temperatures.get('filtering', 0.1),
            'translation': temperatures.get('translation', 0.3),
            'enhancement': temperatures.get('enhancement', 0.5),
            'duplicate_check': temperatures.get('duplicate_check', 0.1)
        }

        return task_temps.get(task, 0.3)

    def get_max_tokens_for_task(self, task: str) -> int:
        """Get recommended max_tokens for task type"""
        config = self.prompts.get('config', {})
        max_tokens = config.get('max_tokens', {})

        task_tokens = {
            'filtering': max_tokens.get('filtering', 500),
            'translation': max_tokens.get('translation', 600),
            'enhancement': max_tokens.get('enhancement', 400),
            'duplicate_check': max_tokens.get('duplicate_check', 300)
        }

        return task_tokens.get(task, 500)


# Singleton instance
_prompt_manager = None


def get_prompt_manager() -> PromptManager:
    """Get singleton PromptManager instance"""
    global _prompt_manager

    if _prompt_manager is None:
        _prompt_manager = PromptManager()

    return _prompt_manager
