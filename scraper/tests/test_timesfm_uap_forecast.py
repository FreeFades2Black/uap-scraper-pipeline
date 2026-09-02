"""
UAP Sightings Data Lakehouse & Scraper Pipeline
Test Suite for TimesFM-3 UAP Forecast Module
"""

import pytest
from scraper.src.timesfm_uap_forecast import TimesFM3UAPForecaster


def test_timesfm_uap_forecaster_execution():
    """Verify TimesFM-3 generates multi-year predictions for aerospace anomalies."""
    forecaster = TimesFM3UAPForecaster()
    dossier = forecaster.predict_future_sighting_waves()

    assert "model_metadata" in dossier
    assert len(dossier["longitudinal_forecast_timeline"]) == 5
    assert len(dossier["regional_corridor_projections"]) >= 5

    # Verify forecast bounds (P10 <= P50 <= P90)
    for period in dossier["longitudinal_forecast_timeline"]:
        p10 = period["confidence_lower_bound_p10"]
        p50 = period["projected_annual_sightings_p50"]
        p90 = period["confidence_upper_bound_p90"]
        assert p10 <= p50 <= p90
        assert p50 > 1000
