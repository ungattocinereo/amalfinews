"""
WordPress REST API client
"""

import logging
import requests
from typing import Dict, Optional
import base64


logger = logging.getLogger(__name__)


class WordPressClient:
    """WordPress REST API client"""

    def __init__(self, url: str, username: str, app_password: str):
        self.url = url.rstrip('/')
        self.api_url = f"{self.url}/wp-json/wp/v2"
        self.username = username
        self.app_password = app_password

        # Create auth header
        credentials = f"{username}:{app_password}"
        token = base64.b64encode(credentials.encode()).decode()
        self.headers = {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json"
        }

    def test_connection(self) -> bool:
        """Test WordPress API connection"""
        try:
            response = requests.get(f"{self.api_url}/users/me", headers=self.headers, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"WordPress connection test failed: {e}")
            return False

    def create_post(self, post_data: Dict) -> Optional[int]:
        """
        Create new post
        Returns post ID or None
        """
        try:
            response = requests.post(
                f"{self.api_url}/posts",
                headers=self.headers,
                json=post_data,
                timeout=30
            )

            if response.status_code in [200, 201]:
                result = response.json()
                post_id = result.get('id')
                logger.info(f"Post created successfully: ID {post_id}")
                return post_id
            else:
                logger.error(f"Failed to create post: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error creating post: {e}")
            return None

    def update_post(self, post_id: int, post_data: Dict) -> bool:
        """Update existing post"""
        try:
            response = requests.post(
                f"{self.api_url}/posts/{post_id}",
                headers=self.headers,
                json=post_data,
                timeout=30
            )

            success = response.status_code == 200
            if success:
                logger.info(f"Post {post_id} updated successfully")
            else:
                logger.error(f"Failed to update post {post_id}: {response.status_code}")

            return success

        except Exception as e:
            logger.error(f"Error updating post {post_id}: {e}")
            return False

    def upload_media(self, image_url: str, title: str = "") -> Optional[int]:
        """
        Upload media from URL
        Returns media ID or None
        """
        try:
            # Download image
            img_response = requests.get(image_url, timeout=10)
            if img_response.status_code != 200:
                logger.error(f"Failed to download image: {image_url}")
                return None

            # Determine filename
            filename = image_url.split('/')[-1].split('?')[0]
            if not filename:
                filename = "event-image.jpg"

            # Upload to WordPress
            files = {'file': (filename, img_response.content)}
            headers = {"Authorization": self.headers["Authorization"]}

            response = requests.post(
                f"{self.api_url}/media",
                headers=headers,
                files=files,
                data={'title': title},
                timeout=30
            )

            if response.status_code == 201:
                result = response.json()
                media_id = result.get('id')
                logger.info(f"Media uploaded: ID {media_id}")
                return media_id
            else:
                logger.error(f"Failed to upload media: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error uploading media: {e}")
            return None

    def get_categories(self) -> Dict:
        """Get all categories"""
        try:
            response = requests.get(f"{self.api_url}/categories", headers=self.headers)
            if response.status_code == 200:
                categories = response.json()
                return {cat['name']: cat['id'] for cat in categories}
            return {}
        except Exception as e:
            logger.error(f"Error fetching categories: {e}")
            return {}

    def get_tags(self) -> Dict:
        """Get all tags"""
        try:
            response = requests.get(f"{self.api_url}/tags", headers=self.headers)
            if response.status_code == 200:
                tags = response.json()
                return {tag['name']: tag['id'] for tag in tags}
            return {}
        except Exception as e:
            logger.error(f"Error fetching tags: {e}")
            return {}
