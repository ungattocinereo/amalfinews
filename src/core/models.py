"""
Data models for Amalfi Events Intelligence System
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict
from enum import Enum


class EventStatus(Enum):
    """Event processing status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"


class SourceType(Enum):
    """Website type"""
    WORDPRESS = "wordpress"
    CUSTOM = "custom"


class EventCategory(Enum):
    """Event categories"""
    CULTURAL = "cultural"
    FOOD = "food"
    FESTIVAL = "festival"
    NATURE = "nature"
    MARKET = "market"
    MUSIC = "music"
    OTHER = "other"


@dataclass
class SourceConfig:
    """Configuration for a news source"""
    id: str
    name: str
    url: str
    type: SourceType
    enabled: bool = True
    priority: int = 1
    rate_limit: float = 1.0
    selectors: Dict[str, str] = field(default_factory=dict)
    rss_feed: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class HealthStatus:
    """Health check status for a source"""
    url: str
    healthy: bool
    status_code: Optional[int] = None
    response_time: Optional[float] = None
    articles_found: int = 0
    error: Optional[str] = None
    checks: Dict[str, bool] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RawEvent:
    """Raw event scraped from source"""
    id: Optional[int] = None
    source: str = ""
    title: str = ""
    content: str = ""
    event_date: Optional[datetime] = None
    image_url: Optional[str] = None
    source_url: str = ""
    scraped_at: datetime = field(default_factory=datetime.now)
    processed: bool = False
    processing_notes: Optional[str] = None


@dataclass
class ProcessedEvent:
    """Processed and translated event"""
    id: Optional[int] = None
    original_id: int = 0
    title_en: str = ""
    description_en: str = ""
    event_date: datetime = field(default_factory=datetime.now)
    event_time: Optional[str] = None
    location: str = ""
    price_info: Optional[str] = None
    accessibility: Optional[str] = None
    category: EventCategory = EventCategory.OTHER
    image_url: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    status: EventStatus = EventStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    moderated_at: Optional[datetime] = None
    moderated_by: Optional[str] = None
    published_at: Optional[datetime] = None
    wordpress_post_id: Optional[int] = None


@dataclass
class FilterResult:
    """Result from LLM filtering"""
    relevant_ids: List[int]
    reasoning: Dict[int, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TranslationResult:
    """Result from LLM translation"""
    is_valid: bool
    title_en: Optional[str] = None
    description_en: Optional[str] = None
    event_date: Optional[str] = None
    event_time: Optional[str] = None
    location: Optional[str] = None
    price_info: Optional[str] = None
    accessibility: Optional[str] = None
    category: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    rejection_reason: Optional[str] = None


@dataclass
class DailyStats:
    """Daily processing statistics"""
    date: datetime = field(default_factory=datetime.now)
    sources_checked: int = 0
    sources_healthy: int = 0
    events_scraped: int = 0
    events_filtered: int = 0
    events_translated: int = 0
    events_pending: int = 0
    events_approved: int = 0
    events_rejected: int = 0
    events_published: int = 0
    processing_time_seconds: float = 0.0
    deepseek_calls: int = 0
    deepseek_tokens: int = 0
    deepseek_cost: float = 0.0
    errors: List[str] = field(default_factory=list)


@dataclass
class SystemMetrics:
    """System resource metrics"""
    timestamp: datetime = field(default_factory=datetime.now)
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    memory_percent: float = 0.0
    database_size_mb: float = 0.0
    log_size_mb: float = 0.0


@dataclass
class CrawlerResult:
    """Result from web crawler"""
    source_id: str
    success: bool
    events: List[RawEvent] = field(default_factory=list)
    error: Optional[str] = None
    duration_seconds: float = 0.0


@dataclass
class DeepSeekUsage:
    """DeepSeek API usage tracking"""
    timestamp: datetime = field(default_factory=datetime.now)
    operation: str = ""  # 'filter' or 'translate'
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0
    success: bool = True
    error: Optional[str] = None


def raw_event_from_dict(data: dict) -> RawEvent:
    """Create RawEvent from dictionary"""
    return RawEvent(
        id=data.get('id'),
        source=data.get('source', ''),
        title=data.get('title', ''),
        content=data.get('content', ''),
        event_date=data.get('event_date'),
        image_url=data.get('image_url'),
        source_url=data.get('source_url', ''),
        scraped_at=data.get('scraped_at', datetime.now()),
        processed=data.get('processed', False),
        processing_notes=data.get('processing_notes')
    )


def processed_event_from_dict(data: dict) -> ProcessedEvent:
    """Create ProcessedEvent from dictionary"""
    return ProcessedEvent(
        id=data.get('id'),
        original_id=data.get('original_id', 0),
        title_en=data.get('title_en', ''),
        description_en=data.get('description_en', ''),
        event_date=data.get('event_date', datetime.now()),
        event_time=data.get('event_time'),
        location=data.get('location', ''),
        price_info=data.get('price_info'),
        accessibility=data.get('accessibility'),
        category=EventCategory(data.get('category', 'other')),
        image_url=data.get('image_url'),
        keywords=data.get('keywords', []),
        status=EventStatus(data.get('status', 'pending')),
        created_at=data.get('created_at', datetime.now()),
        moderated_at=data.get('moderated_at'),
        moderated_by=data.get('moderated_by'),
        published_at=data.get('published_at'),
        wordpress_post_id=data.get('wordpress_post_id')
    )
