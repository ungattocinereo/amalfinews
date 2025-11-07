"""
Image extraction from web sources
"""

import logging
from typing import Optional
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


def extract_image_from_html(html: str, selectors: list = None) -> Optional[str]:
    """Extract image URL from HTML"""
    if not html:
        return None

    soup = BeautifulSoup(html, 'lxml')

    # Default image selectors
    if not selectors:
        selectors = [
            'meta[property="og:image"]',
            'meta[name="twitter:image"]',
            'img.wp-post-image',
            'article img',
            '.post-thumbnail img',
            'img[itemprop="image"]'
        ]

    for selector in selectors:
        elem = soup.select_one(selector)
        if elem:
            # Get src from img or content from meta
            url = elem.get('content') or elem.get('src') or elem.get('data-src')
            if url:
                return url

    return None
