"""
Configuration loader for Amalfi Events Intelligence System
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from dataclasses import dataclass

from src.core.models import SourceConfig, SourceType


@dataclass
class Config:
    """Main configuration container"""
    # System
    system_name: str
    system_version: str
    timezone: str

    # Paths
    database_path: str
    backup_path: str
    log_path: str

    # DeepSeek API
    deepseek_api_key: str
    deepseek_endpoint: str
    deepseek_model: str
    deepseek_temperature: float
    deepseek_max_tokens: int
    deepseek_timeout: int

    # Telegram
    telegram_bot_token: str
    telegram_admin_id: str

    # WordPress
    wordpress_url: str
    wordpress_username: str
    wordpress_app_password: str
    wordpress_category_id: int

    # Crawler settings
    crawl_timeout: int
    crawl_rate_limit: float
    max_articles_per_source: int
    user_agent: str

    # Processing
    batch_size: int
    max_description_words: int

    # Feature flags
    enable_image_download: bool
    enable_auto_publish: bool
    enable_telegram_notifications: bool
    dry_run_mode: bool

    # Other settings
    settings: Dict[str, Any]


class ConfigLoader:
    """Load and manage configuration"""

    def __init__(self, config_dir: str = "./config"):
        self.config_dir = Path(config_dir)
        load_dotenv()  # Load .env file

        self._settings = self._load_yaml("settings.yaml")
        self._sources = self._load_yaml("sources.yaml")
        self._prompts = self._load_yaml("prompts.yaml")

    def _load_yaml(self, filename: str) -> dict:
        """Load YAML configuration file"""
        filepath = self.config_dir / filename

        if not filepath.exists():
            raise FileNotFoundError(f"Configuration file not found: {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def get_config(self) -> Config:
        """Get main configuration object"""
        return Config(
            # System
            system_name=self._settings['system']['name'],
            system_version=self._settings['system']['version'],
            timezone=os.getenv('TIMEZONE', self._settings['system']['timezone']),

            # Paths
            database_path=os.getenv('DATABASE_PATH', self._settings['database']['path']),
            backup_path=os.getenv('DATABASE_BACKUP_PATH', self._settings['database']['backup_path']),
            log_path=os.getenv('LOG_PATH', self._settings['logging']['path']),

            # DeepSeek API
            deepseek_api_key=os.getenv('DEEPSEEK_API_KEY', ''),
            deepseek_endpoint=os.getenv('DEEPSEEK_ENDPOINT', 'https://api.deepseek.com/v1/chat/completions'),
            deepseek_model=os.getenv('DEEPSEEK_MODEL', self._settings['deepseek']['model']),
            deepseek_temperature=float(os.getenv('DEEPSEEK_TEMPERATURE', self._settings['deepseek']['temperature'])),
            deepseek_max_tokens=int(os.getenv('DEEPSEEK_MAX_TOKENS', self._settings['deepseek']['max_tokens'])),
            deepseek_timeout=int(os.getenv('DEEPSEEK_TIMEOUT', self._settings['deepseek']['timeout'])),

            # Telegram
            telegram_bot_token=os.getenv('TELEGRAM_BOT_TOKEN', ''),
            telegram_admin_id=os.getenv('TELEGRAM_ADMIN_ID', ''),

            # WordPress
            wordpress_url=os.getenv('WORDPRESS_URL', ''),
            wordpress_username=os.getenv('WORDPRESS_USERNAME', ''),
            wordpress_app_password=os.getenv('WORDPRESS_APP_PASSWORD', ''),
            wordpress_category_id=int(os.getenv('WORDPRESS_CATEGORY_ID', 1)),

            # Crawler
            crawl_timeout=int(os.getenv('CRAWL_TIMEOUT', self._settings['crawler']['timeout_seconds'])),
            crawl_rate_limit=float(os.getenv('CRAWL_RATE_LIMIT', self._settings['crawler']['rate_limit_delay'])),
            max_articles_per_source=int(os.getenv('MAX_ARTICLES_PER_SOURCE', self._settings['crawler']['max_articles_per_source'])),
            user_agent=os.getenv('USER_AGENT', self._settings['crawler']['user_agent']),

            # Processing
            batch_size=int(os.getenv('BATCH_SIZE', self._settings['deepseek']['batch_size'])),
            max_description_words=int(os.getenv('MAX_DESCRIPTION_WORDS', self._settings['processing']['max_description_words'])),

            # Feature flags
            enable_image_download=os.getenv('ENABLE_IMAGE_DOWNLOAD', 'true').lower() == 'true',
            enable_auto_publish=os.getenv('ENABLE_AUTO_PUBLISH', 'false').lower() == 'true',
            enable_telegram_notifications=os.getenv('ENABLE_TELEGRAM_NOTIFICATIONS', 'true').lower() == 'true',
            dry_run_mode=os.getenv('DRY_RUN_MODE', 'false').lower() == 'true',

            # Full settings dict for advanced usage
            settings=self._settings
        )

    def get_sources(self) -> List[SourceConfig]:
        """Get list of news sources"""
        sources = []

        for source_data in self._sources.get('sources', []):
            sources.append(SourceConfig(
                id=source_data['id'],
                name=source_data['name'],
                url=source_data['url'],
                type=SourceType(source_data['type']),
                enabled=source_data.get('enabled', True),
                priority=source_data.get('priority', 1),
                rate_limit=source_data.get('rate_limit', 1.0),
                selectors=source_data.get('selectors', {}),
                rss_feed=source_data.get('rss_feed'),
                notes=source_data.get('notes')
            ))

        return sources

    def get_enabled_sources(self) -> List[SourceConfig]:
        """Get only enabled sources"""
        return [s for s in self.get_sources() if s.enabled]

    def get_source_by_id(self, source_id: str) -> Optional[SourceConfig]:
        """Get specific source by ID"""
        for source in self.get_sources():
            if source.id == source_id:
                return source
        return None

    def get_prompts(self) -> dict:
        """Get LLM prompts"""
        return self._prompts.get('prompts', {})

    def get_prompt(self, prompt_name: str) -> dict:
        """Get specific prompt by name"""
        prompts = self.get_prompts()
        return prompts.get(prompt_name, {})

    def get_exclusion_keywords(self) -> List[str]:
        """Get list of keywords to exclude"""
        exclusions = self._sources.get('exclusions', {})
        all_keywords = []

        for category, keywords in exclusions.items():
            all_keywords.extend(keywords)

        return all_keywords

    def get_category_keywords(self, category: str) -> List[str]:
        """Get keywords for specific category"""
        categories = self._sources.get('categories', {})
        return categories.get(category, [])

    def validate_config(self) -> tuple[bool, List[str]]:
        """
        Validate configuration completeness
        Returns (is_valid, list_of_errors)
        """
        errors = []
        config = self.get_config()

        # Check required API keys
        if not config.deepseek_api_key:
            errors.append("DEEPSEEK_API_KEY is not set")

        if not config.telegram_bot_token:
            errors.append("TELEGRAM_BOT_TOKEN is not set")

        if not config.wordpress_url:
            errors.append("WORDPRESS_URL is not set")

        # Check paths exist
        paths_to_check = [
            Path(config.log_path),
            Path(config.database_path).parent,
            Path(config.backup_path)
        ]

        for path in paths_to_check:
            if not path.exists():
                try:
                    path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    errors.append(f"Cannot create directory {path}: {e}")

        # Check sources
        sources = self.get_enabled_sources()
        if len(sources) == 0:
            errors.append("No enabled sources found")

        return len(errors) == 0, errors


# Singleton instance
_config_loader: Optional[ConfigLoader] = None


def get_config_loader(config_dir: str = "./config") -> ConfigLoader:
    """Get singleton ConfigLoader instance"""
    global _config_loader

    if _config_loader is None:
        _config_loader = ConfigLoader(config_dir)

    return _config_loader


def get_config() -> Config:
    """Convenience function to get config"""
    return get_config_loader().get_config()


def get_sources() -> List[SourceConfig]:
    """Convenience function to get sources"""
    return get_config_loader().get_sources()


def get_enabled_sources() -> List[SourceConfig]:
    """Convenience function to get enabled sources"""
    return get_config_loader().get_enabled_sources()
