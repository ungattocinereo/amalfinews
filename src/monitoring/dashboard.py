"""
Terminal dashboard using Rich library
"""

import logging
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel

from src.core.database import get_database
from src.monitoring.metrics import get_system_metrics


logger = logging.getLogger(__name__)
console = Console()


def create_status_table() -> Table:
    """Create status table"""
    table = Table(title="Amalfi Events - System Status", show_header=True)

    table.add_column("Metric", style="cyan", width=25)
    table.add_column("Value", style="green", width=15)
    table.add_column("Status", style="yellow", width=10)

    db = get_database()
    stats = db.get_daily_stats()

    table.add_row("Events Scraped", str(stats['scraped']), "✅")
    table.add_row("Events Translated", str(stats['translated']), "✅")
    table.add_row("Pending Review", str(stats['pending']), "⏳")
    table.add_row("Published", str(stats['published']), "✅")

    # System metrics
    metrics = get_system_metrics()
    table.add_row("CPU Usage", f"{metrics.cpu_percent:.1f}%", "✅")
    table.add_row("Memory", f"{metrics.memory_percent:.1f}%", "✅")
    table.add_row("DB Size", f"{metrics.database_size_mb:.1f} MB", "✅")

    return table


def display_status():
    """Display current status"""
    table = create_status_table()
    console.print(table)


def display_daily_summary():
    """Display daily summary"""
    db = get_database()
    stats = db.get_daily_stats()

    panel = Panel(
        f"""[bold]Daily Summary[/bold]

📥 Scraped: {stats['scraped']}
🌍 Translated: {stats['translated']}
✅ Approved: {stats['approved']}
📝 Published: {stats['published']}
""",
        title="Statistics",
        border_style="green"
    )

    console.print(panel)
