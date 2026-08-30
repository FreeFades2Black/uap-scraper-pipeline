"""Unit tests for Global Sensor Mesh Collector."""

import pytest
from unittest.mock import patch, MagicMock
from scraper.src.collectors.global_sensor_mesh_collector import GlobalSensorMeshCollector


@pytest.fixture
def collector():
    return GlobalSensorMeshCollector(timeout=5)


def test_sensor_mesh_collector_init(collector):
    assert collector.name == "sensor_mesh"
    assert "celestrak.org" in collector.source_url


def test_sensor_mesh_collect_safe(collector):
    payload = collector.safe_collect()
    assert payload["source"] == "sensor_mesh"
    assert "sighting_count" in payload
    assert isinstance(payload["sightings"], list)
    assert payload["sighting_count"] >= 1
    assert payload["error"] is None


def test_sensor_mesh_schema_fields(collector):
    payload = collector.safe_collect()
    for record in payload["sightings"]:
        assert "sighting_id" in record
        assert "occurred_at" in record
        assert "city" in record
        assert "shape" in record
        assert "summary" in record
        assert "sensor_type" in record
        assert "confidence_score" in record
