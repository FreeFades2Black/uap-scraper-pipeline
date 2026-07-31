"""UAP Web Scraper - NUFORC Data Collection

Scrapes UAP sighting reports from the National UFO Reporting Center (NUFORC)
and uploads structured JSON data to Google Cloud Storage for lakehouse ingestion.
"""

import os
import logging
from datetime import datetime, timezone
import json
from bs4 import BeautifulSoup
from google.cloud import storage
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
BUCKET_NAME = os.getenv("GCS_RAW_BUCKET", "uap-scraper-lab-2026-scraper-raw")
# Try simpler NUFORC pages that may have less aggressive anti-scraping
TARGET_URL = os.getenv(
    "TARGET_URL",
    "https://www.nuforc.org/webreports/ndxevent.html"  # Try with www. subdomain
)
REQUEST_TIMEOUT = 30  # seconds


def fetch_and_parse_uap_reports(url: str) -> dict:
    """Fetches and parses UAP sighting reports from NUFORC HTML tables.
    
    Args:
        url: The NUFORC reports page URL to scrape
        
    Returns:
        dict: Structured payload containing scraped sightings with metadata
        
    Raises:
        requests.RequestException: If the HTTP request fails
        Exception: If parsing encounters unexpected HTML structure
    """
    logger.info(f"Fetching UAP reports from {url}...")
    
    # Initialize orchestrator and collect from all sources
    orchestrator = MultiSourceOrchestrator()
    consolidated_data = orchestrator.collect_all(parallel=parallel, max_workers=MAX_WORKERS)
    
    return consolidated_data


def upload_to_gcs(bucket_name: str, payload: dict) -> str:
    """Uploads scraped UAP data as JSON to Google Cloud Storage.
    
    Args:
        bucket_name: Target GCS bucket name
        payload: Structured sighting data dictionary
        
    Returns:
        str: The GCS blob path where data was uploaded
        
    Raises:
        Exception: If GCS upload fails
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    destination_blob_name = f"raw_ingest/uap_sightings_{timestamp}.json"
    
    logger.info(f"Uploading to gs://{bucket_name}/{destination_blob_name}...")
    
    try:
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        
        # Upload JSON with proper formatting
        blob.upload_from_string(
            data=json.dumps(payload, indent=2),
            content_type="application/json"
        )
        
        logger.info(
            f"✅ Successfully uploaded {payload.get('total_sightings', 0)} UAP sightings "
            f"to gs://{bucket_name}/{destination_blob_name}"
        )
        
        return destination_blob_name
        
    except Exception as e:
        logger.error(f"GCS upload failed: {e}")
        raise


def main():
    """Main execution function for the multi-source UAP scraper."""
    logger.info("="*60)
    logger.info("Starting Multi-Source UAP Data Aggregator")
    logger.info(f"Mode: {'Parallel' if PARALLEL_COLLECTION else 'Sequential'}")
    logger.info(f"Destination: gs://{BUCKET_NAME}/raw_ingest/")
    logger.info("="*60)
    
    try:
        # Step 1: Collect from all sources
        data = collect_from_all_sources(parallel=PARALLEL_COLLECTION)
        
        if data.get("total_sightings", 0) == 0:
            logger.warning("No sightings collected from any source")
            return
        
        # Step 2: Upload consolidated data to GCS
        blob_path = upload_to_gcs(BUCKET_NAME, data)
        
        # Step 3: Summary
        logger.info("="*60)
        logger.info("✅ Multi-Source UAP Collection Completed Successfully")
        logger.info(f"Total Sightings: {data.get('total_sightings', 0)}")
        logger.info(f"Successful Sources: {data.get('successful_sources', 0)}")
        logger.info(f"GCS Path: gs://{BUCKET_NAME}/{blob_path}")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"❌ Multi-source pipeline failed: {e}")
        raise


def cloud_function_entry(request):
    """Google Cloud Function entry point for HTTP trigger.
    
    Args:
        request: Flask request object (unused, but required by Cloud Functions)
        
    Returns:
        tuple: (response_message, status_code)
    """
    try:
        main()
        return ("✅ UAP scraper completed successfully", 200)
    except Exception as e:
        logger.error(f"Cloud Function execution failed: {e}")
        return (f"❌ Scraper failed: {str(e)}", 500)


if __name__ == "__main__":
    main()
