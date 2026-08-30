"""Synthetic / Airgap Fallback Collector.

Generates realistic structured UAP sighting data matching lakehouse schema
for offline testing, CI/CD pipeline validation, and airgap deployments.
"""

from datetime import datetime, timezone
from typing import Dict
from .base import BaseCollector
from ..uap_test_data import generate_uap_sightings


class SyntheticCollector(BaseCollector):
    """Generates synthetic UAP test telemetry for pipeline validation."""

    def __init__(self, count: int = 50):
        super().__init__("Synthetic_UAP", timeout=5)
        self.count = count

    def collect(self) -> Dict:
        """Generate normalized test sightings."""
        payload = generate_uap_sightings(count=self.count)
        raw_sightings = payload.get("sightings", [])
        normalized = [self.normalize_sighting(s) for s in raw_sightings]

        self.logger.info(f"✅ Generated {len(normalized)} synthetic sighting records")
        return {
            "source": "Synthetic_Telemetry",
            "source_url": "internal://synthetic-generator",
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "sighting_count": len(normalized),
            "sightings": normalized,
            "error": None
        }
