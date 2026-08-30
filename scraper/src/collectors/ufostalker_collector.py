"""UFO Stalker Collector.

Collects public geolocation-indexed sighting reports.
"""

from datetime import datetime, timezone
from typing import Dict
from .base import BaseCollector


class UFOStalkerCollector(BaseCollector):
    """Collects UAP data from UFO Stalker database."""

    def __init__(self):
        super().__init__("UFOStalker", timeout=30)
        self.base_url = "https://www.ufostalker.com"
        self.endpoints = [
            "https://www.ufostalker.com/api/sightings/recent",
            "https://www.ufostalker.com/api/v1/sightings"
        ]

    def collect(self) -> Dict:
        """Attempt to collect recent sightings from UFO Stalker."""
        all_sightings = []
        last_error = None
        session = self.get_session()
        headers = self.get_headers({"Accept": "application/json"})

        for endpoint in self.endpoints:
            try:
                response = session.get(endpoint, headers=headers, timeout=self.timeout)
                if response.status_code == 200:
                    data = response.json()
                    records = data if isinstance(data, list) else data.get("sightings") or data.get("data") or []

                    for rec in records[:50]:
                        raw_data = {
                            "date_time": str(rec.get("occurred") or rec.get("date") or "Unknown"),
                            "city": str(rec.get("city") or "Unknown"),
                            "state": str(rec.get("state") or "Unknown"),
                            "country": str(rec.get("country") or "USA"),
                            "shape": str(rec.get("shape") or "Unknown"),
                            "duration": str(rec.get("duration") or "Unknown"),
                            "summary": str(rec.get("summary") or rec.get("description") or "")[:400],
                            "latitude": rec.get("latitude") or rec.get("lat"),
                            "longitude": rec.get("longitude") or rec.get("lon"),
                            "report_link": f"{self.base_url}/sighting/{rec.get('id')}" if rec.get("id") else None
                        }
                        all_sightings.append(self.normalize_sighting(raw_data))

                    if all_sightings:
                        self.logger.info(f"✅ UFO Stalker returned {len(all_sightings)} records")
                        break
                else:
                    last_error = f"HTTP {response.status_code}"
            except Exception as e:
                last_error = str(e)
                self.logger.warning(f"UFO Stalker endpoint failed ({endpoint}): {e}")

        return {
            "source": "UFOStalker",
            "source_url": self.base_url,
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "sighting_count": len(all_sightings),
            "sightings": all_sightings,
            "error": last_error if len(all_sightings) == 0 else None
        }
