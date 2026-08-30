"""Hugging Face UFOCR / Declassified Dataset Collector.

Downloads structured UAP data from Hugging Face datasets or HTTP REST endpoints.
Dataset: reducto/ufocr (FBI/DoD declassified records)
"""

from datetime import datetime, timezone
import json
from typing import Dict
from .base import BaseCollector


class HuggingFaceCollector(BaseCollector):
    """Collects UAP data from Hugging Face datasets."""

    def __init__(self):
        super().__init__("HuggingFace", timeout=30)
        self.dataset_name = "reducto/ufocr"
        self.hf_api_url = f"https://datasets-server.huggingface.co/rows?dataset={self.dataset_name}&config=default&split=train&offset=0&limit=100"

    def collect(self) -> Dict:
        """Download from Hugging Face UFOCR dataset via library or REST API."""
        all_sightings = []
        last_error = None

        # 1. Try native datasets library
        try:
            from datasets import load_dataset
            self.logger.info(f"Loading dataset via HuggingFace datasets library: {self.dataset_name}")
            dataset = load_dataset(self.dataset_name, split="train[:200]")

            for record in dataset:
                raw_data = {
                    "date_time": str(record.get("date") or record.get("datetime") or "Unknown"),
                    "city": str(record.get("location") or record.get("city") or "Unknown"),
                    "state": "Various",
                    "country": "USA",
                    "shape": "Declassified Record",
                    "duration": str(record.get("duration") or "Unknown"),
                    "summary": str(record.get("text") or record.get("content") or record.get("summary") or "")[:500],
                    "document_type": "FBI/DoD Declassified"
                }
                all_sightings.append(self.normalize_sighting(raw_data))

            self.logger.info(f"✅ Loaded {len(all_sightings)} records via HuggingFace library")

        except Exception as e:
            self.logger.warning(f"Native datasets load failed ({e}), attempting HF REST API...")
            last_error = str(e)

            # 2. Fallback to HF Datasets HTTP API
            try:
                session = self.get_session()
                headers = self.get_headers()
                response = session.get(self.hf_api_url, headers=headers, timeout=self.timeout)

                if response.status_code == 200:
                    data = response.json()
                    rows = data.get("rows", [])
                    for item in rows:
                        row = item.get("row", {})
                        raw_data = {
                            "date_time": str(row.get("date") or "Unknown"),
                            "city": str(row.get("location") or "Unknown"),
                            "state": "Various",
                            "country": "USA",
                            "shape": "Declassified Record",
                            "duration": "Unknown",
                            "summary": str(row.get("text") or row.get("summary") or "")[:500]
                        }
                        all_sightings.append(self.normalize_sighting(raw_data))
                    self.logger.info(f"✅ Loaded {len(all_sightings)} records via HF REST API")
                else:
                    self.logger.warning(f"HF API returned status {response.status_code}")
            except Exception as api_err:
                last_error = str(api_err)
                self.logger.warning(f"HF REST API failed: {api_err}")

        return {
            "source": "HuggingFace_UFOCR",
            "source_url": f"https://huggingface.co/datasets/{self.dataset_name}",
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "sighting_count": len(all_sightings),
            "sightings": all_sightings,
            "error": last_error if len(all_sightings) == 0 else None
        }
