"""UAP Scraper HTTP API Server for Kubernetes Deployments & Webhooks.

Provides:
- GET  /healthz : Kubernetes liveness/readiness probe
- GET  /readyz  : Kubernetes readiness probe
- GET  /metrics : Telemetry and scrape status metrics
- POST /scrape  : Trigger on-demand multi-source scraper job
- GET  /status  : System and collector status
"""

import json
import logging
import os
import time
from typing import Dict, List, Optional
from fastapi import FastAPI, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel, Field

from .config import config
from .main import run_pipeline

logger = logging.getLogger("uap_api")

app = FastAPI(
    title="UAP Multi-Source Scraper Service",
    description="Containerized High-Throughput UAP Data Ingestion & Lakehouse Pipeline API",
    version="2.0.0"
)

# Global in-memory metrics state
METRICS = {
    "start_time": time.time(),
    "total_runs": 0,
    "successful_runs": 0,
    "failed_runs": 0,
    "last_run_timestamp": None,
    "last_run_duration_seconds": 0.0,
    "last_total_sightings": 0,
    "last_successful_sources": 0,
    "is_scraping": False
}


class ScrapeRequest(BaseModel):
    sources: Optional[List[str]] = Field(default=["all"], description="List of sources or ['all']")
    parallel: Optional[bool] = Field(default=True, description="Run collectors concurrently")
    max_workers: Optional[int] = Field(default=6, description="Parallel thread worker count")
    upload_gcs: Optional[bool] = Field(default=False, description="Upload to GCS bucket")


class ScrapeResponse(BaseModel):
    status: str
    message: str
    total_sightings: Optional[int] = None
    successful_sources: Optional[int] = None
    duration_seconds: Optional[float] = None
    destination: Optional[str] = None
    timestamp: Optional[str] = None


@app.get("/healthz", tags=["Probes"])
def health_check():
    """Kubernetes Liveness Probe."""
    return {"status": "healthy", "uptime_seconds": round(time.time() - METRICS["start_time"], 2)}


@app.get("/readyz", tags=["Probes"])
def readiness_check():
    """Kubernetes Readiness Probe."""
    return {
        "status": "ready",
        "is_scraping": METRICS["is_scraping"],
        "target_bucket": config.gcs_raw_bucket
    }


@app.get("/metrics", tags=["Telemetry"])
def prometheus_metrics():
    """Prometheus-compatible plain text metrics."""
    uptime = time.time() - METRICS["start_time"]
    lines = [
        "# HELP uap_scraper_uptime_seconds Process uptime in seconds",
        "# TYPE uap_scraper_uptime_seconds gauge",
        f"uap_scraper_uptime_seconds {round(uptime, 2)}",
        "# HELP uap_scraper_total_runs Total number of scrape runs executed",
        "# TYPE uap_scraper_total_runs counter",
        f"uap_scraper_total_runs {METRICS['total_runs']}",
        "# HELP uap_scraper_successful_runs Total successful scrape runs",
        "# TYPE uap_scraper_successful_runs counter",
        f"uap_scraper_successful_runs {METRICS['successful_runs']}",
        "# HELP uap_scraper_last_sightings Number of sightings in most recent run",
        "# TYPE uap_scraper_last_sightings gauge",
        f"uap_scraper_last_sightings {METRICS['last_total_sightings']}",
        "# HELP uap_scraper_last_duration_seconds Duration of most recent run in seconds",
        "# TYPE uap_scraper_last_duration_seconds gauge",
        f"uap_scraper_last_duration_seconds {METRICS['last_run_duration_seconds']}"
    ]
    return "\n".join(lines)


@app.get("/status", tags=["Status"])
def system_status():
    """Detailed JSON telemetry status."""
    return {
        "metrics": METRICS,
        "config": {
            "gcs_raw_bucket": config.gcs_raw_bucket,
            "upload_to_gcs": config.upload_to_gcs,
            "parallel_collection": config.parallel_collection,
            "max_workers": config.max_workers,
            "local_output_dir": config.local_output_dir
        }
    }


def execute_scrape_task(req: ScrapeRequest):
    """Background task executor for scraping."""
    METRICS["is_scraping"] = True
    METRICS["total_runs"] += 1
    start_time = time.time()

    try:
        result = run_pipeline(
            sources=req.sources,
            parallel=req.parallel,
            max_workers=req.max_workers,
            upload_gcs=req.upload_gcs,
            local_output=config.local_output_dir
        )
        duration = round(time.time() - start_time, 3)

        METRICS["successful_runs"] += 1
        METRICS["last_run_timestamp"] = result.get("collection_timestamp")
        METRICS["last_run_duration_seconds"] = duration
        METRICS["last_total_sightings"] = result.get("total_sightings", 0)
        METRICS["last_successful_sources"] = result.get("successful_sources", 0)
        logger.info(f"Background scrape job completed: {METRICS['last_total_sightings']} sightings in {duration}s")
    except Exception as e:
        METRICS["failed_runs"] += 1
        logger.error(f"Background scrape job error: {e}")
    finally:
        METRICS["is_scraping"] = False


@app.post("/scrape", response_model=ScrapeResponse, tags=["Scraper"])
def trigger_scrape(request: ScrapeRequest, background: bool = Query(default=False)):
    """Trigger a multi-source UAP scrape job (sync or async background)."""
    if METRICS["is_scraping"]:
        raise HTTPException(status_code=409, detail="A scraping job is already running")

    if background:
        import threading
        thread = threading.Thread(target=execute_scrape_task, args=(request,))
        thread.start()
        return ScrapeResponse(
            status="accepted",
            message="Scraper job started in background",
            timestamp=str(time.time())
        )

    # Synchronous execution
    METRICS["is_scraping"] = True
    METRICS["total_runs"] += 1
    start_time = time.time()

    try:
        result = run_pipeline(
            sources=request.sources,
            parallel=request.parallel,
            max_workers=request.max_workers,
            upload_gcs=request.upload_gcs,
            local_output=config.local_output_dir
        )
        duration = round(time.time() - start_time, 3)

        METRICS["successful_runs"] += 1
        METRICS["last_run_timestamp"] = result.get("collection_timestamp")
        METRICS["last_run_duration_seconds"] = duration
        METRICS["last_total_sightings"] = result.get("total_sightings", 0)
        METRICS["last_successful_sources"] = result.get("successful_sources", 0)

        return ScrapeResponse(
            status="completed",
            message="Scraper job completed successfully",
            total_sightings=result.get("total_sightings", 0),
            successful_sources=result.get("successful_sources", 0),
            duration_seconds=duration,
            destination=result.get("destination"),
            timestamp=result.get("collection_timestamp")
        )
    except Exception as e:
        METRICS["failed_runs"] += 1
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        METRICS["is_scraping"] = False


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.api_host, port=config.api_port)
