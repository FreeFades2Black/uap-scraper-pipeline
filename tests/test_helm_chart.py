"""Validation tests for Helm Chart files and YAML structure."""

import os
import yaml
import pytest


CHART_DIR = os.path.join(os.path.dirname(__file__), "..", "charts", "uap-scraper")


def test_chart_yaml_exists_and_valid():
    """Verify Chart.yaml exists and is valid YAML."""
    chart_path = os.path.join(CHART_DIR, "Chart.yaml")
    assert os.path.exists(chart_path)

    with open(chart_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert data["name"] == "uap-scraper"
    assert data["apiVersion"] == "v2"
    assert "version" in data
    assert "appVersion" in data


def test_values_yaml_exists_and_valid():
    """Verify values.yaml exists and contains essential keys."""
    values_path = os.path.join(CHART_DIR, "values.yaml")
    assert os.path.exists(values_path)

    with open(values_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert "image" in data
    assert "cronjob" in data
    assert "deployment" in data
    assert "config" in data
    assert data["cronjob"]["schedule"] == "0 */6 * * *"


def test_templates_exist():
    """Verify standard Kubernetes templates exist in Helm chart."""
    templates_dir = os.path.join(CHART_DIR, "templates")
    assert os.path.exists(templates_dir)

    expected_templates = [
        "_helpers.tpl",
        "configmap.yaml",
        "cronjob.yaml",
        "deployment.yaml",
        "service.yaml",
        "serviceaccount.yaml"
    ]
    for tmpl in expected_templates:
        assert os.path.exists(os.path.join(templates_dir, tmpl))
