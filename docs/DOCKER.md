# Docker Deployment Guide

## Overview

Run the Amalfi Events Intelligence System in a Docker container with a web monitoring interface on a **random available port**.

## Quick Start

### 1. Prerequisites

- Docker installed (20.10+)
- Docker Compose installed (2.0+)

```bash
# Check versions
docker --version
docker-compose --version
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit with your API keys
nano .env
```

**Required configuration:**
```bash
# DeepSeek API (already provided)
DEEPSEEK_API_KEY=sk-40c7b8b70652484989af0747043b4117

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_ADMIN_ID=your_telegram_id

# WordPress
WORDPRESS_URL=https://your-site.com
WORDPRESS_USERNAME=admin
WORDPRESS_APP_PASSWORD=your_app_password
```

### 3. Start the Container

```bash
# Simple start
./docker-start.sh

# Or manually
docker-compose up -d
```

The system will:
- Build the Docker image
- Start the container
- Assign a **random available port** for the web interface
- Initialize the database
- Start the scheduler for daily runs at 4:05 AM

### 4. Find Your Assigned Port

```bash
# Get the assigned port
docker-compose port amalfi-events 8000

# Example output: 0.0.0.0:32768
# Your web interface is at http://localhost:32768
```

## Web Interface

Once running, access the monitoring dashboard:

```bash
# Get port
PORT=$(docker-compose port amalfi-events 8000 | cut -d: -f2)

# Open in browser
open http://localhost:$PORT  # macOS
xdg-open http://localhost:$PORT  # Linux
```

### Available Endpoints

| Endpoint | Description |
|----------|-------------|
| `/` | Web dashboard (HTML) |
| `/health` | Health check for Docker |
| `/status` | System status (JSON) |
| `/stats` | Daily statistics |
| `/sources/health` | Check all 11 news sources |
| `/events/pending` | Pending events for review |
| `/events/recent` | Recently processed events |
| `/run` | Trigger manual run (POST) |
| `/logs/recent` | Recent log entries |
| `/docs` | Interactive API documentation |

### Example API Calls

```bash
# Get assigned port
PORT=$(docker-compose port amalfi-events 8000 | cut -d: -f2)

# Check status
curl http://localhost:$PORT/status

# Check source health
curl http://localhost:$PORT/sources/health

# View statistics
curl http://localhost:$PORT/stats

# Trigger manual run (dry run)
curl -X POST http://localhost:$PORT/run \
  -H "Content-Type: application/json" \
  -d '{"dry_run": true}'
```

## Container Management

### Start/Stop/Restart

```bash
# Start
./docker-start.sh
# or
docker-compose up -d

# Stop
./docker-stop.sh
# or
docker-compose stop

# Restart
docker-compose restart

# Remove completely
docker-compose down
```

### View Logs

```bash
# Follow logs
./docker-logs.sh
# or
docker-compose logs -f

# View last 100 lines
docker-compose logs --tail=100

# View specific service logs
docker-compose logs amalfi-events
```

### Execute Commands in Container

```bash
# Open shell
docker-compose exec amalfi-events bash

# Run database setup
docker-compose exec amalfi-events python scripts/setup_database.py

# Test sources
docker-compose exec amalfi-events python scripts/test_sources.py

# Test DeepSeek API
docker-compose exec amalfi-events python scripts/test_deepseek.py

# Manual daily run
docker-compose exec amalfi-events python scripts/daily_run.py
```

## Container Modes

The container supports different startup modes:

### 1. Web Mode (Default)

Starts web server + scheduler:

```bash
docker-compose up -d
```

Features:
- Web interface on random port
- Scheduled daily runs at 4:05 AM
- REST API for monitoring
- Background task processing

### 2. Run Once Mode

Execute daily workflow and exit:

```bash
docker-compose run --rm amalfi-events run
```

Useful for:
- Testing the workflow
- Manual runs via cron outside Docker
- CI/CD pipelines

### 3. Shell Mode

Interactive shell access:

```bash
docker-compose run --rm amalfi-events shell
```

## Data Persistence

Data is persisted via Docker volumes:

```yaml
volumes:
  - ./data:/app/data        # SQLite database
  - ./logs:/app/logs        # Application logs
  - ./config:/app/config    # Configuration files
```

**On host machine:**
- Database: `./data/events.db`
- Logs: `./logs/daily_run.log`
- Config: `./config/*.yaml`

**Backup database:**
```bash
# Create backup
cp data/events.db data/backups/events_$(date +%Y%m%d).db

# Automated backup
docker-compose exec amalfi-events \
  cp /app/data/events.db /app/data/backups/backup_$(date +%Y%m%d).db
```

## Port Configuration

### Random Port (Default)

```yaml
ports:
  - "0:8000"  # Docker assigns random available port
```

Benefits:
- No port conflicts
- Multiple instances possible
- Automatic port selection

### Fixed Port

Edit `docker-compose.yml`:

```yaml
ports:
  - "8080:8000"  # Fixed to port 8080
```

### Custom Port Range

```yaml
ports:
  - "8000-8100:8000"  # Assign from range 8000-8100
```

## Environment Variables

All configuration via environment variables in `.env`:

