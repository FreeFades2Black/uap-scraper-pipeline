"""Base collector class for UAP data sources.

All source-specific collectors inherit from this base class.
Provides connection pooling, retry logic, rotating headers, and metrics.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
import logging
import random
import time
from typing import Dict, List, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

logger = logging.getLogger(__name__)

# Realistic browser User-Agent pool for anti-blocking rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
]


class BaseCollector(ABC):
    """Abstract base class for UAP data collectors with robust networking and telemetry."""

    def __init__(self, name: str, timeout: int = 30):
        self.name = name
        self.timeout = timeout
        self.logger = logging.getLogger(f"collectors.{name}")
        self._session: Optional[requests.Session] = None

    def get_session(self) -> requests.Session:
        """Create or return a reusable HTTP session with connection pooling and retries."""
        if self._session is None:
            session = requests.Session()
            retry_strategy = Retry(
                total=3,
                backoff_factor=1.0,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "OPTIONS"]
            )
            adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=20)
            session.mount("https://", adapter)
            session.mount("http://", adapter)
            self._session = session
        return self._session

    def get_headers(self, custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Generate browser-like headers with randomized User-Agent."""
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,application/json,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-User": "?1",
        }
        if custom_headers:
            headers.update(custom_headers)
        return headers

    @abstractmethod
    def collect(self) -> Dict:
        """Collect data from the source.

        Returns:
            dict: Standardized payload with structure:
                {
                    "source": str,
                    "source_url": str,
                    "scraped_at": str (ISO timestamp),
                    "sighting_count": int,
                    "sightings": List[dict],
                    "latency_seconds": float,
                    "error": Optional[str]
                }
        """
        pass

    def safe_collect(self) -> Dict:
        """Safely collect data with timing, metrics, and error boundaries."""
        self.logger.info(f"Starting collection from {self.name}...")
        start_time = time.time()

        try:
            payload = self.collect()
            latency = round(time.time() - start_time, 3)
            payload["latency_seconds"] = latency
            payload.setdefault("error", None)

            count = payload.get("sighting_count", 0)
            if count > 0:
                self.logger.info(f"✅ {self.name}: Collected {count} sightings in {latency}s")
            else:
                self.logger.warning(f"⚠️ {self.name}: No sightings collected ({latency}s)")

            return payload

        except Exception as e:
            latency = round(time.time() - start_time, 3)
            self.logger.error(f"❌ {self.name}: Collection failed ({latency}s) - {e}")
            return {
                "source": self.name,
                "source_url": "error",
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "sighting_count": 0,
                "sightings": [],
                "latency_seconds": latency,
                "error": str(e),
            }

    def normalize_sighting(self, raw_data: dict) -> dict:
        """Normalize raw sighting data to standard lakehouse schema."""
        return {
            "date_time": str(raw_data.get("date_time") or raw_data.get("datetime") or "Unknown").strip(),
            "city": str(raw_data.get("city") or "Unknown").strip().title(),
            "state": str(raw_data.get("state") or "Unknown").strip().upper(),
            "country": str(raw_data.get("country") or "USA").strip().upper(),
            "shape": str(raw_data.get("shape") or "Unknown").strip().title(),
            "duration": str(raw_data.get("duration") or raw_data.get("duration (seconds)") or "Unknown").strip(),
            "summary": str(raw_data.get("summary") or raw_data.get("comments") or raw_data.get("text") or "").strip(),
            "report_link": raw_data.get("report_link"),
            "latitude": raw_data.get("latitude"),
            "longitude": raw_data.get("longitude"),
            "raw_data": raw_data,
        }
