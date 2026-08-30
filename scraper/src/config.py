"""Centralized configuration for UAP Scraper Pipeline."""

import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class ScraperConfig:
    """Pipeline runtime configuration."""
    
    # GCP / Storage settings
    gcs_raw_bucket: str = os.getenv("GCS_RAW_BUCKET", "uap-scraper-lab-2026-scraper-raw")
    gcs_staging_bucket: str = os.getenv("GCS_STAGING_BUCKET", "uap-scraper-lab-2026-lakehouse-data")
    gcp_project_id: str = os.getenv("GCP_PROJECT_ID", "uap-scraper-lab-2026")
    upload_to_gcs: bool = os.getenv("UPLOAD_TO_GCS", "true").lower() in ("true", "1", "yes")
    local_output_dir: str = os.getenv("LOCAL_OUTPUT_DIR", "./data/output")
    
    # Concurrency and Performance
    parallel_collection: bool = os.getenv("PARALLEL_COLLECTION", "true").lower() in ("true", "1", "yes")
    max_workers: int = int(os.getenv("MAX_WORKERS", "6"))
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    max_records_per_source: int = int(os.getenv("MAX_RECORDS_PER_SOURCE", "1000"))
    
    # Resilience & Fallback
    enable_synthetic_fallback: bool = os.getenv("ENABLE_SYNTHETIC_FALLBACK", "true").lower() in ("true", "1", "yes")
    retry_attempts: int = int(os.getenv("RETRY_ATTEMPTS", "3"))
    retry_backoff_factor: float = float(os.getenv("RETRY_BACKOFF_FACTOR", "1.5"))
    
    # HTTP Service / API Mode
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8080"))
    
    # Active Collector Filter
    enabled_sources: List[str] = field(default_factory=lambda: [
        s.strip().lower() for s in os.getenv("ENABLED_SOURCES", "all").split(",") if s.strip()
    ])


# Global default configuration instance
config = ScraperConfig()