### DeepSeek API
```bash
DEEPSEEK_API_KEY=sk-your-key
DEEPSEEK_ENDPOINT=https://api.deepseek.com/v1/chat/completions
DEEPSEEK_MODEL=deepseek-chat
```

### Telegram
```bash
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_ADMIN_ID=your_id
```

### WordPress
```bash
WORDPRESS_URL=https://your-site.com
WORDPRESS_USERNAME=admin
WORDPRESS_APP_PASSWORD=your_password
WORDPRESS_CATEGORY_ID=1
```

### Scheduling
```bash
DAILY_RUN_HOUR=4      # Run at 4 AM
DAILY_RUN_MINUTE=5    # Run at :05 minutes
```

### Features
```bash
ENABLE_AUTO_PUBLISH=false           # Auto-publish approved events
ENABLE_TELEGRAM_NOTIFICATIONS=true  # Send Telegram notifications
DRY_RUN_MODE=false                  # Test mode (no actual changes)
```

## Monitoring

### Health Checks

Docker automatically monitors container health:

```bash
# Check health status
docker-compose ps

# View health check logs
docker inspect --format='{{json .State.Health}}' amalfi-events | jq
```

Health check endpoint: `http://localhost:$PORT/health`

### Resource Usage

```bash
# Monitor resources
docker stats amalfi-events

# View detailed info
docker-compose exec amalfi-events top
```

### Application Metrics

Via web interface:
- CPU usage
- Memory consumption
- Database size
- Log file size
- Daily statistics

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs

# Check environment
docker-compose config

# Rebuild image
docker-compose build --no-cache
docker-compose up -d
```

### Can't find assigned port

```bash
# Get port mapping
docker-compose port amalfi-events 8000

# Or inspect container
docker inspect amalfi-events | grep HostPort

# Or check all mappings
docker-compose ps
```

### Database issues

```bash
# Reset database
docker-compose down
rm -rf data/events.db
docker-compose up -d

# Or reinitialize
docker-compose exec amalfi-events python scripts/setup_database.py
```

### Permission errors

```bash
# Fix permissions on host
chmod -R 755 data/ logs/

# Or run as root temporarily
docker-compose exec -u root amalfi-events bash
```

### Out of memory

Edit `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      memory: 2G
    reservations:
      memory: 512M
```

## Advanced Configuration

### Multiple Instances

Run multiple instances (different ports):

```bash
# Instance 1
docker-compose up -d

# Instance 2 (different project name)
docker-compose -p amalfi-events-2 up -d
```

### Custom Network

```yaml
networks:
  amalfi-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.25.0.0/16
```

### External Database

Use external PostgreSQL instead of SQLite:

1. Update configuration
2. Change DATABASE_PATH to connection string
3. Update database.py for PostgreSQL support

### Reverse Proxy

Behind nginx/traefik:

```nginx
server {
    listen 80;
    server_name events.example.com;

    location / {
        proxy_pass http://localhost:32768;  # Use assigned port
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Production Deployment

### Security Checklist

- [ ] Change default API keys in `.env`
- [ ] Set `ENABLE_AUTO_PUBLISH=false` initially
- [ ] Enable HTTPS with reverse proxy
- [ ] Restrict API access (firewall rules)
- [ ] Regular database backups
- [ ] Monitor logs for errors
- [ ] Set resource limits
- [ ] Use Docker secrets for sensitive data

### Backup Strategy

```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d)
docker-compose exec -T amalfi-events \
  sqlite3 /app/data/events.db ".backup /app/data/backups/events_$DATE.db"

# Keep last 30 days
find ./data/backups -name "events_*.db" -mtime +30 -delete
```

Add to cron:
```bash
0 2 * * * /path/to/backup-script.sh
```

### Monitoring & Alerts

Set up monitoring:
- Health check endpoint for uptime monitoring
- Log aggregation (ELK, Grafana)
- Alert on failed health checks
- Monitor API usage and costs

## Scaling

### Horizontal Scaling

Run multiple containers with load balancer:

```yaml
# docker-compose.scale.yml
services:
  amalfi-events:
    deploy:
      replicas: 3
```

```bash
docker-compose -f docker-compose.yml -f docker-compose.scale.yml up -d
```

### Performance Tuning

```yaml
environment:
  - MAX_CONCURRENT_CRAWLERS=5
  - MAX_CONCURRENT_TRANSLATIONS=10
  - BATCH_SIZE=30
```

## Useful Commands Reference

```bash
# Quick start
./docker-start.sh

# Stop
./docker-stop.sh

# View logs
./docker-logs.sh

# Get web interface URL
echo "http://localhost:$(docker-compose port amalfi-events 8000 | cut -d: -f2)"

# Shell access
docker-compose exec amalfi-events bash

# Manual run
docker-compose exec amalfi-events python scripts/daily_run.py

# Rebuild
docker-compose build --no-cache

# Clean everything
docker-compose down -v

# Export database
docker-compose exec -T amalfi-events \
  sqlite3 /app/data/events.db .dump > backup.sql
```

## Support

For issues:
1. Check logs: `docker-compose logs`
2. Verify environment: `docker-compose config`
3. Test components individually
4. Review documentation in `/docs`
