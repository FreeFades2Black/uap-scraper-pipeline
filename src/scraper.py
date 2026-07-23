import json
import os
from datetime import datetime, timezone
import requests
from google.cloud import storage

# Configuration
BUCKET_NAME = os.getenv("GCS_RAW_BUCKET", "uap-scraper-lab-2026-scraper-raw")
TARGET_URL = os.getenv("TARGET_URL", "https://api.github.com/events") # Default lab endpoint

def fetch_payload(url: str) -> dict:
    """Fetches raw data from the target endpoint."""
    print(f"Fetching data from {url}...")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()

def upload_to_gcs(bucket_name: str, payload: dict) -> str:
    """Uploads raw payload as JSON to GCS landing bucket."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    destination_blob_name = f"raw_ingest/ingest_{timestamp}.json"

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_string(
        data=json.dumps(payload, indent=2),
        content_type="application/json"
    )

    print(f"Successfully uploaded payload to gs://{bucket_name}/{destination_blob_name}")
    return destination_blob_name

def main():
    try:
        data = fetch_payload(TARGET_URL)
        blob_path = upload_to_gcs(BUCKET_NAME, data)
        print("Scraper execution completed successfully.")
    except Exception as e:
        print(f"Scraper execution failed: {e}")
        raise e

if __name__ == "__main__":
    main()
