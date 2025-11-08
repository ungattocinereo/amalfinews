"""
FastAPI web interface for monitoring and control
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from src.core.database import get_database
from src.core.config import get_config, get_enabled_sources
from src.crawlers.health_check import HealthChecker
from src.monitoring.metrics import get_system_metrics

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Amalfi Events Intelligence",
    description="Automated event collection system for Amalfi Coast tourism",
    version="4.0"
)

# Global state for background tasks
background_task_running = False


class StatusResponse(BaseModel):
    """System status response"""
    status: str
    uptime: str
    database_size_mb: float
    events_today: Dict
    system_metrics: Dict


class ManualRunRequest(BaseModel):
    """Manual run request"""
    dry_run: bool = False


@app.get("/")
async def root():
    """Root endpoint with HTML dashboard"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Amalfi Events Intelligence</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 10px;
                margin-bottom: 20px;
            }
            .card {
                background: white;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .status-ok { color: #10b981; font-weight: bold; }
            .status-error { color: #ef4444; font-weight: bold; }
            button {
                background-color: #667eea;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
            }
            button:hover {
                background-color: #764ba2;
            }
            .endpoint {
                background-color: #f0f0f0;
                padding: 10px;
                border-radius: 5px;
                margin: 10px 0;
                font-family: monospace;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎯 Amalfi Events Intelligence</h1>
            <p>Automated Event Collection System v4.0</p>
        </div>

        <div class="card">
            <h2>📊 System Status</h2>
            <p>Check system status: <span class="endpoint">GET /status</span></p>
            <button onclick="window.location.href='/status'">View Status</button>
        </div>

        <div class="card">
            <h2>📈 Statistics</h2>
            <p>Daily statistics: <span class="endpoint">GET /stats</span></p>
            <button onclick="window.location.href='/stats'">View Statistics</button>
        </div>

        <div class="card">
            <h2>🌐 Source Health</h2>
            <p>Check news sources: <span class="endpoint">GET /sources/health</span></p>
            <button onclick="window.location.href='/sources/health'">Check Sources</button>
        </div>

        <div class="card">
            <h2>📝 Events</h2>
            <p>Pending events: <span class="endpoint">GET /events/pending</span></p>
            <p>Recent events: <span class="endpoint">GET /events/recent</span></p>
            <button onclick="window.location.href='/events/pending'">View Pending</button>
            <button onclick="window.location.href='/events/recent'">View Recent</button>
        </div>

        <div class="card">
            <h2>▶️ Manual Control</h2>
            <p>Trigger manual run: <span class="endpoint">POST /run</span></p>
            <button onclick="triggerRun()">Run Now (Dry Run)</button>
        </div>

        <div class="card">
            <h2>📚 API Documentation</h2>
            <p><a href="/docs" target="_blank">Interactive API Docs (Swagger UI)</a></p>
            <p><a href="/redoc" target="_blank">ReDoc Documentation</a></p>
        </div>

        <script>
            function triggerRun() {
                if (confirm('Trigger a dry run of the daily workflow?')) {
                    fetch('/run', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({dry_run: true})
                    })
                    .then(response => response.json())
                    .then(data => alert('Run started: ' + data.message))
                    .catch(error => alert('Error: ' + error));
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get system status"""
    try:
        config = get_config()
        db = get_database(config.database_path)
        metrics = get_system_metrics(config.database_path, config.log_path)
        stats = db.get_daily_stats()

        return StatusResponse(
            status="running",
            uptime=datetime.now().isoformat(),
            database_size_mb=metrics.database_size_mb,
            events_today=stats,
            system_metrics={
                "cpu_percent": metrics.cpu_percent,
                "memory_percent": metrics.memory_percent,
                "memory_mb": metrics.memory_mb,
                "log_size_mb": metrics.log_size_mb
            }
        )
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_statistics():
    """Get daily statistics"""
    try:
        config = get_config()
        db = get_database(config.database_path)
        stats = db.get_daily_stats()
        return stats
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sources/health")
async def check_sources_health():
    """Check health of all news sources"""
    try:
        sources = get_enabled_sources()
        checker = HealthChecker(timeout=5)
        results = await checker.check_all_sources(sources)

        health_status = []
        for source, result in zip(sources, results):
            health_status.append({
                "id": source.id,
                "name": source.name,
                "url": source.url,
                "healthy": result.healthy,
                "response_time": result.response_time,
                "articles_found": result.articles_found,
                "error": result.error
            })

        healthy_count = sum(1 for h in health_status if h["healthy"])

        return {
            "total": len(sources),
            "healthy": healthy_count,
            "unhealthy": len(sources) - healthy_count,
            "sources": health_status
        }
    except Exception as e:
        logger.error(f"Source health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/events/pending")
async def get_pending_events():
    """Get pending events for moderation"""
    try:
        config = get_config()
        db = get_database(config.database_path)
        events = db.get_pending_events(limit=20)

        return {
            "count": len(events),
            "events": [
                {
                    "id": e.id,
                    "title": e.title_en,
                    "description": e.description_en[:200] + "..." if len(e.description_en) > 200 else e.description_en,
                    "date": e.event_date.isoformat(),
                    "location": e.location,
                    "category": e.category.value,
                    "created_at": e.created_at.isoformat()
                }
                for e in events
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get pending events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/events/recent")
async def get_recent_events():
    """Get recently processed events"""
    try:
        config = get_config()
        db = get_database(config.database_path)

        # Get all processed events from today
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM processed_events
                ORDER BY created_at DESC
                LIMIT 20
            """)
            rows = cursor.fetchall()

        events = []
        for row in rows:
            events.append({
                "id": row["id"],
                "title": row["title_en"],
                "date": row["event_date"],
                "location": row["location"],
                "status": row["status"],
                "created_at": row["created_at"]
            })

        return {"count": len(events), "events": events}

    except Exception as e:
        logger.error(f"Failed to get recent events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/run")
async def trigger_manual_run(request: ManualRunRequest, background_tasks: BackgroundTasks):
    """Trigger manual run of daily workflow"""
    global background_task_running

    if background_task_running:
        raise HTTPException(status_code=409, detail="A run is already in progress")

    logger.info(f"Manual run triggered (dry_run={request.dry_run})")

    # Import here to avoid circular imports
    from scripts.daily_run import main as daily_run_main

    async def run_workflow():
        global background_task_running
        background_task_running = True
        try:
            await daily_run_main()
        except Exception as e:
            logger.error(f"Manual run failed: {e}")
        finally:
            background_task_running = False

    background_tasks.add_task(run_workflow)

    return {
        "status": "started",
        "message": "Daily workflow started in background",
        "dry_run": request.dry_run,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/logs/recent")
async def get_recent_logs(lines: int = 50):
    """Get recent log entries"""
    try:
        log_file = "./logs/daily_run.log"

        try:
            with open(log_file, 'r') as f:
                all_lines = f.readlines()
                recent = all_lines[-lines:]
                return {
                    "total_lines": len(all_lines),
                    "returned_lines": len(recent),
                    "logs": [line.strip() for line in recent]
                }
        except FileNotFoundError:
            return {
                "total_lines": 0,
                "returned_lines": 0,
                "logs": []
            }

    except Exception as e:
        logger.error(f"Failed to read logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
