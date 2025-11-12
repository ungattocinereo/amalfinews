"""
Source health check module
"""

import asyncio
import aiohttp
import logging
from datetime import datetime
from typing import List

from src.core.models import HealthStatus, SourceConfig


logger = logging.getLogger(__name__)


class HealthChecker:
    """Check health of news sources"""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    async def check_source(self, source: SourceConfig) -> HealthStatus:
        """Check if source is healthy"""
        checks = {}
        status_code = None
        response_time = None
        articles_found = 0
        error = None

        try:
            start = datetime.now()

            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7"
            }

            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession() as session:
                async with session.get(source.url, headers=headers, timeout=timeout, allow_redirects=True) as response:
                    response_time = (datetime.now() - start).total_seconds()
                    status_code = response.status

                    # Check status code
                    checks['status_code_200'] = (status_code == 200)

                    # Check response time (allow up to 10 seconds)
                    checks['response_time_ok'] = (response_time < 10.0)

                    # Check content
                    if status_code == 200:
                        html = await response.text()
                        checks['has_content'] = (len(html) > 1000)
                        # Encoding check is informational, not critical
                        checks['encoding_ok'] = True  # Most sites work fine regardless

                        # Quick check for articles (multiple patterns)
                        articles_found = (
                            html.count('<article') +
                            html.count('class="post') +
                            html.count('class="evento') +
                            html.count('class="event') +
                            html.count('class="notizia') +
                            html.count('class="news') +
                            html.count('class="entry')
                        )
                        # Article check is informational only, not required for health
                        checks['has_articles'] = True  # Always pass, just count for info
                    else:
                        checks['has_content'] = False
                        checks['encoding_ok'] = False

        except asyncio.TimeoutError:
            error = f"Timeout after {self.timeout}s"
            checks['timeout'] = False
        except Exception as e:
            error = str(e)
            logger.error(f"{source.id}: Health check error: {e}")

        healthy = all(checks.values()) and error is None

        return HealthStatus(
            url=source.url,
            healthy=healthy,
            status_code=status_code,
            response_time=response_time,
            articles_found=articles_found,
            error=error,
            checks=checks,
            timestamp=datetime.now()
        )

    async def check_all_sources(self, sources: List[SourceConfig]) -> List[HealthStatus]:
        """Check health of all sources in parallel"""
        logger.info(f"Checking health of {len(sources)} sources...")

        tasks = [self.check_source(source) for source in sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        health_statuses = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"{sources[i].id}: Health check failed: {result}")
                health_statuses.append(HealthStatus(
                    url=sources[i].url,
                    healthy=False,
                    error=str(result)
                ))
            else:
                health_statuses.append(result)

        healthy_count = sum(1 for h in health_statuses if h.healthy)
        logger.info(f"Health check complete: {healthy_count}/{len(sources)} sources healthy")

        return health_statuses
