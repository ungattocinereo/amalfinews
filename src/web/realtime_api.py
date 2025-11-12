"""
Real-time API with Server-Sent Events for live monitoring
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from sse_starlette.sse import EventSourceResponse

from src.core.database import get_database
from src.core.config import get_config, get_enabled_sources
from src.crawlers.health_check import HealthChecker
from src.monitoring.metrics import get_system_metrics
from src.monitoring.progress_tracker import progress_tracker

logger = logging.getLogger(__name__)


def get_current_stats():
    """Get current system statistics"""
    try:
        config = get_config()
        db = get_database(config.database_path)
        metrics = get_system_metrics(config.database_path, config.log_path)
        stats = db.get_daily_stats()

        # Get progress from tracker
        progress_data = progress_tracker.get_progress_dict()

        return {
            "timestamp": datetime.now().isoformat(),
            "status": progress_data["status"],
            "current_source": progress_data.get("current_source_name") or progress_data.get("current_source"),
            "progress": progress_data["progress"],
            "articles_found": progress_data["articles_found"],
            "sources_completed": progress_data["sources_completed"],
            "sources_failed": progress_data["sources_failed"],
            "daily_stats": {
                "scraped": stats.get("scraped", 0),
                "translated": stats.get("translated", 0),
                "approved": stats.get("approved", 0),
                "published": stats.get("published", 0),
                "pending": stats.get("pending", 0)
            },
            "system": {
                "cpu_percent": round(metrics.cpu_percent, 1),
                "memory_percent": round(metrics.memory_percent, 1),
                "memory_mb": round(metrics.memory_mb, 1),
                "database_size_mb": round(metrics.database_size_mb, 2),
                "log_size_mb": round(metrics.log_size_mb, 2)
            },
            "errors": progress_data.get("errors", [])
        }
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        return {"error": str(e), "timestamp": datetime.now().isoformat()}


async def event_stream() -> AsyncGenerator[str, None]:
    """Stream server-sent events with system stats"""
    while True:
        try:
            stats = get_current_stats()
            yield {
                "event": "stats",
                "data": json.dumps(stats)
            }
            await asyncio.sleep(1)  # Update every second
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in event stream: {e}")
            await asyncio.sleep(5)


def create_realtime_dashboard() -> str:
    """Create HTML dashboard with real-time updates"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Amalfi Events - Real-Time Dashboard</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }

            .container {
                max-width: 1400px;
                margin: 0 auto;
            }

            .header {
                background: rgba(255, 255, 255, 0.95);
                padding: 30px;
                border-radius: 15px;
                margin-bottom: 20px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }

            .header h1 {
                color: #667eea;
                font-size: 2.5em;
                margin-bottom: 10px;
            }

            .header .subtitle {
                color: #666;
                font-size: 1.1em;
            }

            .status-badge {
                display: inline-block;
                padding: 8px 16px;
                border-radius: 20px;
                font-weight: bold;
                font-size: 0.9em;
                margin-top: 15px;
            }

            .status-idle {
                background: #e5e7eb;
                color: #6b7280;
            }

            .status-running {
                background: #10b981;
                color: white;
                animation: pulse 2s ease-in-out infinite;
            }

            .status-error {
                background: #ef4444;
                color: white;
            }

            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.7; }
            }

            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 20px;
            }

            .card {
                background: rgba(255, 255, 255, 0.95);
                padding: 25px;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                transition: transform 0.3s ease;
            }

            .card:hover {
                transform: translateY(-5px);
            }

            .card-title {
                font-size: 0.9em;
                color: #666;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 10px;
            }

            .card-value {
                font-size: 2.5em;
                font-weight: bold;
                color: #667eea;
                margin-bottom: 5px;
            }

            .card-subtitle {
                font-size: 0.9em;
                color: #999;
            }

            .progress-bar {
                width: 100%;
                height: 30px;
                background: #e5e7eb;
                border-radius: 15px;
                overflow: hidden;
                margin: 15px 0;
                position: relative;
            }

            .progress-fill {
                height: 100%;
                background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                transition: width 0.5s ease;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: bold;
                font-size: 0.9em;
            }

            .progress-text {
                position: absolute;
                width: 100%;
                text-align: center;
                line-height: 30px;
                font-weight: bold;
                color: #333;
                mix-blend-mode: difference;
            }

            .metric-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 15px;
                margin-top: 15px;
            }

            .metric-item {
                background: #f9fafb;
                padding: 15px;
                border-radius: 10px;
                border-left: 4px solid #667eea;
            }

            .metric-label {
                font-size: 0.85em;
                color: #666;
                margin-bottom: 5px;
            }

            .metric-value {
                font-size: 1.5em;
                font-weight: bold;
                color: #333;
            }

            .sources-list {
                max-height: 300px;
                overflow-y: auto;
            }

            .source-item {
                background: #f9fafb;
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 10px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-left: 4px solid #667eea;
            }

            .source-item.active {
                background: #dbeafe;
                border-left-color: #10b981;
                animation: highlight 2s ease-in-out infinite;
            }

            @keyframes highlight {
                0%, 100% { background: #dbeafe; }
                50% { background: #bfdbfe; }
            }

            .source-name {
                font-weight: 600;
                color: #333;
            }

            .source-status {
                padding: 5px 12px;
                border-radius: 12px;
                font-size: 0.85em;
                font-weight: bold;
            }

            .source-status.pending {
                background: #e5e7eb;
                color: #6b7280;
            }

            .source-status.processing {
                background: #fef3c7;
                color: #d97706;
            }

            .source-status.done {
                background: #d1fae5;
                color: #059669;
            }

            .error-log {
                background: #fee2e2;
                border: 1px solid #fecaca;
                border-radius: 10px;
                padding: 15px;
                margin-top: 15px;
                max-height: 200px;
                overflow-y: auto;
            }

            .error-item {
                padding: 8px;
                margin-bottom: 8px;
                background: white;
                border-radius: 5px;
                font-size: 0.9em;
                color: #991b1b;
            }

            .timestamp {
                color: #999;
                font-size: 0.85em;
                margin-top: 10px;
            }

            .icon {
                font-size: 1.2em;
                margin-right: 8px;
            }

            ::-webkit-scrollbar {
                width: 8px;
            }

            ::-webkit-scrollbar-track {
                background: #f1f1f1;
                border-radius: 10px;
            }

            ::-webkit-scrollbar-thumb {
                background: #667eea;
                border-radius: 10px;
            }

            ::-webkit-scrollbar-thumb:hover {
                background: #764ba2;
            }

            .control-btn {
                width: 100%;
                padding: 15px 20px;
                margin-bottom: 10px;
                border: none;
                border-radius: 10px;
                font-size: 1em;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
            }

            .control-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            }

            .control-btn:active {
                transform: translateY(0);
            }

            .control-btn-primary {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }

            .control-btn-secondary {
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                color: white;
            }

            .control-btn-warning {
                background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
                color: white;
            }

            .control-btn-danger {
                background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
                color: white;
            }

            .control-btn:disabled {
                opacity: 0.5;
                cursor: not-allowed;
                transform: none !important;
            }

            .btn-icon {
                font-size: 1.2em;
            }

            .status-message {
                padding: 12px;
                border-radius: 8px;
                font-weight: 500;
                animation: fadeIn 0.3s ease;
            }

            .status-success {
                background: #d1fae5;
                color: #065f46;
                border: 1px solid #10b981;
            }

            .status-error {
                background: #fee2e2;
                color: #991b1b;
                border: 1px solid #ef4444;
            }

            .status-warning {
                background: #fef3c7;
                color: #92400e;
                border: 1px solid #f59e0b;
            }

            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(-10px); }
                to { opacity: 1; transform: translateY(0); }
            }

            /* Modal styles */
            .modal {
                display: none;
                position: fixed;
                z-index: 1000;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0,0,0,0.7);
                animation: fadeIn 0.3s ease;
            }

            .modal-content {
                background: white;
                margin: 50px auto;
                padding: 0;
                border-radius: 15px;
                width: 90%;
                max-width: 900px;
                max-height: 85vh;
                display: flex;
                flex-direction: column;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }

            .modal-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 25px 30px;
                border-radius: 15px 15px 0 0;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .modal-header h2 {
                margin: 0;
                font-size: 1.5em;
            }

            .close-modal {
                color: white;
                font-size: 35px;
                font-weight: bold;
                cursor: pointer;
                line-height: 1;
                transition: transform 0.2s;
            }

            .close-modal:hover {
                transform: scale(1.2);
            }

            .modal-body {
                padding: 20px 30px;
                overflow-y: auto;
                flex: 1;
            }

            .event-item {
                background: #f9fafb;
                border-left: 4px solid #667eea;
                padding: 20px;
                margin-bottom: 15px;
                border-radius: 8px;
                transition: all 0.3s ease;
            }

            .event-item:hover {
                background: #f3f4f6;
                transform: translateX(5px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }

            .event-title {
                font-size: 1.2em;
                font-weight: 600;
                color: #667eea;
                margin-bottom: 10px;
            }

            .event-title-it {
                font-size: 0.95em;
                color: #666;
                font-style: italic;
                margin-bottom: 10px;
            }

            .event-description {
                color: #444;
                line-height: 1.6;
                margin-bottom: 15px;
            }

            .event-meta {
                display: flex;
                gap: 20px;
                flex-wrap: wrap;
                font-size: 0.9em;
                color: #666;
            }

            .event-meta-item {
                display: flex;
                align-items: center;
                gap: 5px;
            }

            .event-link {
                color: #667eea;
                text-decoration: none;
                font-weight: 500;
            }

            .event-link:hover {
                text-decoration: underline;
            }

            .clickable-card {
                cursor: pointer;
                transition: all 0.3s ease;
            }

            .clickable-card:hover {
                transform: translateY(-8px) scale(1.02);
                box-shadow: 0 15px 40px rgba(0,0,0,0.3);
            }

            .no-events {
                text-align: center;
                padding: 40px;
                color: #999;
                font-size: 1.1em;
            }

            .loading {
                text-align: center;
                padding: 40px;
                color: #667eea;
            }

            .spinner-small {
                border: 3px solid rgba(102, 126, 234, 0.3);
                border-radius: 50%;
                border-top: 3px solid #667eea;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎯 Amalfi Events Intelligence</h1>
                <p class="subtitle">Real-Time Monitoring Dashboard</p>
                <span id="status-badge" class="status-badge status-idle">● IDLE</span>
                <div class="timestamp">Last update: <span id="last-update">--</span></div>
            </div>

            <div class="grid">
                <div class="card">
                    <div class="card-title">📥 Articles Scraped Today</div>
                    <div class="card-value" id="scraped-count">0</div>
                    <div class="card-subtitle">From all sources</div>
                </div>

                <div class="card clickable-card" onclick="openTranslatedModal()" title="Click to view translated events">
                    <div class="card-title">🌍 Translated</div>
                    <div class="card-value" id="translated-count">0</div>
                    <div class="card-subtitle">Click to view details</div>
                </div>

                <div class="card clickable-card" onclick="openApprovedModal()" title="Click to view approved events">
                    <div class="card-title">✅ Approved</div>
                    <div class="card-value" id="approved-count">0</div>
                    <div class="card-subtitle">Click to view details</div>
                </div>

                <div class="card">
                    <div class="card-title">⏳ Pending Review</div>
                    <div class="card-value" id="pending-count">0</div>
                    <div class="card-subtitle">Awaiting moderation</div>
                </div>
            </div>

            <div class="grid">
                <div class="card">
                    <div class="card-title">🔄 Current Operation</div>
                    <div id="current-source" style="font-size: 1.3em; color: #667eea; font-weight: 600; margin: 15px 0;">
                        Waiting for next run...
                    </div>

                    <div class="progress-bar">
                        <div class="progress-fill" id="progress-fill" style="width: 0%"></div>
                        <div class="progress-text" id="progress-text">0%</div>
                    </div>

                    <div class="metric-grid">
                        <div class="metric-item">
                            <div class="metric-label">Articles Found</div>
                            <div class="metric-value" id="articles-found">0</div>
                        </div>
                        <div class="metric-item">
                            <div class="metric-label">Progress</div>
                            <div class="metric-value" id="progress-fraction">0/0</div>
                        </div>
                    </div>
                </div>

                <div class="card">
                    <div class="card-title">💻 System Resources</div>

                    <div class="metric-grid">
                        <div class="metric-item">
                            <div class="metric-label">CPU Usage</div>
                            <div class="metric-value" id="cpu-usage">0%</div>
                        </div>
                        <div class="metric-item">
                            <div class="metric-label">Memory</div>
                            <div class="metric-value" id="memory-usage">0%</div>
                        </div>
                        <div class="metric-item">
                            <div class="metric-label">Database Size</div>
                            <div class="metric-value" id="db-size">0 MB</div>
                        </div>
                        <div class="metric-item">
                            <div class="metric-label">Logs Size</div>
                            <div class="metric-value" id="log-size">0 MB</div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="grid">
                <div class="card">
                    <div class="card-title">🎮 Control Panel</div>
                    <div style="margin-top: 15px;">
                        <button class="control-btn control-btn-primary" onclick="triggerManualRun()">
                            <span class="btn-icon">▶️</span>
                            <span>Run Crawling Now</span>
                        </button>
                        <button class="control-btn control-btn-secondary" onclick="checkSourcesHealth()">
                            <span class="btn-icon">🔍</span>
                            <span>Check Sources Health</span>
                        </button>
                        <button class="control-btn control-btn-warning" onclick="clearPendingEvents()">
                            <span class="btn-icon">🗑️</span>
                            <span>Clear Pending Events</span>
                        </button>
                        <button class="control-btn control-btn-danger" onclick="clearDatabase()">
                            <span class="btn-icon">⚠️</span>
                            <span>Clear All Database</span>
                        </button>
                    </div>
                    <div id="control-status" style="margin-top: 15px; padding: 10px; border-radius: 8px; display: none;"></div>
                </div>

                <div class="card">
                    <div class="card-title">⚠️ Recent Errors</div>
                    <div id="errors-container">
                        <div style="text-align: center; color: #999; padding: 20px;">
                            No errors
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Translated Events Modal -->
        <div id="translatedModal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>🌍 Translated Events</h2>
                    <span class="close-modal" onclick="closeModal('translatedModal')">&times;</span>
                </div>
                <div class="modal-body" id="translatedModalBody">
                    <div class="loading">
                        <div class="spinner-small"></div>
                        <div>Loading translated events...</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Approved Events Modal -->
        <div id="approvedModal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>✅ Approved Events</h2>
                    <span class="close-modal" onclick="closeModal('approvedModal')">&times;</span>
                </div>
                <div class="modal-body" id="approvedModalBody">
                    <div class="loading">
                        <div class="spinner-small"></div>
                        <div>Loading approved events...</div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            var eventSource = new EventSource('/api/realtime/stream');

            eventSource.addEventListener('stats', function(event) {
                try {
                    var data = JSON.parse(event.data);
                    updateDashboard(data);
                } catch (e) {
                    console.error('Failed to parse event data:', e);
                }
            });

            eventSource.onerror = function(error) {
                console.error('EventSource error:', error);
                setTimeout(function() {
                    location.reload();
                }, 5000);
            };

            function updateDashboard(data) {
                // Update timestamp
                document.getElementById('last-update').textContent = new Date().toLocaleTimeString();

                // Update status badge
                var statusBadge = document.getElementById('status-badge');
                statusBadge.className = 'status-badge status-' + data.status;
                statusBadge.textContent = '● ' + data.status.toUpperCase();

                // Update daily stats
                if (data.daily_stats) {
                    document.getElementById('scraped-count').textContent = data.daily_stats.scraped || 0;
                    document.getElementById('translated-count').textContent = data.daily_stats.translated || 0;
                    document.getElementById('approved-count').textContent = data.daily_stats.approved || 0;
                    document.getElementById('pending-count').textContent = data.daily_stats.pending || 0;
                }

                // Update current operation
                if (data.current_source) {
                    document.getElementById('current-source').textContent = '📡 ' + data.current_source;
                } else {
                    document.getElementById('current-source').textContent = 'Waiting for next run...';
                }

                // Update progress
                if (data.progress) {
                    var percentage = Math.round(data.progress.percentage);
                    document.getElementById('progress-fill').style.width = percentage + '%';
                    document.getElementById('progress-text').textContent = percentage + '%';
                    document.getElementById('progress-fraction').textContent =
                        data.progress.current + '/' + data.progress.total;
                }

                document.getElementById('articles-found').textContent = data.articles_found || 0;

                // Update system metrics
                if (data.system) {
                    document.getElementById('cpu-usage').textContent = data.system.cpu_percent + '%';
                    document.getElementById('memory-usage').textContent = data.system.memory_percent + '%';
                    document.getElementById('db-size').textContent = data.system.database_size_mb + ' MB';
                    document.getElementById('log-size').textContent = data.system.log_size_mb + ' MB';
                }

                // Update errors
                if (data.errors && data.errors.length > 0) {
                    var errorsHtml = data.errors.map(function(err) {
                        return '<div class="error-item">⚠️ ' + err + '</div>';
                    }).join('');
                    document.getElementById('errors-container').innerHTML =
                        '<div class="error-log">' + errorsHtml + '</div>';
                } else {
                    document.getElementById('errors-container').innerHTML =
                        '<div style="text-align: center; color: #999; padding: 20px;">No errors</div>';
                }
            }

            // Control panel functions
            function showStatus(message, type) {
                var statusDiv = document.getElementById('control-status');
                statusDiv.className = 'status-message status-' + type;
                statusDiv.textContent = message;
                statusDiv.style.display = 'block';

                setTimeout(function() {
                    statusDiv.style.display = 'none';
                }, 5000);
            }

            function disableButtons(disabled) {
                var buttons = document.querySelectorAll('.control-btn');
                buttons.forEach(function(btn) {
                    btn.disabled = disabled;
                });
            }

            function triggerManualRun() {
                if (!confirm('Start manual crawling of all sources?')) return;

                disableButtons(true);
                showStatus('⏳ Starting crawling operation...', 'warning');

                fetch('/run', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({dry_run: false})
                })
                .then(function(response) {
                    return response.json().then(function(data) {
                        return {response: response, data: data};
                    });
                })
                .then(function(result) {
                    if (result.response.ok) {
                        showStatus('✅ Crawling started! Watch progress above.', 'success');
                    } else {
                        showStatus('❌ Error: ' + (result.data.detail || 'Failed to start'), 'error');
                    }
                    setTimeout(function() { disableButtons(false); }, 2000);
                })
                .catch(function(error) {
                    showStatus('❌ Error: ' + error.message, 'error');
                    setTimeout(function() { disableButtons(false); }, 2000);
                });
            }

            function checkSourcesHealth() {
                disableButtons(true);
                showStatus('⏳ Checking sources health...', 'warning');

                fetch('/sources/health')
                .then(function(response) {
                    return response.json().then(function(data) {
                        return {response: response, data: data};
                    });
                })
                .then(function(result) {
                    if (result.response.ok) {
                        showStatus('✅ Health check complete: ' + result.data.healthy + '/' + result.data.total + ' sources healthy', 'success');
                    } else {
                        showStatus('❌ Health check failed', 'error');
                    }
                    setTimeout(function() { disableButtons(false); }, 1000);
                })
                .catch(function(error) {
                    showStatus('❌ Error: ' + error.message, 'error');
                    setTimeout(function() { disableButtons(false); }, 1000);
                });
            }

            function clearPendingEvents() {
                if (!confirm('Clear all pending events? This cannot be undone!')) return;

                disableButtons(true);
                showStatus('⏳ Clearing pending events...', 'warning');

                fetch('/api/database/clear-pending', {
                    method: 'POST'
                })
                .then(function(response) {
                    return response.json().then(function(data) {
                        return {response: response, data: data};
                    });
                })
                .then(function(result) {
                    if (result.response.ok) {
                        showStatus('✅ Cleared ' + result.data.deleted + ' pending events', 'success');
                    } else {
                        showStatus('❌ Error: ' + (result.data.detail || 'Failed to clear'), 'error');
                    }
                    setTimeout(function() { disableButtons(false); }, 1000);
                })
                .catch(function(error) {
                    showStatus('❌ Error: ' + error.message, 'error');
                    setTimeout(function() { disableButtons(false); }, 1000);
                });
            }

            function clearDatabase() {
                if (!confirm('⚠️ WARNING: This will DELETE ALL DATA in the database!\\n\\nAre you absolutely sure?')) return;
                if (!confirm('This is your LAST WARNING. All events will be permanently deleted. Continue?')) return;

                disableButtons(true);
                showStatus('⏳ Clearing entire database...', 'warning');

                fetch('/api/database/clear-all', {
                    method: 'POST'
                })
                .then(function(response) {
                    return response.json().then(function(data) {
                        return {response: response, data: data};
                    });
                })
                .then(function(result) {
                    if (result.response.ok) {
                        showStatus('✅ Database cleared: ' + result.data.deleted_raw + ' raw + ' + result.data.deleted_processed + ' processed events', 'success');
                    } else {
                        showStatus('❌ Error: ' + (result.data.detail || 'Failed to clear'), 'error');
                    }
                    setTimeout(function() { disableButtons(false); }, 1000);
                })
                .catch(function(error) {
                    showStatus('❌ Error: ' + error.message, 'error');
                    setTimeout(function() { disableButtons(false); }, 1000);
                });
            }

            // Modal functions
            function openModal(modalId) {
                document.getElementById(modalId).style.display = 'block';
            }

            function closeModal(modalId) {
                document.getElementById(modalId).style.display = 'none';
            }

            function formatDate(dateStr) {
                if (!dateStr) return 'N/A';
                var date = new Date(dateStr);
                return date.toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric'
                });
            }

            function renderEvent(event) {
                var html = '<div class="event-item">';
                html += '<div class="event-title">' + (event.title_en || 'Untitled') + '</div>';
                if (event.title_it) {
                    html += '<div class="event-title-it">' + event.title_it + '</div>';
                }
                if (event.description) {
                    html += '<div class="event-description">' + event.description + '</div>';
                }
                html += '<div class="event-meta">';
                if (event.event_date) {
                    html += '<div class="event-meta-item">📅 ' + formatDate(event.event_date) + '</div>';
                }
                if (event.location) {
                    html += '<div class="event-meta-item">📍 ' + event.location + '</div>';
                }
                if (event.category) {
                    html += '<div class="event-meta-item">🏷️ ' + event.category + '</div>';
                }
                if (event.source_url) {
                    html += '<div class="event-meta-item"><a href="' + event.source_url + '" target="_blank" class="event-link">🔗 Source</a></div>';
                }
                html += '</div>';
                html += '</div>';
                return html;
            }

            function openTranslatedModal() {
                openModal('translatedModal');

                var bodyDiv = document.getElementById('translatedModalBody');
                bodyDiv.innerHTML = '<div class="loading"><div class="spinner-small"></div><div>Loading translated events...</div></div>';

                fetch('/api/events/translated?limit=50')
                .then(function(response) {
                    return response.json();
                })
                .then(function(data) {
                    if (data.events && data.events.length > 0) {
                        var html = '';
                        data.events.forEach(function(event) {
                            html += renderEvent(event);
                        });
                        bodyDiv.innerHTML = html;
                    } else {
                        bodyDiv.innerHTML = '<div class="no-events">No translated events found</div>';
                    }
                })
                .catch(function(error) {
                    bodyDiv.innerHTML = '<div class="no-events">Error loading events: ' + error.message + '</div>';
                });
            }

            function openApprovedModal() {
                openModal('approvedModal');

                var bodyDiv = document.getElementById('approvedModalBody');
                bodyDiv.innerHTML = '<div class="loading"><div class="spinner-small"></div><div>Loading approved events...</div></div>';

                fetch('/api/events/approved?limit=50')
                .then(function(response) {
                    return response.json();
                })
                .then(function(data) {
                    if (data.events && data.events.length > 0) {
                        var html = '';
                        data.events.forEach(function(event) {
                            html += renderEvent(event);
                        });
                        bodyDiv.innerHTML = html;
                    } else {
                        bodyDiv.innerHTML = '<div class="no-events">No approved events found</div>';
                    }
                })
                .catch(function(error) {
                    bodyDiv.innerHTML = '<div class="no-events">Error loading events: ' + error.message + '</div>';
                });
            }

            // Close modal when clicking outside
            window.onclick = function(event) {
                if (event.target.className === 'modal') {
                    event.target.style.display = 'none';
                }
            }
        </script>
    </body>
    </html>
    """


# FastAPI routes
async def setup_realtime_routes(app: FastAPI):
    """Setup real-time monitoring routes"""

    @app.get("/dashboard", response_class=HTMLResponse)
    async def get_dashboard():
        """Get real-time dashboard"""
        return create_realtime_dashboard()

    @app.get("/api/realtime/stream")
    async def stream_stats():
        """Stream real-time statistics via SSE"""
        return EventSourceResponse(event_stream())

    @app.get("/api/realtime/stats")
    async def get_realtime_stats():
        """Get current statistics (REST endpoint)"""
        return get_current_stats()
