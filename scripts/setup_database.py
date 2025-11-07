#!/usr/bin/env python3
"""
Initialize database
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database import get_database
from src.core.config import get_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Initialize database"""
    logger.info("Initializing database...")

    try:
        config = get_config()
        db = get_database(config.database_path)

        # Initialize tables
        db.initialize()

        # Check database
        size_mb = db.get_database_size()

        logger.info(f"✅ Database initialized successfully")
        logger.info(f"   Path: {config.database_path}")
        logger.info(f"   Size: {size_mb:.2f} MB")

    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
