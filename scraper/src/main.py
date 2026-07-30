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
TARGET_URL = os.getenv(
    "TARGET_URL",
    "https://nuforc.org/webreports/ndxevent.html"
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
    
    # Enhanced browser headers to avoid 403 Forbidden
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0'
    }
    
    # Retry logic with exponential backoff
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Attempt {attempt}/{max_retries} - Fetching {url}...")
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT, allow_redirects=True)
            response.raise_for_status()
            logger.info(f"✅ Successfully retrieved page (status: {response.status_code}, size: {len(response.content)} bytes)")
            break
        except requests.HTTPError as e:
            if e.response.status_code == 403:
                logger.warning(f"Got 403 Forbidden on attempt {attempt}/{max_retries}")
                if attempt < max_retries:
                    import time
                    wait_time = retry_delay * (2 ** (attempt - 1))  # exponential backoff
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
            logger.error(f"HTTP error on attempt {attempt}: {e}")
            if attempt == max_retries:
                raise
        except requests.RequestException as e:
            logger.error(f"Request failed on attempt {attempt}: {e}")
            if attempt == max_retries:
                raise
            import time
            time.sleep(retry_delay)
    else:
        raise requests.RequestException(f"Failed after {max_retries} attempts")
    
    # Parse HTML content
    logger.info("Parsing HTML content...")
    soup = BeautifulSoup(response.text, "html.parser")
    
    scraped_sightings = []
    
    # NUFORC uses HTML tables with one row per sighting
    table = soup.find("table")
    
    if not table:
        logger.warning("No table found in HTML - page structure may have changed")
        return {
            "source": "NUFORC",
            "source_url": url,
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "sighting_count": 0,
            "sightings": [],
            "error": "No table found in HTML"
        }
    
    rows = table.find_all("tr")
    logger.info(f"Found {len(rows)} rows in table (including header)")
    
    # Skip header row, process data rows
    for idx, row in enumerate(rows[1:], start=1):
        cols = row.find_all("td")
        
        if len(cols) < 6:
            logger.debug(f"Skipping row {idx} - insufficient columns ({len(cols)})")
            continue
        
        try:
            # Extract data from table columns
            sighting = {
                "date_time": cols[0].get_text(strip=True),
                "city": cols[1].get_text(strip=True),
                "state": cols[2].get_text(strip=True),
                "country": cols[3].get_text(strip=True),
                "shape": cols[4].get_text(strip=True),
                "duration": cols[5].get_text(strip=True),
                "summary": cols[6].get_text(strip=True) if len(cols) > 6 else None,
                "report_link": None
            }
            
            # Extract report link if available
            link_element = cols[0].find("a")
            if link_element and link_element.get("href"):
                sighting["report_link"] = link_element["href"]
            
            scraped_sightings.append(sighting)
            
        except Exception as e:
            logger.warning(f"Error parsing row {idx}: {e}")
            continue
    
    logger.info(f"Successfully parsed {len(scraped_sightings)} UAP sightings")
    
    # Package into structured payload
    payload = {
        "source": "NUFORC",
        "source_url": url,
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "sighting_count": len(scraped_sightings),
        "sightings": scraped_sightings,
    }
    
    return payload


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
            f"✅ Successfully uploaded {payload['sighting_count']} UAP sightings "
            f"to gs://{bucket_name}/{destination_blob_name}"
        )
        
        return destination_blob_name
        
    except Exception as e:
        logger.error(f"GCS upload failed: {e}")
        raise


def main():
    """Main execution function for the UAP scraper pipeline."""
    logger.info("="*60)
    logger.info("Starting UAP Scraper Pipeline")
    logger.info(f"Target: {TARGET_URL}")
    logger.info(f"Destination: gs://{BUCKET_NAME}/raw_ingest/")
    logger.info("="*60)
    
    try:
        # Step 1: Fetch and parse UAP reports from NUFORC
        data = fetch_and_parse_uap_reports(TARGET_URL)
        
        if data["sighting_count"] == 0:
            logger.warning("No sightings were scraped - check target URL or HTML structure")
            return
        
        # Step 2: Upload to GCS
        blob_path = upload_to_gcs(BUCKET_NAME, data)
        
        # Step 3: Summary
        logger.info("="*60)
        logger.info("✅ UAP Scraper Pipeline Completed Successfully")
        logger.info(f"Sightings Collected: {data['sighting_count']}")
        logger.info(f"GCS Path: gs://{BUCKET_NAME}/{blob_path}")
        logger.info("="*60)
        
    except requests.RequestException as e:
        logger.error(f"❌ Network error during scraping: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ UAP scraper pipeline failed: {e}")
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
