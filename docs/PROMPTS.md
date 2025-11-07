# Prompt Engineering Guide

## Overview

The system uses carefully crafted prompts for DeepSeek API to filter and translate events.

## Prompt Types

### 1. Batch Filtering Prompt

**Purpose:** Identify tourist-relevant events from Italian articles

**Temperature:** 0.1 (low creativity, objective filtering)

**Key Requirements:**
- JSON response format
- Clear inclusion/exclusion criteria
- Context about today's date
- Batch processing (up to 20 events)

**Version:** 3.0

### 2. Translation Prompt

**Purpose:** Translate and adapt events for English-speaking tourists

**Temperature:** 0.3 (moderate creativity, natural language)

**Key Requirements:**
- Simple English (B1 level)
- 50-150 words
- Tourist context (how to get there, accessibility)
- Practical information (time, price, location)
- Verification of future date

**Version:** 2.0

## Prompt Optimization

### Filtering Improvements

**v1.0 → v2.0:**
- Added explicit exclusion keywords
- Required date validation
- Added reasoning field

**v2.0 → v3.0:**
- Improved Italian cultural context
- Better religious vs. tourist event distinction
- Added today's date parameter

### Translation Improvements

**v1.0 → v2.0:**
- Reduced word count (200 → 150)
- Added B1 language level requirement
- Included accessibility information
- Added location context for foreigners

## Common Issues & Solutions

### Issue: Too many events filtered out
**Solution:** Adjust temperature to 0.2 or relax exclusion criteria

### Issue: Translations too short
**Solution:** Increase min_description_words in prompts.yaml

### Issue: Past events included
**Solution:** Verify {today_date} parameter is passed correctly

### Issue: Religious services included
**Solution:** Strengthen exclusion keywords in prompt

## Testing Prompts

```python
from src.llm.prompts import get_prompt_manager
from src.llm.deepseek_client import DeepSeekClient

pm = get_prompt_manager()
client = DeepSeekClient(...)

# Test filtering
system, user = pm.get_batch_filter_prompt(test_articles)
response = await client.json_completion(system, user)

# Test translation
system, user = pm.get_translation_prompt(title, content, date)
response = await client.json_completion(system, user)
```

## Prompt Version Management

All prompts are stored in `config/prompts.yaml`:

```yaml
prompts:
  batch_filter:
    version: "3.0"
    system_message: "..."
    user_template: "..."

  translate:
    version: "2.0"
    system_message: "..."
    user_template: "..."
```

**To update prompts:**
1. Edit `config/prompts.yaml`
2. Increment version number
3. Test with `python scripts/test_deepseek.py`
4. Monitor results for 2-3 days
5. Roll back if quality decreases

## Best Practices

1. **Always include version numbers** in prompts
2. **Test on sample data** before production
3. **Monitor approval rates** after changes
4. **Keep prompts simple** and specific
5. **Provide clear examples** in prompts
6. **Use structured output** (JSON) for consistency
