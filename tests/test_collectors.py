"""Unit tests for UAP data collectors."""

import pytest
from scraper.src.collectors.base import BaseCollector
from scraper.src.collectors.synthetic_collector import SyntheticCollector
from scraper.src.collectors.aaro_collector import AAROCollector
from scraper.src.collectors.nasa_collector import NASACollector
from scraper.src.collectors.kaggle_collector import KaggleCollector
from scraper.src.collectors.huggingface_collector import HuggingFaceCollector
from scraper.src.collectors.nuforc_collector import NUFORCCollector


class DummyCollector(BaseCollector):
    """Test collector implementation."""
    def __init__(self):
        super().__init__("Dummy")

    def collect(self):
        return {
            "source": "Dummy",
            "source_url": "http://dummy.local",
            "scraped_at": "2026-08-30T00:00:00Z",
            "sighting_count": 1,
            "sightings": [
                self.normalize_sighting({
                    "date_time": "2026-08-30 12:00",
                    "city": "austin",
                    "state": "tx",
                    "country": "usa",
                    "shape": "triangle",
                    "duration": "5 minutes",
                    "summary": "Bright triangular formation hovering silently."
                })
            ]
        }


def test_base_collector_normalization():
    """Verify BaseCollector normalization sanitizes and formats schema fields."""
    collector = DummyCollector()
    raw = {
        "datetime": "2026-08-30 14:00",
        "city": "san antonio",
        "state": "tx",
        "country": "usa",
        "shape": "disk",
        "duration (seconds)": "120",
        "comments": "Observed rapid acceleration."
    }
    normalized = collector.normalize_sighting(raw)

    assert normalized["city"] == "San Antonio"
    assert normalized["state"] == "TX"
    assert normalized["country"] == "USA"
    assert normalized["shape"] == "Disk"
    assert normalized["summary"] == "Observed rapid acceleration."
    assert normalized["date_time"] == "2026-08-30 14:00"


def test_safe_collect_wrapper():
    """Verify safe_collect catches errors and attaches latency metrics."""
    collector = DummyCollector()
    payload = collector.safe_collect()

    assert payload["source"] == "Dummy"
    assert payload["sighting_count"] == 1
    assert "latency_seconds" in payload
    assert payload["error"] is None


def test_synthetic_collector():
    """Verify SyntheticCollector generates expected payload matching schema."""
    collector = SyntheticCollector(count=15)
    payload = collector.safe_collect()

    assert payload["source"] == "Synthetic_Telemetry"
    assert payload["sighting_count"] == 15
    assert len(payload["sightings"]) == 15

    sample = payload["sightings"][0]
    assert "city" in sample
    assert "state" in sample
    assert "shape" in sample
    assert "date_time" in sample


def test_aaro_collector():
    """Verify AAROCollector returns official declassified records."""
    collector = AAROCollector()
    payload = collector.safe_collect()

    assert payload["source"] == "AARO_DoD"
    assert payload["sighting_count"] >= 3
    assert len(payload["sightings"]) >= 3


def test_nasa_collector():
    """Verify NASACollector returns reports or baseline study cases."""
    collector = NASACollector()
    payload = collector.safe_collect()

    assert payload["source"] == "NASA_UAP"
    assert payload["sighting_count"] >= 2
