"""Base collector class for UAP data sources.

All source-specific collectors inherit from this base class.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """Abstract base class for UAP data collectors."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"collectors.{name}")
    
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
                    "error": Optional[str]
                }
        """
        pass
    
    def safe_collect(self) -> Dict:
        """Safely collect data with error handling.
        
        Returns:
            dict: Payload (potentially with error field if collection failed)
        """
        self.logger.info(f"Starting collection from {self.name}...")
        
        try:
            payload = self.collect()
            
            if payload.get("sighting_count", 0) > 0:
                self.logger.info(
                    f"✅ {self.name}: Collected {payload['sighting_count']} sightings"
                )
            else:
                self.logger.warning(f"⚠️ {self.name}: No sightings collected")
            
            return payload
            
        except Exception as e:
            self.logger.error(f"❌ {self.name}: Collection failed - {e}")
            return {
                "source": self.name,
                "source_url": "error",
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "sighting_count": 0,
                "sightings": [],
                "error": str(e)
            }
    
    def normalize_sighting(self, raw_data: dict) -> dict:
        """Normalize raw sighting data to standard schema.
        
        Standard schema:
            {
                "date_time": str,
                "city": str,
                "state": str,
                "country": str,
                "shape": str,
                "duration": str,
                "summary": str,
                "report_link": Optional[str],
                "raw_data": dict (original data for reference)
            }
        """
        return {
            "date_time": raw_data.get("date_time", "Unknown"),
            "city": raw_data.get("city", "Unknown"),
            "state": raw_data.get("state", "Unknown"),
            "country": raw_data.get("country", "USA"),
            "shape": raw_data.get("shape", "Unknown"),
            "duration": raw_data.get("duration", "Unknown"),
            "summary": raw_data.get("summary", ""),
            "report_link": raw_data.get("report_link"),
            "raw_data": raw_data
        }
