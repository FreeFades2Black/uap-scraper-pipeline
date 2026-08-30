"""UAP Multi-Source Data Aggregator & Pipeline CLI.

Collects UAP sighting reports from 8+ sources and uploads to GCS or local staging.
Supports both CLI batch execution, scheduled CronJob, and Cloud Function triggers.
"""

import argparse
from datetime import datetime, timezone
import json
import logging
import os
import sys

from .config import config
from .orchestrator import MultiSourceOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("uap_scraper")


def save_locally(payload: dict, output_dir: str = "./data/output") -> str:
    """Save payload to local JSON file for staging, offline testing, or container volumes."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    local_path = os.path.join(output_dir, f"uap_sightings_{timestamp}.json")

    with open(local_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    logger.info(f"💾 Saved {payload.get('total_sightings', 0)} records locally to: {local_path}")
    return local_path


def upload_to_gcs(bucket_name: str, payload: dict) -> str:
    """Uploads scraped UAP data as JSON to Google Cloud Storage landing bucket."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    destination_blob_name = f"raw_ingest/uap_sightings_{timestamp}.json"

    logger.info(f"Uploading to gs://{bucket_name}/{destination_blob_name}...")

    try:
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)

        blob.upload_from_string(
            data=json.dumps(payload, indent=2),
            content_type="application/json"
        )

        logger.info(
            f"✅ Successfully uploaded {payload.get('total_sightings', 0)} sightings "
            f"to gs://{bucket_name}/{destination_blob_name}"
        )
        return destination_blob_name

    except Exception as e:
        logger.error(f"GCS upload failed ({e}). Falling back to local staging storage...")
        local_file = save_locally(payload, config.local_output_dir)
        return local_file


def run_pipeline(
    sources: list = None,
    parallel: bool = True,
    max_workers: int = 6,
    upload_gcs: bool = True,
    local_output: str = "./data/output"
) -> dict:
    """Run full collection pipeline with configured parameters."""
    logger.info("=" * 60)
    logger.info("🚀 Starting Multi-Source UAP Scraper Pipeline")
    logger.info(f"Target Bucket: gs://{config.gcs_raw_bucket}/raw_ingest/")
    logger.info("=" * 60)

    orchestrator = MultiSourceOrchestrator(sources=sources)
    data = orchestrator.collect_all(parallel=parallel, max_workers=max_workers)

    if data.get("total_sightings", 0) == 0:
        logger.warning("No sightings collected across all sources")
        return data

    # Storage output routing
    if upload_gcs and config.upload_to_gcs:
        try:
            blob_path = upload_to_gcs(config.gcs_raw_bucket, data)
            data["destination"] = f"gs://{config.gcs_raw_bucket}/{blob_path}"
        except Exception as err:
            logger.warning(f"GCS upload fallback: {err}")
            path = save_locally(data, local_output)
            data["destination"] = path
    else:
        path = save_locally(data, local_output)
        data["destination"] = path

    return data


def main():
    """CLI Entry point for container and command line execution."""
    parser = argparse.ArgumentParser(description="UAP Multi-Source Scraper & Ingestion Engine")
    parser.add_argument("--sources", nargs="+", default=["all"], help="Specific sources to scrape")
    parser.add_argument("--no-parallel", action="store_true", help="Run collectors sequentially")
    parser.add_argument("--workers", type=int, default=6, help="Max parallel worker threads")
    parser.add_argument("--local-only", action="store_true", help="Skip GCS upload and save to local disk only")
    parser.add_argument("--output-dir", default="./data/output", help="Local directory for JSON staging")
    parser.add_argument("--dry-run", action="store_true", help="Collect but do not upload to GCS")
    args = parser.parse_args()

    upload_gcs = not (args.local_only or args.dry_run)

    try:
        run_pipeline(
            sources=args.sources,
            parallel=not args.no_parallel,
            max_workers=args.workers,
            upload_gcs=upload_gcs,
            local_output=args.output_dir
        )
    except Exception as e:
        logger.error(f"Fatal pipeline error: {e}")
        sys.exit(1)


def cloud_function_entry(request):
    """Google Cloud Function Gen2 / Cloud Run HTTP Entrypoint."""
    try:
        result = run_pipeline(
            parallel=config.parallel_collection,
            max_workers=config.max_workers,
            upload_gcs=config.upload_to_gcs,
            local_output=config.local_output_dir
        )
        return (
            json.dumps({
                "status": "success",
                "total_sightings": result.get("total_sightings", 0),
                "successful_sources": result.get("successful_sources", 0),
                "duration_seconds": result.get("duration_seconds", 0),
                "destination": result.get("destination", "unknown")
            }),
            200,
            {"Content-Type": "application/json"}
        )
    except Exception as e:
        logger.error(f"Cloud Function execution failed: {e}")
        return (json.dumps({"status": "error", "message": str(e)}), 500, {"Content-Type": "application/json"})


if __name__ == "__main__":
    main()
