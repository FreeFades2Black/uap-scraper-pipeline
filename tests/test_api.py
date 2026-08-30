"""Integration tests for UAP Scraper FastAPI service."""

import pytest
from fastapi.testclient import TestClient
from scraper.src.api import app


@pytest.fixture
def client():
    """Create test client fixture."""
    return TestClient(app)


def test_healthz_endpoint(client):
    """Test /healthz liveness probe."""
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "uptime_seconds" in data


def test_readyz_endpoint(client):
    """Test /readyz readiness probe."""
    response = client.get("/readyz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "target_bucket" in data


def test_status_endpoint(client):
    """Test /status system telemetry endpoint."""
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "config" in data


def test_prometheus_metrics_endpoint(client):
    """Test /metrics endpoint plain text response."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "uap_scraper_uptime_seconds" in response.text
    assert "uap_scraper_total_runs" in response.text


def test_scrape_endpoint(client):
    """Test /scrape synchronous execution with selected lightweight source."""
    response = client.post(
        "/scrape",
        json={"sources": ["aaro_dod"], "parallel": False, "upload_gcs": False}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["total_sightings"] > 0
