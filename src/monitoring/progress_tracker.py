"""
Progress tracking for crawling operations
Provides real-time updates about what's being processed
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CrawlerProgress:
    """Tracks progress of crawler operations"""
    status: str = "idle"  # idle, running, error
    current_source: Optional[str] = None
    current_source_name: Optional[str] = None
    progress: int = 0
    total: int = 0
    articles_found: int = 0
    sources_completed: List[str] = field(default_factory=list)
    sources_failed: List[Dict] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ProgressTracker:
    """Global progress tracker singleton"""

    _instance = None
    _progress: CrawlerProgress = CrawlerProgress()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def start_operation(self, total_sources: int):
        """Start a new crawling operation"""
        self._progress = CrawlerProgress(
            status="running",
            total=total_sources,
            progress=0,
            articles_found=0,
            started_at=datetime.now(),
            updated_at=datetime.now()
        )
        logger.info(f"Started crawling operation with {total_sources} sources")

    def update_source(self, source_id: str, source_name: str):
        """Update current source being processed"""
        self._progress.current_source = source_id
        self._progress.current_source_name = source_name
        self._progress.updated_at = datetime.now()
        logger.info(f"Processing source: {source_name} ({source_id})")

    def complete_source(self, source_id: str, articles_count: int, success: bool = True, error: Optional[str] = None):
        """Mark a source as completed"""
        self._progress.progress += 1
        self._progress.articles_found += articles_count
        self._progress.updated_at = datetime.now()

        if success:
            self._progress.sources_completed.append(source_id)
            logger.info(f"Completed source {source_id}: {articles_count} articles found")
        else:
            self._progress.sources_failed.append({
                "source_id": source_id,
                "error": error or "Unknown error"
            })
            if error:
                self._progress.errors.append(f"{source_id}: {error}")
            logger.error(f"Failed source {source_id}: {error}")

    def finish_operation(self):
        """Mark operation as finished"""
        self._progress.status = "idle"
        self._progress.current_source = None
        self._progress.current_source_name = None
        self._progress.updated_at = datetime.now()

        duration = (datetime.now() - self._progress.started_at).total_seconds() if self._progress.started_at else 0
        logger.info(
            f"Crawling operation finished: {self._progress.progress}/{self._progress.total} sources, "
            f"{self._progress.articles_found} articles found, "
            f"{len(self._progress.sources_failed)} failures, "
            f"Duration: {duration:.1f}s"
        )

    def add_error(self, error_msg: str):
        """Add an error message"""
        self._progress.errors.append(error_msg)
        self._progress.updated_at = datetime.now()
        # Keep only last 10 errors
        if len(self._progress.errors) > 10:
            self._progress.errors = self._progress.errors[-10:]

    def get_progress(self) -> CrawlerProgress:
        """Get current progress"""
        return self._progress

    def get_progress_dict(self) -> Dict:
        """Get progress as dictionary for API responses"""
        return {
            "status": self._progress.status,
            "current_source": self._progress.current_source,
            "current_source_name": self._progress.current_source_name,
            "progress": {
                "current": self._progress.progress,
                "total": self._progress.total,
                "percentage": (self._progress.progress / self._progress.total * 100) if self._progress.total > 0 else 0
            },
            "articles_found": self._progress.articles_found,
            "sources_completed": len(self._progress.sources_completed),
            "sources_failed": len(self._progress.sources_failed),
            "failures": self._progress.sources_failed[-5:],  # Last 5 failures
            "errors": self._progress.errors[-5:],  # Last 5 errors
            "started_at": self._progress.started_at.isoformat() if self._progress.started_at else None,
            "updated_at": self._progress.updated_at.isoformat() if self._progress.updated_at else None
        }


# Global instance
progress_tracker = ProgressTracker()
