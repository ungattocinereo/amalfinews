# Deployment Guide - Mac Mini Setup

## System Requirements

- **Hardware:** Mac Mini M1/M2
- **RAM:** 16GB recommended (8GB minimum)
- **Storage:** 20GB free space
- **OS:** macOS Sonoma/Sequoia
- **Network:** Stable internet connection

## Initial Setup

### 1. Install Python 3.11+

```bash
# Check Python version
python3 --version

# If needed, install via Homebrew
brew install python@3.11
```

### 2. Clone Repository

```bash
cd ~/Projects  # or your preferred location
git clone <repository-url> amalfinews
cd amalfinews
```

### 3. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright browsers (for JavaScript-heavy sites)
playwright install
```

## Configuration

### 1. Environment Variables

```bash
cp .env.example .env
nano .env
```

**Required variables:**
```bash
# DeepSeek API
DEEPSEEK_API_KEY=sk-40c7b8b70652484989af0747043b4117

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_ADMIN_ID=your_telegram_id

# WordPress
WORDPRESS_URL=https://your-site.com
WORDPRESS_USERNAME=admin
WORDPRESS_APP_PASSWORD=your_app_password
```

### 2. Get API Keys

**DeepSeek API:**
- Already provided: `sk-40c7b8b70652484989af0747043b4117`
- Dashboard: https://platform.deepseek.com

**Telegram Bot:**
1. Message @BotFather on Telegram
2. Send `/newbot`
3. Follow instructions
4. Copy bot token

**Your Telegram ID:**
1. Message @userinfobot
2. Copy your user ID

**WordPress App Password:**
1. Login to WordPress admin
2. Users → Profile
3. Scroll to "Application Passwords"
4. Create new password
5. Copy generated password

### 3. Initialize Database

```bash
python scripts/setup_database.py
```

### 4. Test Setup

```bash
# Test sources
python scripts/test_sources.py

# Test DeepSeek API
python scripts/test_deepseek.py

# Test full workflow (dry run)
DRY_RUN_MODE=true python scripts/daily_run.py
```

## Automation with Cron

### 1. Edit Crontab

```bash
crontab -e
```

### 2. Add Daily Schedule

```bash
# Run daily at 4:05 AM
5 4 * * * cd ~/Projects/amalfinews && ./venv/bin/python scripts/daily_run.py >> logs/cron.log 2>&1

# Weekly cleanup (Sunday 2 AM)
0 2 * * 0 cd ~/Projects/amalfinews && ./venv/bin/python scripts/cleanup.py >> logs/cron.log 2>&1
```

### 3. Verify Cron

```bash
crontab -l
```

## Running the System

### Manual Execution

```bash
# Activate environment
source venv/bin/activate

# Full daily run
python scripts/daily_run.py

# Individual stages
python scripts/daily_run.py --stage health_check
python scripts/daily_run.py --stage crawl
python scripts/daily_run.py --stage filter
python scripts/daily_run.py --stage translate
```

### Telegram Bot

```bash
# Start bot (keeps running)
python -m src.telegram.bot

# Or run in background
nohup python -m src.telegram.bot &
```

### Monitoring

```bash
# View logs
tail -f logs/daily_run.log
tail -f logs/crawler.log

# Check database
sqlite3 data/events.db "SELECT COUNT(*) FROM raw_events;"
sqlite3 data/events.db "SELECT COUNT(*) FROM processed_events WHERE status='pending';"

# System status
python -c "from src.monitoring.dashboard import display_status; display_status()"
```

## Maintenance

### Daily Tasks
- Monitor Telegram for pending events
- Approve/reject events via bot
- Check logs for errors

### Weekly Tasks
- Backup database: `cp data/events.db data/backups/events_$(date +%Y%m%d).db`
- Review source health trends
- Check DeepSeek API usage

### Monthly Tasks
- Update source configurations if sites change
- Review and update LLM prompts
- Analyze published events performance

## Troubleshooting

### Cron job not running
```bash
# Check cron logs
tail -f /var/log/system.log | grep cron

# Test manually
cd ~/Projects/amalfinews && ./venv/bin/python scripts/daily_run.py
```

### Permission errors
```bash
chmod +x scripts/*.py
chmod -R 755 logs/
chmod -R 755 data/
```

### Virtual environment issues
```bash
deactivate
rm -rf venv/
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Database corruption
```bash
# Backup current
cp data/events.db data/events_backup.db

# Reinitialize
rm data/events.db
python scripts/setup_database.py
```

## Security Best Practices

1. **Never commit .env file** - Contains sensitive API keys
2. **Restrict file permissions** - `chmod 600 .env`
3. **Regularly rotate passwords** - WordPress app passwords
4. **Monitor API usage** - Check DeepSeek dashboard
5. **Keep dependencies updated** - `pip list --outdated`

## Performance Optimization

### Memory Usage
```bash
# Check memory
top -pid $(pgrep -f daily_run.py)

# If high memory, reduce concurrency in settings.yaml:
max_concurrent_crawlers: 2
max_concurrent_translations: 3
```

### Disk Space
```bash
# Check usage
du -sh data/ logs/

# Clean old logs
find logs/ -name "*.log" -mtime +30 -delete

# Clean old events
python scripts/cleanup.py --days 90
```

## Backup Strategy

### Automated Backups

Add to crontab:
```bash
# Daily database backup
0 3 * * * cp ~/Projects/amalfinews/data/events.db ~/Backups/events_$(date +\%Y\%m\%d).db
```

### Manual Backup
```bash
# Full backup
tar -czf amalfinews_backup_$(date +%Y%m%d).tar.gz \
  --exclude='venv' \
  --exclude='logs/*.log' \
  amalfinews/
```

## Updating the System

```bash
cd ~/Projects/amalfinews
source venv/bin/activate

# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Run migrations if any
python scripts/migrate.py

# Restart services
pkill -f "telegram.bot"
python -m src.telegram.bot &
```
