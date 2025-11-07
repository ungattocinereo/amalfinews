"""
Basic database tests
"""

import pytest
from datetime import datetime
from src.core.database import Database
from src.core.models import RawEvent, ProcessedEvent, EventStatus, EventCategory


def test_database_initialization(tmp_path):
    """Test database initialization"""
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))
    db.initialize()

    assert db_path.exists()
    assert db.get_database_size() > 0


def test_raw_event_operations(tmp_path):
    """Test raw event CRUD operations"""
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))
    db.initialize()

    # Create event
    event = RawEvent(
        source="test_source",
        title="Test Event",
        content="Test content",
        source_url="https://test.com/event1",
        scraped_at=datetime.now()
    )

    event_id = db.insert_raw_event(event)
    assert event_id > 0

    # Retrieve event
    retrieved = db.get_raw_event(event_id)
    assert retrieved is not None
    assert retrieved.title == "Test Event"


def test_processed_event_operations(tmp_path):
    """Test processed event operations"""
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))
    db.initialize()

    # Create raw event first
    raw = RawEvent(
        source="test",
        title="Test",
        content="Content",
        source_url="https://test.com/1"
    )
    raw_id = db.insert_raw_event(raw)

    # Create processed event
    processed = ProcessedEvent(
        original_id=raw_id,
        title_en="Test Event",
        description_en="A test event",
        event_date=datetime.now(),
        location="Test Location",
        category=EventCategory.CULTURAL,
        status=EventStatus.PENDING
    )

    processed_id = db.insert_processed_event(processed)
    assert processed_id > 0

    # Retrieve
    retrieved = db.get_processed_event(processed_id)
    assert retrieved is not None
    assert retrieved.title_en == "Test Event"
