"""
System metrics collection
"""

import psutil
import logging
from pathlib import Path
from datetime import datetime

from src.core.models import SystemMetrics


logger = logging.getLogger(__name__)


def get_system_metrics(db_path: str = "./data/events.db",
                      log_path: str = "./logs") -> SystemMetrics:
    """Get current system metrics"""

    # CPU and memory
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    memory_mb = memory.used / (1024 * 1024)
    memory_percent = memory.percent

    # Database size
    db_size_mb = 0
    if Path(db_path).exists():
        db_size_mb = Path(db_path).stat().st_size / (1024 * 1024)

    # Log directory size
    log_size_mb = 0
    log_dir = Path(log_path)
    if log_dir.exists():
        log_size_mb = sum(f.stat().st_size for f in log_dir.glob('*.log')) / (1024 * 1024)

    return SystemMetrics(
        timestamp=datetime.now(),
        cpu_percent=cpu_percent,
        memory_mb=memory_mb,
        memory_percent=memory_percent,
        database_size_mb=db_size_mb,
        log_size_mb=log_size_mb
    )
