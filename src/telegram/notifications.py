"""
Telegram notifications and reports
"""

import logging
from datetime import datetime
from typing import List

from src.core.models import DailyStats, HealthStatus


logger = logging.getLogger(__name__)


def format_daily_report(stats: DailyStats, health_statuses: List[HealthStatus] = None) -> str:
    """Format daily statistics report"""

    report = f"""📊 *Daily Report - {datetime.now().strftime('%B %d, %Y')}*

🕷️ *Sources:* {stats.sources_healthy}/{stats.sources_checked} healthy
📥 *Events Scraped:* {stats.events_scraped}
🔍 *Passed Filter:* {stats.events_filtered} ({_percentage(stats.events_filtered, stats.events_scraped)}%)
🌍 *Translated:* {stats.events_translated}
⏳ *Pending Review:* {stats.events_pending}
✅ *Approved:* {stats.events_approved}
❌ *Rejected:* {stats.events_rejected}
📝 *Published:* {stats.events_published}

⏱️ *Processing Time:* {_format_duration(stats.processing_time_seconds)}

🤖 *DeepSeek API:*
  • Calls: {stats.deepseek_calls}
  • Tokens: {stats.deepseek_tokens:,}
  • Cost: ${stats.deepseek_cost:.3f}

"""

    if stats.errors:
        report += f"🚨 *Errors:* {len(stats.errors)}\n"
        for error in stats.errors[:3]:
            report += f"  • {error}\n"

    if health_statuses:
        unhealthy = [h for h in health_statuses if not h.healthy]
        if unhealthy:
            report += f"\n⚠️ *Unhealthy Sources:*\n"
            for h in unhealthy[:3]:
                report += f"  • {h.url}: {h.error}\n"

    return report


def format_error_alert(error: str, context: str = "") -> str:
    """Format error alert message"""
    return f"""🚨 *Error Alert*

*Error:* {error}

*Context:* {context}

*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""


def format_source_failure_alert(source_id: str, error: str) -> str:
    """Format source failure alert"""
    return f"""⚠️ *Source Failure*

*Source:* {source_id}
*Error:* {error}
*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Check source configuration and health.
"""


def _percentage(part: int, total: int) -> int:
    """Calculate percentage"""
    if total == 0:
        return 0
    return int((part / total) * 100)


def _format_duration(seconds: float) -> str:
    """Format duration in human-readable form"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} min"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} hours"
