# DeepSeek API Integration

## Overview

The Amalfi Events system uses DeepSeek API for AI-powered event filtering and translation.

## Authentication

```python
from src.llm.deepseek_client import DeepSeekClient

client = DeepSeekClient(
    api_key="sk-40c7b8b70652484989af0747043b4117",
    endpoint="https://api.deepseek.com/v1/chat/completions",
    model="deepseek-chat",
    temperature=0.1,
    max_tokens=500,
    timeout=30
)
```

## API Operations

### 1. Batch Filtering

Filters multiple events to identify tourist-relevant content.

**Input:** List of Italian event articles
**Output:** List of relevant event IDs

**Example:**
```python
from src.llm.filter import EventFilter

filter = EventFilter(client)
result = await filter.batch_filter_events(events, batch_size=20)

# result.relevant_ids = [1, 5, 12, ...]
# result.reasoning = {1: "Public concert", 5: "Food festival", ...}
```

### 2. Individual Translation

Translates single event from Italian to English.

**Input:** Raw Italian event
**Output:** Translated ProcessedEvent or None

**Example:**
```python
from src.llm.translator import EventTranslator

translator = EventTranslator(client)
processed = await translator.translate_event(raw_event)

if processed:
    print(processed.title_en)
    print(processed.description_en)
```

## Pricing

DeepSeek API pricing (as of 2025):
- **Input:** $0.14 per 1M tokens
- **Output:** $0.28 per 1M tokens

**Estimated daily cost:**
- ~20 events scraped
- ~15 filter API calls (batch)
- ~12 translation calls (individual)
- **Total:** ~15,000 tokens = **$0.03-0.05 per day**

## Rate Limits

- No strict rate limit
- Recommended: 3 retries with exponential backoff
- Timeout: 30 seconds per request

## Error Handling

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2))
async def safe_api_call():
    return await client.complete(messages)
```

## Monitoring Usage

```python
usage = client.get_total_usage()
print(f"Total calls: {usage['total_calls']}")
print(f"Total tokens: {usage['total_tokens']}")
print(f"Total cost: ${usage['total_cost']:.3f}")
```

## API Reference

- **Endpoint:** https://api.deepseek.com/v1/chat/completions
- **Documentation:** https://platform.deepseek.com/api-docs
- **Dashboard:** https://platform.deepseek.com/usage
