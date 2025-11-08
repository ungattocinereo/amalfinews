#!/bin/bash
set -e

echo "🚀 Starting Amalfi Events Intelligence System"

# Initialize database if it doesn't exist
if [ ! -f "/app/data/events.db" ]; then
    echo "📋 Initializing database..."
    python scripts/setup_database.py
fi

# Function to run daily workflow
run_daily_workflow() {
    echo "⏰ Running daily workflow at $(date)"
    python scripts/daily_run.py
}

# Start based on command
case "$1" in
    web)
        echo "🌐 Starting web server..."

        # Start scheduler in background for daily runs
        python -c "
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import logging
import os
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('scheduler')

def run_daily():
    logger.info('Triggering daily run...')
    subprocess.run(['python', 'scripts/daily_run.py'])

scheduler = BackgroundScheduler()

# Get schedule from environment
hour = int(os.getenv('DAILY_RUN_HOUR', 4))
minute = int(os.getenv('DAILY_RUN_MINUTE', 5))

scheduler.add_job(run_daily, 'cron', hour=hour, minute=minute)
scheduler.start()

logger.info(f'Scheduler started. Daily runs at {hour:02d}:{minute:02d}')

# Keep scheduler running
import time
while True:
    time.sleep(60)
" &

        # Start web server
        exec uvicorn src.web.api:app --host 0.0.0.0 --port 8000
        ;;

    run)
        echo "▶️ Running daily workflow once..."
        run_daily_workflow
        ;;

    shell)
        echo "🐚 Starting shell..."
        exec /bin/bash
        ;;

    *)
        echo "Usage: $0 {web|run|shell}"
        echo "  web   - Start web server with scheduler (default)"
        echo "  run   - Run daily workflow once and exit"
        echo "  shell - Start interactive shell"
        exit 1
        ;;
esac
