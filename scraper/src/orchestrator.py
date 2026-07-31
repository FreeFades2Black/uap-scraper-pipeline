"""Multi-Source UAP Data Orchestrator.

Coordinates data collection from all 10 UAP sources and consolidates results.
"""

import logging
from datetime import datetime, timezone
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

from .collectors.base import BaseCollector
from .collectors.nuforc_collector import NUFORCCollector
from .collectors.kaggle_collector import KaggleCollector
from .collectors.mufon_collector import MUFONCollector
from .collectors.nasa_collector import NASACollector
from .collectors.huggingface_collector import HuggingFaceCollector
from .collectors.ufostalker_collector import UFOStalkerCollector

logger = logging.getLogger(__name__)


class MultiSourceOrchestrator:
    """Orchestrates UAP data collection from multiple sources."""
    
    def __init__(self):
        """Initialize all collectors."""
        self.collectors: List[BaseCollector] = [
            KaggleCollector(),          # Direct CSV download
            HuggingFaceCollector(),     # FBI/DoD declassified via HF
            NUFORCCollector(),          # National UFO Reporting Center
            MUFONCollector(),           # Mutual UFO Network
            NASACollector(),            # NASA UAP Study
            UFOStalkerCollector(),      # UFO Stalker mapping DB
            # TODO: Add remaining sources:
            # - AARO (aaro.mil)
            # - Black Vault (theblackvault.com)
            # - NARA (archives.gov)
            # - CUFOS (cufos.org)
        ]
        
        logger.info(f"Initialized {len(self.collectors)} collectors")
    
    def collect_all(self, parallel: bool = True, max_workers: int = 5) -> Dict:
        """Collect data from all sources.
        
        Args:
            parallel: Whether to run collectors in parallel (faster but more resource-intensive)
            max_workers: Max number of parallel collection threads
            
        Returns:
            dict: Consolidated payload with all sources
        """
        logger.info("=" * 60)
        logger.info("Starting Multi-Source UAP Data Collection")
        logger.info(f"Sources: {len(self.collectors)}")
        logger.info(f"Mode: {'Parallel' if parallel else 'Sequential'}")
        logger.info("=" * 60)
        
        all_payloads = []
        
        if parallel:
            # Parallel execution for speed
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(collector.safe_collect): collector 
                    for collector in self.collectors
                }
                
                for future in as_completed(futures):
                    collector = futures[future]
                    try:
                        payload = future.result()
                        all_payloads.append(payload)
                    except Exception as e:
                        logger.error(f"Collector {collector.name} raised exception: {e}")
        else:
            # Sequential execution
            for collector in self.collectors:
                payload = collector.safe_collect()
                all_payloads.append(payload)
        
        # Consolidate results
        consolidated = self._consolidate_payloads(all_payloads)
        
        logger.info("=" * 60)
        logger.info("✅ Multi-Source Collection Complete")
        logger.info(f"Total Sources Attempted: {len(self.collectors)}")
        logger.info(f"Total Sightings Collected: {consolidated['total_sightings']}")
        logger.info(f"Successful Sources: {consolidated['successful_sources']}/{len(self.collectors)}")
        logger.info("=" * 60)
        
        return consolidated
    
    def _consolidate_payloads(self, payloads: List[Dict]) -> Dict:
        """Consolidate all source payloads into single structure.
        
        Returns:
            dict: {
                "collection_timestamp": str,
                "total_sightings": int,
                "successful_sources": int,
                "source_breakdown": dict,
                "all_sightings": List[dict] (with source field added)
            }
        """
        all_sightings = []
        source_breakdown = {}
        successful_sources = 0
        
        for payload in payloads:
            source_name = payload.get("source", "Unknown")
            sighting_count = payload.get("sighting_count", 0)
            error = payload.get("error")
            
            source_breakdown[source_name] = {
                "count": sighting_count,
                "url": payload.get("source_url"),
                "success": sighting_count > 0 and not error,
                "error": error
            }
            
            if sighting_count > 0:
                successful_sources += 1
            
            # Add source field to each sighting
            for sighting in payload.get("sightings", []):
                sighting["data_source"] = source_name
                all_sightings.append(sighting)
        
        return {
            "collection_timestamp": datetime.now(timezone.utc).isoformat(),
            "total_sightings": len(all_sightings),
            "successful_sources": successful_sources,
            "source_breakdown": source_breakdown,
            "all_sightings": all_sightings
        }
