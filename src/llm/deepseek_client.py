"""
DeepSeek API client for LLM operations
"""

import logging
import json
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.models import DeepSeekUsage


logger = logging.getLogger(__name__)


class DeepSeekClient:
    """Client for DeepSeek API"""

    def __init__(self, api_key: str, endpoint: str, model: str = "deepseek-chat",
                 temperature: float = 0.1, max_tokens: int = 500, timeout: int = 30):
        self.api_key = api_key
        self.endpoint = endpoint
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

        self.total_usage = []

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=10))
    async def complete(self, messages: list, temperature: Optional[float] = None,
                      max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """
        Send completion request to DeepSeek API
        Returns response dict
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature or self.temperature,
            "max_tokens": max_tokens or self.max_tokens
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.endpoint,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:

                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"DeepSeek API error {response.status}: {error_text}")
                        raise Exception(f"API error: {response.status}")

                    result = await response.json()

                    # Track usage
                    if 'usage' in result:
                        usage = DeepSeekUsage(
                            timestamp=datetime.now(),
                            operation="completion",
                            prompt_tokens=result['usage'].get('prompt_tokens', 0),
                            completion_tokens=result['usage'].get('completion_tokens', 0),
                            total_tokens=result['usage'].get('total_tokens', 0),
                            cost=self.calculate_cost(result['usage']),
                            success=True
                        )
                        self.total_usage.append(usage)

                    return result

        except asyncio.TimeoutError:
            logger.error("DeepSeek API timeout")
            raise Exception("API timeout")
        except Exception as e:
            logger.error(f"DeepSeek API request failed: {e}")
            raise

    async def chat_completion(self, system_message: str, user_message: str,
                             temperature: Optional[float] = None) -> str:
        """
        Simple chat completion
        Returns assistant's response text
        """
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]

        response = await self.complete(messages, temperature=temperature)

        if 'choices' in response and len(response['choices']) > 0:
            return response['choices'][0]['message']['content']

        raise Exception("No response from API")

    async def json_completion(self, system_message: str, user_message: str,
                             temperature: Optional[float] = None) -> Dict:
        """
        Request JSON response and parse it
        Returns parsed JSON dict
        """
        # Add JSON instruction to system message
        system_with_json = f"{system_message}\n\nYou must respond with valid JSON only, no other text."

        response_text = await self.chat_completion(system_with_json, user_message, temperature)

        # Extract JSON from response (handle markdown code blocks)
        json_text = response_text.strip()
        if json_text.startswith('```json'):
            json_text = json_text[7:]
        if json_text.startswith('```'):
            json_text = json_text[3:]
        if json_text.endswith('```'):
            json_text = json_text[:-3]

        json_text = json_text.strip()

        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {response_text[:200]}")
            raise Exception(f"Invalid JSON response: {e}")

    def calculate_cost(self, usage: Dict) -> float:
        """
        Calculate cost based on DeepSeek pricing
        Input: $0.14 per 1M tokens
        Output: $0.28 per 1M tokens
        """
        prompt_tokens = usage.get('prompt_tokens', 0)
        completion_tokens = usage.get('completion_tokens', 0)

        prompt_cost = (prompt_tokens / 1_000_000) * 0.14
        completion_cost = (completion_tokens / 1_000_000) * 0.28

        return prompt_cost + completion_cost

    def get_total_usage(self) -> Dict:
        """Get total usage statistics"""
        if not self.total_usage:
            return {
                'total_calls': 0,
                'total_tokens': 0,
                'total_cost': 0.0
            }

        return {
            'total_calls': len(self.total_usage),
            'total_tokens': sum(u.total_tokens for u in self.total_usage),
            'prompt_tokens': sum(u.prompt_tokens for u in self.total_usage),
            'completion_tokens': sum(u.completion_tokens for u in self.total_usage),
            'total_cost': sum(u.cost for u in self.total_usage)
        }

    async def test_connection(self) -> bool:
        """Test API connection"""
        try:
            response = await self.chat_completion(
                system_message="You are a helpful assistant.",
                user_message="Reply with 'OK' if you can read this.",
                temperature=0.1
            )
            return 'ok' in response.lower()
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
