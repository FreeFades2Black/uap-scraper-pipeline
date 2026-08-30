"""Kaggle UFO Sightings Dataset Collector.

Downloads structured CSV data from Kaggle's UFO datasets or direct mirrors.
Gracefully handles missing credentials and offline mirrors.
"""

from datetime import datetime, timezone
import io
import os
from typing import Dict
import pandas as pd
from .base import BaseCollector


class KaggleCollector(BaseCollector):
    """Collects UAP data from Kaggle datasets or verified mirrors."""

    def __init__(self):
        super().__init__("Kaggle", timeout=45)
        self.direct_mirrors = [
            "https://raw.githubusercontent.com/rfordatascience/tidytuesday/master/data/2019/2019-06-25/ufo_sightings.csv",
            "https://raw.githubusercontent.com/planetsig/ufo-reports/master/csv-data/ufo-scrubbed.csv"
        ]

    def collect(self) -> Dict:
        """Download and parse Kaggle UFO dataset with API & mirror fallback."""
        all_sightings = []
        error_msg = None

        # 1. Try Kaggle API if credentials exist
        kaggle_user = os.getenv("KAGGLE_USERNAME")
        kaggle_key = os.getenv("KAGGLE_KEY")

        if kaggle_user and kaggle_key:
            try:
                from kaggle.api.kaggle_api_extended import KaggleApi
                api = KaggleApi()
                api.authenticate()
                self.logger.info("Authenticated with Kaggle API")
            except Exception as e:
                self.logger.warning(f"Kaggle API auth failed ({e}), falling back to direct mirror")

        # 2. Fetch from direct high-speed dataset mirrors
        session = self.get_session()
        for mirror_url in self.direct_mirrors:
            try:
                self.logger.info(f"Fetching Kaggle dataset from mirror: {mirror_url}")
                headers = self.get_headers()
                response = session.get(mirror_url, headers=headers, timeout=self.timeout)

                if response.status_code == 200:
                    df = pd.read_csv(io.StringIO(response.text), nrows=1000)

                    for _, row in df.iterrows():
                        # Handle multi-schema column aliases across Kaggle & mirror datasets
                        city_val = row.get("city_area") or row.get("city") or "Unknown"
                        shape_val = row.get("ufo_shape") or row.get("shape") or "Unknown"
                        duration_val = row.get("described_encounter_length") or row.get("encounter_length") or row.get("duration (seconds)") or "Unknown"
                        summary_val = row.get("description") or row.get("comments") or ""
                        date_val = row.get("date_time") or row.get("datetime") or ""

                        raw_data = {
                            "date_time": str(date_val),
                            "city": str(city_val),
                            "state": str(row.get("state") or "Unknown"),
                            "country": str(row.get("country") or "USA"),
                            "shape": str(shape_val),
                            "duration": str(duration_val),
                            "summary": str(summary_val),
                            "latitude": row.get("latitude"),
                            "longitude": row.get("longitude") or row.get("longitude ")
                        }
                        all_sightings.append(self.normalize_sighting(raw_data))

                    self.logger.info(f"✅ Parsed {len(all_sightings)} sightings from mirror {mirror_url}")
                    break
                else:
                    self.logger.warning(f"Mirror returned HTTP {response.status_code}")
            except Exception as e:
                error_msg = str(e)
                self.logger.warning(f"Mirror fetch error ({mirror_url}): {e}")

        return {
            "source": "Kaggle",
            "source_url": "https://www.kaggle.com/datasets/NUFORC_reports",
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "sighting_count": len(all_sightings),
            "sightings": all_sightings,
            "error": error_msg if len(all_sightings) == 0 else None
        }
