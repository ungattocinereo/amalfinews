"""
Image validation
"""

import logging
from typing import Tuple


logger = logging.getLogger(__name__)


def validate_image_url(url: str, min_width: int = 800, min_height: int = 600) -> Tuple[bool, str]:
    """
    Validate image URL
    Returns (is_valid, reason)
    """
    if not url:
        return False, "No URL provided"

    # Check if URL is valid format
    if not url.startswith('http'):
        return False, "Invalid URL format"

    # Check file extension
    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    url_lower = url.lower()

    if not any(url_lower.endswith(ext) for ext in valid_extensions):
        # May still be valid if no extension visible
        pass

    return True, "Valid"


def is_image_size_valid(width: int, height: int, min_width: int = 800, min_height: int = 600) -> bool:
    """Check if image dimensions are acceptable"""
    return width >= min_width and height >= min_height
