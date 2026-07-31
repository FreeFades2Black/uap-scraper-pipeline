"""Hugging Face UFOCR Dataset Collector.

Downloads structured UAP data from Hugging Face datasets.
Dataset: reducto/ufocr (FBI/DoD declassified records)
"""

from datetime import datetime, timezone
from typing import Dict
from .base import BaseCollector


class HuggingFaceCollector(BaseCollector):
    """Collects UAP data from Hugging Face datasets."""
    
    def __init__(self):
        super().__init__("HuggingFace")
        self.dataset_name = "reducto/ufocr"
    
    def collect(self) -> Dict:
        """Download from Hugging Face UFOCR dataset."""
        
        all_sightings = []
        
        try:
            from datasets import load_dataset
            
            self.logger.info(f"Loading dataset: {self.dataset_name}")
            
            # Load dataset (limit to prevent huge downloads)
            dataset = load_dataset(self.dataset_name, split="train[:1000]")
            
            # Parse dataset records
            for record in dataset:
                # UFOCR dataset structure may vary - adapt as needed
                sighting = {
                    "date_time": record.get("date", "Unknown"),
                    "city": record.get("location", "Unknown"),
                    "state": "Various",
                    "country": "USA",
                    "shape": "Declassified",
                    "duration": record.get("duration", "Unknown"),
                    "summary": record.get("text", ""),
                    "report_link": None,
                    "document_type": "FBI/DoD Declassified"
                }
                all_sightings.append(sighting)
            
            self.logger.info(f"Loaded {len(all_sightings)} records from HuggingFace")
            
        except ImportError:
            self.logger.warning("datasets library not installed - skipping HuggingFace")
        except Exception as e:
            self.logger.error(f"HuggingFace collection error: {e}")
        
        return {
            "source": "HuggingFace_UFOCR",
            "source_url": f"https://huggingface.co/datasets/{self.dataset_name}",
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "sighting_count": len(all_sightings),
            "sightings": all_sightings
        }
