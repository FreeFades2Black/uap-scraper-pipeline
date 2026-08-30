"""Unit tests for MultiSourceOrchestrator."""

import pytest
from scraper.src.orchestrator import MultiSourceOrchestrator


def test_orchestrator_initialization():
    """Verify orchestrator loads active collectors."""
    orchestrator = MultiSourceOrchestrator()
    assert len(orchestrator.collectors) > 0


def test_orchestrator_source_filtering():
    """Verify source filtering allows selecting specific collectors."""
    orchestrator = MultiSourceOrchestrator(sources=["aaro_dod", "nasa_uap"])
    names = [c.name.lower() for c in orchestrator.collectors]
    assert "aaro_dod" in names
    assert "nasa_uap" in names


def test_orchestrator_deduplication():
    """Verify deduplication removes duplicate records based on content hash."""
    orchestrator = MultiSourceOrchestrator()
    sample_sighting = {
        "date_time": "2026-08-30 12:00",
        "city": "Dallas",
        "state": "TX",
        "shape": "Sphere",
        "summary": "Dual metallic spheres in unison"
    }
    hash1 = orchestrator._generate_sighting_id(sample_sighting)
    hash2 = orchestrator._generate_sighting_id(sample_sighting)
    assert hash1 == hash2


def test_orchestrator_collection_execution():
    """Verify full orchestrator collection workflow and consolidation."""
    orchestrator = MultiSourceOrchestrator(sources=["aaro_dod", "nasa_uap"])
    payload = orchestrator.collect_all(parallel=True, max_workers=2)

    assert "collection_timestamp" in payload
    assert "total_sightings" in payload
    assert payload["total_sightings"] > 0
    assert "source_breakdown" in payload
    assert "duration_seconds" in payload
    assert len(payload["all_sightings"]) == payload["total_sightings"]
