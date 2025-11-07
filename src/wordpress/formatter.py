"""
WordPress content formatter
"""

from typing import Dict, List
from src.core.models import ProcessedEvent


def format_event_post(event: ProcessedEvent, category_id: int) -> Dict:
    """
    Format ProcessedEvent as WordPress post data
    """
    # Format title with date
    title = f"{event.title_en} - {event.event_date.strftime('%B %d, %Y')}"

    # Format content
    content = format_post_content(event)

    # Prepare tags
    tags = event.keywords[:5] if event.keywords else []

    post_data = {
        'title': title,
        'content': content,
        'status': 'publish',
        'categories': [category_id],
        'tags': tags,
        'meta': {
            'event_date': event.event_date.isoformat(),
            'location': event.location,
            'category': event.category.value
        }
    }

    return post_data


def format_post_content(event: ProcessedEvent) -> str:
    """Format event content as HTML"""

    html = f"""
<div class="event-details">
    <div class="event-header">
        <h2>{event.title_en}</h2>
    </div>

    <div class="event-meta">
        <p><strong>📅 Date:</strong> {format_event_date(event)}</p>
        <p><strong>📍 Location:</strong> {event.location}</p>
"""

    if event.price_info:
        html += f'        <p><strong>💰 Price:</strong> {event.price_info}</p>\n'

    if event.accessibility:
        html += f'        <p><strong>🚌 How to get there:</strong> {event.accessibility}</p>\n'

    html += """    </div>

    <div class="event-description">
"""

    # Add description paragraphs
    paragraphs = event.description_en.split('\n')
    for para in paragraphs:
        if para.strip():
            html += f"        <p>{para.strip()}</p>\n"

    html += """    </div>

    <div class="event-category">
        <p><em>Category: {category}</em></p>
    </div>
</div>
""".format(category=event.category.value.title())

    return html


def format_event_date(event: ProcessedEvent) -> str:
    """Format event date with optional time"""
    date_str = event.event_date.strftime('%A, %B %d, %Y')

    if event.event_time:
        date_str += f" at {event.event_time}"

    return date_str


def generate_excerpt(event: ProcessedEvent, max_length: int = 200) -> str:
    """Generate short excerpt for event"""
    description = event.description_en

    if len(description) <= max_length:
        return description

    # Truncate at sentence or word boundary
    excerpt = description[:max_length]
    last_period = excerpt.rfind('.')
    last_space = excerpt.rfind(' ')

    if last_period > max_length * 0.7:
        return excerpt[:last_period + 1]
    elif last_space > 0:
        return excerpt[:last_space] + "..."

    return excerpt + "..."
