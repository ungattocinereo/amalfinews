#!/usr/bin/env python3
"""
Test DeepSeek API connection
"""

import sys
import asyncio
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import get_config
from src.llm.deepseek_client import DeepSeekClient

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def main():
    """Test DeepSeek API"""
    logger.info("Testing DeepSeek API...")

    try:
        config = get_config()

        if not config.deepseek_api_key:
            logger.error("❌ DEEPSEEK_API_KEY not set in environment")
            sys.exit(1)

        # Create client
        client = DeepSeekClient(
            api_key=config.deepseek_api_key,
            endpoint=config.deepseek_endpoint,
            model=config.deepseek_model,
            temperature=config.deepseek_temperature,
            max_tokens=config.deepseek_max_tokens,
            timeout=config.deepseek_timeout
        )

        print("\n" + "="*60)
        print("DEEPSEEK API TEST")
        print("="*60 + "\n")

        print(f"Endpoint: {config.deepseek_endpoint}")
        print(f"Model: {config.deepseek_model}")
        print(f"API Key: {config.deepseek_api_key[:20]}...")
        print()

        # Test connection
        logger.info("Testing connection...")
        is_connected = await client.test_connection()

        if is_connected:
            print("✅ Connection successful!")
            print()

            # Test completion
            logger.info("Testing chat completion...")
            response = await client.chat_completion(
                system_message="You are a helpful assistant.",
                user_message="Say 'Hello from Amalfi!' in one sentence.",
                temperature=0.3
            )

            print("✅ Chat completion successful!")
            print(f"Response: {response}")
            print()

            # Show usage
            usage = client.get_total_usage()
            print(f"Total API calls: {usage['total_calls']}")
            print(f"Total tokens: {usage['total_tokens']}")
            print(f"Total cost: ${usage['total_cost']:.4f}")

        else:
            print("❌ Connection failed!")
            sys.exit(1)

        print("\n" + "="*60)
        print("TEST COMPLETE")
        print("="*60)

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
