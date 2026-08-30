"""Multi-Source UAP Data Orchestrator.

Coordinates high-throughput data collection across 8+ UAP sources,
performs cross-source deduplication, timing telemetry, and synthetic fallback.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import logging
import time
from typing import Dict, List, Optional

from .collectors.base import BaseCollector
from .collectors.nuforc_collector import NUFORCCollector
from .collectors.kaggle_collector import KaggleCollector
from .collectors.huggingface_collector import HuggingFaceCollector
from .collectors.nasa_collector import NASACollector
from .collectors.mufon_collector import MUFONCollector
from .collectors.ufostalker_collector import UFOStalkerCollector
from .collectors.aaro_collector import AAROCollector
from .collectors.synthetic_collector import SyntheticCollector
from .config import config

logger = logging.getLogger(__name__)


class MultiSourceOrchestrator:
    """Orchestrates multi-source UAP scraping, deduplication, and telemetry."""

    def __init__(self, sources: Optional[List[str]] = None):
        """Initialize collectors according to enabled source filter."""
        all_collectors: List[BaseCollector] = [
            KaggleCollector(),
            HuggingFaceCollector(),
            NUFORCCollector(),
            AAROCollector(),
            NASACollector(),
            MUFONCollector(),
            UFOStalkerCollector(),
        ]

        # Filter by enabled sources if configured
        selected = sources or config.enabled_sources
        if "all" in selected:
            self.collectors = all_collectors
        else:
            self.collectors = [
                c for c in all_collectors 
                if c.name.lower() in [s.lower() for s in selected]
            ]
            if not self.collectors:
                logger.warning("No matching collectors found for filter, defaulting to all")
                self.collectors = all_collectors

        logger.info(f"Initialized {len(self.collectors)} collectors: {[c.name for c in self.collectors]}")

    def collect_all(self, parallel: Optional[bool] = None, max_workers: Optional[int] = None) -> Dict:
        """Collect data from all sources concurrently with telemetry and fallback."""
        is_parallel = parallel if parallel is not None else config.parallel_collection
        workers = max_workers or config.max_workers

        logger.info("=" * 60)
        logger.info("Starting Multi-Source UAP Ingestion Pipeline")
        logger.info(f"Collectors: {[c.name for c in self.collectors]}")
        logger.info(f"Execution Mode: {'Parallel (Workers: ' + str(workers) + ')' if is_parallel else 'Sequential'}")
        logger.info("=" * 60)

        start_time = time.time()
        all_payloads = []

        if is_parallel:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                future_to_collector = {
                    executor.submit(c.safe_collect): c for c in self.collectors
                }
                for future in as_completed(future_to_collector):
                    collector = future_to_collector[future]
                    try:
                        payload = future.result()
                        all_payloads.append(payload)
                    except Exception as e:
                        logger.error(f"Collector {collector.name} fatal error: {e}")
                        all_payloads.append({
                            "source": collector.name,
                            "source_url": "error",
                            "scraped_at": datetime.now(timezone.utc).isoformat(),
                            "sighting_count": 0,
                            "sightings": [],
                            "error": str(e)
                        })
        else:
            for c in self.collectors:
                all_payloads.append(c.safe_collect())

        # Consolidate results
        consolidated = self._consolidate_payloads(all_payloads, start_time)

        # Resilient fallback: if zero sightings and synthetic fallback enabled, generate synthetic records
        if consolidated["total_sightings"] == 0 and config.enable_synthetic_fallback:
            logger.warning("⚠️ All live web sources returned 0 sightings. Engaging Synthetic Fallback...")
            synthetic = SyntheticCollector(count=50).safe_collect()
            all_payloads.append(synthetic)
            consolidated = self._consolidate_payloads(all_payloads, start_time)

        logger.info("=" * 60)
        logger.info("✅ Multi-Source Ingestion Finished")
        logger.info(f"Total Sightings (Deduplicated): {consolidated['total_sightings']}")
        logger.info(f"Successful Sources: {consolidated['successful_sources']}/{len(self.collectors)}")
        logger.info(f"Pipeline Duration: {consolidated['duration_seconds']}s")
        logger.info("=" * 60)

        return consolidated

    def _generate_sighting_id(self, sighting: dict) -> str:
        """Create deterministic content hash for cross-source deduplication."""
        date = str(sighting.get("date_time", "")).lower().strip()
        city = str(sighting.get("city", "")).lower().strip()
        state = str(sighting.get("state", "")).lower().strip()
        shape = str(sighting.get("shape", "")).lower().strip()
        summary = str(sighting.get("summary", ""))[:50].lower().strip()
        raw_key = f"{date}|{city}|{state}|{shape}|{summary}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:16]

    def _consolidate_payloads(self, payloads: List[Dict], start_time: float) -> Dict:
        """Consolidate, deduplicate, and calculate metrics across payloads."""
        all_sightings = []
        seen_ids = set()
        source_breakdown = {}
        successful_sources = 0
        duplicates_removed = 0

        for payload in payloads:
            source_name = payload.get("source", "Unknown")
            count = payload.get("sighting_count", 0)
            error = payload.get("error")
            latency = payload.get("latency_seconds", 0.0)

            source_breakdown[source_name] = {
                "count": count,
                "url": payload.get("source_url"),
                "success": count > 0 and not error,
                "error": error,
                "latency_seconds": latency,
            }

            if count > 0:
                successful_sources += 1

            for sighting in payload.get("sightings", []):
                sighting["data_source"] = source_name
                sighting_id = self._generate_sighting_id(sighting)
                sighting["sighting_hash"] = sighting_id

                if sighting_id not in seen_ids:
                    seen_ids.add(sighting_id)
                    all_sightings.append(sighting)
                else:
                    duplicates_removed += 1

        duration = round(time.time() - start_time, 3)

        return {
            "collection_timestamp": datetime.now(timezone.utc).isoformat(),
            "total_sightings": len(all_sightings),
            "duplicates_removed": duplicates_removed,
            "successful_sources": successful_sources,
            "duration_seconds": duration,
            "source_breakdown": source_breakdown,
            "all_sightings": all_sightings
        }
