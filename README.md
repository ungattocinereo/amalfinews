# Amalfi Events Intelligence

**Automated Event Collection & Translation System for Amalfi Coast Tourism**

Version 4.0 | DeepSeek API Edition | Docker + Telegram

## Overview

Automated system for collecting, analyzing, and translating tourist events from the Amalfi Coast region (Italy) for international visitors. The system runs in Docker with **DeepSeek API** for intelligent content processing and delivers ready-to-publish content via Telegram.

### What It Does

- **Scrapes** 11 Italian news websites daily for event information
- **Filters** relevant tourist events using DeepSeek AI
- **Translates** Italian content to tourist-friendly English
- **Moderates** via Telegram bot interface
- **Delivers** translated events ready for you to publish

## Key Features

- 🕷️ **Multi-Source Crawling** - 11 Italian news websites
- 🤖 **AI-Powered Filtering** - DeepSeek API batch processing
- 🌍 **Smart Translation** - Tourist-optimized English content
- 📱 **Telegram Moderation** - Easy approval workflow
- 💾 **Database Storage** - All events in SQLite for export
- 📊 **Real-Time Monitoring** - Web interface with dashboard
- 🔧 **Health Checks** - Automatic source validation
- 🐳 **Docker Ready** - One-command installation

## Architecture

```
News Sites → Health Check → Crawler → SQLite → DeepSeek Filter
                                                      ↓
WordPress ← Telegram Moderation ← DeepSeek Translation
```

## Quick Start

### 🐳 Docker (Recommended)

**Fastest way to get started:**

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit with your API keys
nano .env

# 3. Start container on random port
./docker-start.sh

# 4. Access web interface
# The script will show you the URL, e.g., http://localhost:32768
```

**Features:**
- ✅ Runs on random available port (no conflicts)
- ✅ Web monitoring dashboard
- ✅ Automatic daily runs at 4:05 AM
- ✅ REST API for control and monitoring
- ✅ Persistent data via Docker volumes

[Full Docker Documentation →](docs/DOCKER.md)

### 📦 Manual Installation

**For development or non-Docker environments:**

#### Prerequisites

- Python 3.11+
- Mac Mini (16GB RAM recommended) or any Linux/macOS
- DeepSeek API key
- Telegram Bot token
- WordPress site with REST API

#### Installation

```bash
# Clone repository
cd amalfinews

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your credentials

# Initialize database
python scripts/setup_database.py

# Test sources
python scripts/test_sources.py

# Test DeepSeek API
python scripts/test_deepseek.py
```

### Daily Execution

```bash
# Manual run
python scripts/daily_run.py

# Or setup cron (runs daily at 4:05 AM)
5 4 * * * cd /path/to/amalfinews && ./venv/bin/python scripts/daily_run.py
```

## Data Sources

The system monitors 11 Italian websites:

1. **amalfinews.it** - Amalfi news
2. **amalfinotizie.it** - Amalfi news & events
3. **booble.it** - Events & entertainment
4. **ilvescovado.it** - Local news & events
5. **ilporticoamalfi.it** - Amalfi culture & shows
6. **maiorinews.it** - Maiori news
7. **occhisusalerno.it** - Salerno culture
8. **positanonews.it** - Positano & Coast news
9. **positanonotizie.it** - Positano events
10. **ravellonotizie.it** - Ravello events
11. **salernotoday.it** - Salerno news

## Project Structure

```
amalfinews/
├── src/
│   ├── core/          # Database & models
│   ├── crawlers/      # Web scraping
│   ├── llm/           # DeepSeek API integration
│   ├── telegram/      # Moderation bot
│   ├── wordpress/     # Publishing
│   ├── images/        # Image processing
│   └── monitoring/    # Metrics & dashboard
├── config/            # Configuration files
├── scripts/           # Utility scripts
├── tests/             # Test suite
├── data/              # SQLite database
├── logs/              # Application logs
└── docs/              # Documentation

```

## Configuration

### Environment Variables (.env)

```bash
# DeepSeek API
DEEPSEEK_API_KEY=sk-your-key-here
DEEPSEEK_MODEL=deepseek-chat

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_ADMIN_ID=your_telegram_id

# WordPress
WORDPRESS_URL=https://your-site.com
WORDPRESS_USERNAME=admin
WORDPRESS_APP_PASSWORD=your_password

# System
DATABASE_PATH=./data/events.db
TIMEZONE=Europe/Rome
LOG_LEVEL=INFO
```

## Workflow Stages

1. **Health Check** (2 min) - Validate source availability
2. **Web Crawling** (15 min) - Scrape event articles
3. **Batch Filtering** (5 min) - AI-powered relevance check
4. **Translation** (10 min) - Tourist-friendly English
5. **Telegram Review** (on-demand) - Human moderation
6. **WordPress Publish** (instant) - Auto-publish approved events

## Telegram Commands

- `/events` - Show pending events for review
- `/stats` - View daily statistics
- `/sources` - Check source health status
- `/help` - Command list

## Monitoring

### Terminal Dashboard

```bash
# Real-time monitoring
python src/monitoring/dashboard.py
```

### Daily Statistics Report

Automatic Telegram report includes:
- Events scraped/filtered/translated
- Processing time breakdown
- DeepSeek API usage & cost
- System resource usage
- Error summary

## Testing

```bash
# Run all tests
pytest tests/ -v

# Test specific components
pytest tests/test_crawlers.py -v
pytest tests/test_llm.py -v

# Integration test
pytest tests/test_integration.py -v
```

## Documentation

- [API Documentation](docs/API.md) - DeepSeek API integration
- [Source Documentation](docs/SOURCES.md) - Website configurations
- [Deployment Guide](docs/DEPLOYMENT.md) - Mac Mini setup
- [Prompt Engineering](docs/PROMPTS.md) - LLM prompt versions

## Success Metrics

- **Uptime:** 95%+ system availability
- **Processing Time:** <30 min daily cycle
- **Events per Day:** 20+ scraped, 8-12 published
- **Filter Accuracy:** 80%+ relevant events
- **Translation Quality:** 90%+ human approval rate

## Troubleshooting

### Source Health Check Fails
```bash
# Test individual source
python scripts/test_sources.py --source amalfinews.it

# Check logs
tail -f logs/crawler.log
```

### DeepSeek API Issues
```bash
# Test API connection
python scripts/test_deepseek.py

# Check API usage
# Visit: https://platform.deepseek.com/usage
```

### Database Issues
```bash
# Backup database
cp data/events.db data/backups/events_$(date +%Y%m%d).db

# Reinitialize
python scripts/setup_database.py --reset
```

## License

Proprietary - Amalfi Events Intelligence System

## Contact

For issues and support, please check the logs and documentation.

---

**Built with:** Python, DeepSeek AI, Telegram, WordPress
**Platform:** Mac Mini (Local Network)
**Created:** September 2025
