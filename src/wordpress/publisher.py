"""
WordPress event publisher
"""

import logging
from typing import Optional

from src.core.models import ProcessedEvent
from src.core.database import get_database
from src.wordpress.client import WordPressClient
from src.wordpress.formatter import format_event_post


logger = logging.getLogger(__name__)


class EventPublisher:
    """Publish events to WordPress"""

    def __init__(self, client: WordPressClient, category_id: int = 1, dry_run: bool = False):
        self.client = client
        self.category_id = category_id
        self.dry_run = dry_run

    async def publish_event(self, event: ProcessedEvent) -> Optional[int]:
        """
        Publish event to WordPress
        Returns WordPress post ID or None
        """
        logger.info(f"Publishing event {event.id}: {event.title_en}")

        if self.dry_run:
            logger.info(f"DRY RUN: Would publish event {event.id}")
            return 99999

        try:
            # Format post data
            post_data = format_event_post(event, self.category_id)

            # Upload featured image if available
            if event.image_url:
                media_id = self.client.upload_media(event.image_url, event.title_en)
                if media_id:
                    post_data['featured_media'] = media_id

            # Create post
            post_id = self.client.create_post(post_data)

            if post_id:
                # Update database
                db = get_database()
                db.mark_event_published(event.id, post_id)
                logger.info(f"Event {event.id} published successfully as post {post_id}")
                return post_id
            else:
                logger.error(f"Failed to publish event {event.id}")
                return None

        except Exception as e:
            logger.error(f"Error publishing event {event.id}: {e}")
            return None

    async def publish_approved_events(self) -> int:
        """
        Publish all approved but unpublished events
        Returns count of published events
        """
        db = get_database()
        approved_events = db.get_approved_unpublished_events()

        if not approved_events:
            logger.info("No approved events to publish")
            return 0

        logger.info(f"Publishing {len(approved_events)} approved events")

        published_count = 0
        for event in approved_events:
            post_id = await self.publish_event(event)
            if post_id:
                published_count += 1

        logger.info(f"Published {published_count}/{len(approved_events)} events")
        return published_count
