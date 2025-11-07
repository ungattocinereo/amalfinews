# News Sources Documentation

## Overview

The system monitors 11 Italian news websites for event information about the Amalfi Coast region.

## Source Types

### WordPress Sites (9 sources)
- Use RSS feeds when available
- Fall back to HTML parsing
- Standard WordPress selectors

### Custom CMS (2 sources)
- HTML parsing only
- Custom selectors per site

## Source List

| ID | Name | Type | Priority | RSS Feed |
|----|------|------|----------|----------|
| amalfinews | Amalfi News | WordPress | 1 | ✅ |
| amalfinotizie | Amalfi Notizie | WordPress | 1 | ✅ |
| booble | Booble Eventi | Custom | 2 | ❌ |
| ilvescovado | Il Vescovado | WordPress | 2 | ✅ |
| ilporticoamalfi | Il Portico Amalfi | WordPress | 1 | ✅ |
| maiorinews | Maiori News | WordPress | 2 | ✅ |
| occhisusalerno | Occhi su Salerno | WordPress | 2 | ✅ |
| positanonews | Positano News | WordPress | 1 | ✅ |
| positanonotizie | Positano Notizie | WordPress | 1 | ✅ |
| ravellonotizie | Ravello Notizie | WordPress | 1 | ✅ |
| salernotoday | Salerno Today | Custom | 2 | ❌ |

## Adding New Sources

1. **Edit `config/sources.yaml`:**

```yaml
- id: "newsource"
  name: "New Source"
  url: "https://newsource.it"
  type: "wordpress"  # or "custom"
  enabled: true
  priority: 1
  rate_limit: 1.0
  selectors:
    articles: ".post"
    title: "h2.entry-title"
    date: "time.entry-date"
    content: ".entry-content"
    image: ".wp-post-image"
  rss_feed: "https://newsource.it/feed/"
```

2. **Test the source:**

```bash
python scripts/test_sources.py
```

3. **Verify articles are scraped:**

```bash
python scripts/daily_run.py --stage crawl
```

## Health Checks

Sources are tested before each scraping session:

- HTTP status (must be 200)
- Response time (<5 seconds)
- Content structure validation
- Article presence check

**Failed health checks:**
- Source is skipped for this session
- Error logged to `logs/crawler.log`
- Notification sent to Telegram (if enabled)
- Retry in next session

## Rate Limiting

Each source has a rate limit (requests per second):
- WordPress sites: 1.0 req/s
- Custom sites: 0.5 req/s

**Respect robots.txt:**
- Enabled by default
- Configurable in `config/settings.yaml`

## Troubleshooting

### Source always fails health check
- Check if URL is accessible
- Verify DNS resolution
- Check robots.txt restrictions
- Test manually with curl

### No articles found
- Verify selectors in sources.yaml
- Inspect page HTML structure
- Check if site structure changed
- Try RSS feed if available

### Images not extracted
- Check image selector
- Verify image URLs are absolute
- Check if images are lazy-loaded
- Update selector for data-src attribute
