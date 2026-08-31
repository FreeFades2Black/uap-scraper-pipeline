"""Unit tests for Ancient & Historical UAP Chronology Collector."""

from scraper.src.collectors.ancient_and_historical_chronology_collector import AncientHistoricalChronologyCollector


def test_ancient_collector_initialization():
    """Verify collector initializes with standard metadata."""
    collector = AncientHistoricalChronologyCollector()
    assert collector.name == "ancient_historical_chronology"
    assert collector.timeout == 15


def test_ancient_collector_payload_structure():
    """Verify collect() returns standardized payload dictionary."""
    collector = AncientHistoricalChronologyCollector()
    payload = collector.collect()
    assert isinstance(payload, dict)
    assert payload["source"] == "ancient_historical_chronology"
    assert "sightings" in payload
    assert payload["sighting_count"] >= 15


def test_roswell_records_present():
    """Verify Roswell 1947 crash and debris retrieval records are present."""
    collector = AncientHistoricalChronologyCollector()
    records = collector.scrape()
    roswell_records = [r for r in records if "Roswell" in r.get("title", "") or "Roswell" in r.get("city", "")]
    assert len(roswell_records) >= 2
    for r in roswell_records:
        assert r["state"] == "NM"
        assert r["country"] == "USA"
        assert r["latitude"] != 0
        assert r["longitude"] != 0


def test_ancient_civilizations_coverage():
    """Verify coverage across Ancient Rome, Greece, Egypt, Mesopotamia, Inca, and Maya."""
    collector = AncientHistoricalChronologyCollector()
    records = collector.scrape()
    civilizations = {r.get("civilization_era") for r in records}
    assert any("Roman" in c or "Rome" in c for c in civilizations if c)
    assert any("Greece" in c or "Greek" in c for c in civilizations if c)
    assert any("Egypt" in c for c in civilizations if c)
    assert any("Mesopotamia" in c or "Sumer" in c for c in civilizations if c)
    assert any("Maya" in c for c in civilizations if c)
    assert any("Tiwanaku" in c or "Andean" in c or "Nazca" in c or "Inca" in c for c in civilizations if c)

