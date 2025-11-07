"""
Database manager for Amalfi Events Intelligence System
SQLite database operations
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from contextlib import contextmanager

from src.core.models import RawEvent, ProcessedEvent, EventStatus, raw_event_from_dict, processed_event_from_dict


logger = logging.getLogger(__name__)


class Database:
    """SQLite database manager"""

    def __init__(self, db_path: str = "./data/events.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def get_connection(self):
        """Context manager for database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Access columns by name
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def initialize(self):
        """Create tables and indices"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Create raw_events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS raw_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    event_date DATE,
                    image_url TEXT,
                    source_url TEXT UNIQUE NOT NULL,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed BOOLEAN DEFAULT 0,
                    processing_notes TEXT
                )
            """)

            # Create processed_events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processed_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_id INTEGER NOT NULL,
                    title_en TEXT NOT NULL,
                    description_en TEXT NOT NULL,
                    event_date DATE NOT NULL,
                    event_time TEXT,
                    location TEXT,
                    price_info TEXT,
                    accessibility TEXT,
                    category TEXT DEFAULT 'other',
                    image_url TEXT,
                    keywords TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    moderated_at TIMESTAMP,
                    moderated_by TEXT,
                    published_at TIMESTAMP,
                    wordpress_post_id INTEGER,
                    FOREIGN KEY (original_id) REFERENCES raw_events(id)
                )
            """)

            # Create indices
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_raw_source ON raw_events(source)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_raw_processed ON raw_events(processed)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_raw_scraped_at ON raw_events(scraped_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_processed_status ON processed_events(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_processed_event_date ON processed_events(event_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_processed_created_at ON processed_events(created_at)")

            logger.info("Database initialized successfully")

    # ===== RAW EVENTS =====

    def insert_raw_event(self, event: RawEvent) -> int:
        """Insert raw event, return ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR IGNORE INTO raw_events
                (source, title, content, event_date, image_url, source_url, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                event.source,
                event.title,
                event.content,
                event.event_date,
                event.image_url,
                event.source_url,
                event.scraped_at
            ))

            return cursor.lastrowid

    def get_raw_event(self, event_id: int) -> Optional[RawEvent]:
        """Get raw event by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM raw_events WHERE id = ?", (event_id,))
            row = cursor.fetchone()

            if row:
                return raw_event_from_dict(dict(row))
            return None

    def get_unprocessed_raw_events(self, limit: int = 100) -> List[RawEvent]:
        """Get unprocessed raw events"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM raw_events
                WHERE processed = 0
                ORDER BY scraped_at DESC
                LIMIT ?
            """, (limit,))

            return [raw_event_from_dict(dict(row)) for row in cursor.fetchall()]

    def get_raw_events_by_source(self, source: str, days: int = 7) -> List[RawEvent]:
        """Get recent raw events from specific source"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cutoff = datetime.now() - timedelta(days=days)

            cursor.execute("""
                SELECT * FROM raw_events
                WHERE source = ? AND scraped_at > ?
                ORDER BY scraped_at DESC
            """, (source, cutoff))

            return [raw_event_from_dict(dict(row)) for row in cursor.fetchall()]

    def mark_raw_event_processed(self, event_id: int, notes: str = ""):
        """Mark raw event as processed"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE raw_events
                SET processed = 1, processing_notes = ?
                WHERE id = ?
            """, (notes, event_id))

    def get_raw_events_count(self, source: Optional[str] = None, days: int = 1) -> int:
        """Get count of raw events"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cutoff = datetime.now() - timedelta(days=days)

            if source:
                cursor.execute("""
                    SELECT COUNT(*) FROM raw_events
                    WHERE source = ? AND scraped_at > ?
                """, (source, cutoff))
            else:
                cursor.execute("""
                    SELECT COUNT(*) FROM raw_events
                    WHERE scraped_at > ?
                """, (cutoff,))

            return cursor.fetchone()[0]

    # ===== PROCESSED EVENTS =====

    def insert_processed_event(self, event: ProcessedEvent) -> int:
        """Insert processed event, return ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            keywords_str = ",".join(event.keywords) if event.keywords else ""

            cursor.execute("""
                INSERT INTO processed_events
                (original_id, title_en, description_en, event_date, event_time,
                 location, price_info, accessibility, category, image_url,
                 keywords, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.original_id,
                event.title_en,
                event.description_en,
                event.event_date,
                event.event_time,
                event.location,
                event.price_info,
                event.accessibility,
                event.category.value,
                event.image_url,
                keywords_str,
                event.status.value,
                event.created_at
            ))

            return cursor.lastrowid

    def get_processed_event(self, event_id: int) -> Optional[ProcessedEvent]:
        """Get processed event by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM processed_events WHERE id = ?", (event_id,))
            row = cursor.fetchone()

            if row:
                data = dict(row)
                if data.get('keywords'):
                    data['keywords'] = data['keywords'].split(',')
                return processed_event_from_dict(data)
            return None

    def get_events_by_status(self, status: EventStatus, limit: int = 100) -> List[ProcessedEvent]:
        """Get events by status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM processed_events
                WHERE status = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (status.value, limit))

            events = []
            for row in cursor.fetchall():
                data = dict(row)
                if data.get('keywords'):
                    data['keywords'] = data['keywords'].split(',')
                events.append(processed_event_from_dict(data))

            return events

    def update_event_status(self, event_id: int, status: EventStatus,
                          moderated_by: Optional[str] = None):
        """Update event status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            if status in [EventStatus.APPROVED, EventStatus.REJECTED]:
                cursor.execute("""
                    UPDATE processed_events
                    SET status = ?, moderated_at = ?, moderated_by = ?
                    WHERE id = ?
                """, (status.value, datetime.now(), moderated_by, event_id))
            else:
                cursor.execute("""
                    UPDATE processed_events
                    SET status = ?
                    WHERE id = ?
                """, (status.value, event_id))

    def mark_event_published(self, event_id: int, wordpress_post_id: int):
        """Mark event as published with WordPress post ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE processed_events
                SET status = ?, published_at = ?, wordpress_post_id = ?
                WHERE id = ?
            """, (EventStatus.PUBLISHED.value, datetime.now(), wordpress_post_id, event_id))

    def get_pending_events(self, limit: int = 10) -> List[ProcessedEvent]:
        """Get pending events for moderation"""
        return self.get_events_by_status(EventStatus.PENDING, limit)

    def get_approved_unpublished_events(self) -> List[ProcessedEvent]:
        """Get approved but unpublished events"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM processed_events
                WHERE status = ? AND wordpress_post_id IS NULL
                ORDER BY event_date ASC
            """, (EventStatus.APPROVED.value,))

            events = []
            for row in cursor.fetchall():
                data = dict(row)
                if data.get('keywords'):
                    data['keywords'] = data['keywords'].split(',')
                events.append(processed_event_from_dict(data))

            return events

    def get_upcoming_events(self, days: int = 30) -> List[ProcessedEvent]:
        """Get upcoming published events"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cutoff = datetime.now() + timedelta(days=days)

            cursor.execute("""
                SELECT * FROM processed_events
                WHERE status = ? AND event_date <= ?
                ORDER BY event_date ASC
            """, (EventStatus.PUBLISHED.value, cutoff))

            events = []
            for row in cursor.fetchall():
                data = dict(row)
                if data.get('keywords'):
                    data['keywords'] = data['keywords'].split(',')
                events.append(processed_event_from_dict(data))

            return events

    # ===== STATISTICS =====

    def get_daily_stats(self, date: Optional[datetime] = None) -> Dict:
        """Get statistics for a specific day"""
        if date is None:
            date = datetime.now()

        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = date.replace(hour=23, minute=59, second=59, microsecond=999999)

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Raw events scraped today
            cursor.execute("""
                SELECT COUNT(*) FROM raw_events
                WHERE scraped_at BETWEEN ? AND ?
            """, (start_of_day, end_of_day))
            scraped = cursor.fetchone()[0]

            # Processed events created today
            cursor.execute("""
                SELECT COUNT(*) FROM processed_events
                WHERE created_at BETWEEN ? AND ?
            """, (start_of_day, end_of_day))
            translated = cursor.fetchone()[0]

            # Events by status
            cursor.execute("""
                SELECT status, COUNT(*) FROM processed_events
                GROUP BY status
            """)
            status_counts = {row[0]: row[1] for row in cursor.fetchall()}

            return {
                'date': date,
                'scraped': scraped,
                'translated': translated,
                'pending': status_counts.get('pending', 0),
                'approved': status_counts.get('approved', 0),
                'rejected': status_counts.get('rejected', 0),
                'published': status_counts.get('published', 0)
            }

    def cleanup_old_events(self, days: int = 90):
        """Delete old events past their date"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cutoff = datetime.now() - timedelta(days=days)

            # Delete old processed events
            cursor.execute("""
                DELETE FROM processed_events
                WHERE event_date < ? AND status = ?
            """, (cutoff, EventStatus.PUBLISHED.value))

            deleted = cursor.rowcount
            logger.info(f"Deleted {deleted} old events")

            return deleted

    def get_database_size(self) -> float:
        """Get database size in MB"""
        if self.db_path.exists():
            return self.db_path.stat().st_size / (1024 * 1024)
        return 0.0


# Singleton instance
_db_instance: Optional[Database] = None


def get_database(db_path: str = "./data/events.db") -> Database:
    """Get singleton Database instance"""
    global _db_instance

    if _db_instance is None:
        _db_instance = Database(db_path)

    return _db_instance
