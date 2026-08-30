# 🛸 UAP Sightings Data Lakehouse & Scraper Pipeline

**High-Throughput Multi-Source UAP (Unidentified Aerial Phenomena) Data Aggregator, Containerized Orchestrator & End-to-End Lakehouse Analytics**

Automated pipeline collecting UAP sighting data from 8+ open-source repositories and government declassified feeds, processing through medallion architecture, and delivering analytics-ready tables in Databricks Unity Catalog.

[![Live Interactive Dashboard](https://img.shields.io/badge/Live%20Dashboard-GitHub%20Pages-00bcd4?style=for-the-badge&logo=googlechrome)](https://freefades2black.github.io/uap-scraper-pipeline/)
[![Medallion Status](https://img.shields.io/badge/Medallion%20Pipeline-100%25%20Zero--Stall-brightgreen?style=for-the-badge&logo=apachespark)](https://github.com/FreeFades2Black/uap-scraper-pipeline/blob/main/REPORTS/MEDALLION_ANALYTICS_REPORT.md)
[![Docker](https://img.shields.io/badge/Docker-Multi--Stage%20Container-blue?style=for-the-badge&logo=docker)](https://github.com/FreeFades2Black/uap-scraper-pipeline/blob/main/Dockerfile)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Helm%20Chart-326ce5?style=for-the-badge&logo=kubernetes)](https://github.com/FreeFades2Black/uap-scraper-pipeline/tree/main/charts/uap-scraper)

---

## 📑 Latest UAP Intelligence & Sighting Reports

Below is the verified multi-source intelligence ledger ingested directly by the pipeline, complete with exact **dates, timestamps, locations, phenomenon shapes, summaries, and official citations/references**:

### 🛡️ 1. Official Government & Military Declassified Sensor Telemetry

| Date & Time (UTC) | Case Title / Unit | Location | Shape / Morphology | Duration | Summary & Sensor Telemetry | Source & Reference Citation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`2023-01-18`** | **MQ-9 Reaper EO/IR Sensor Capture** | CENTCOM Operating Area | Silver / Metallic Orb | `15 sec` | MQ-9 Reaper Electro-Optical/Infrared (EO/IR) gimbal sensor capture of a high-velocity spherical anomaly with zero thermal exhaust signature. | [AARO DoD Case Reference](https://www.aaro.mil/UAP-Cases/Middle-East-MQ9/) |
| **`2015-01-20`** | **USS Theodore Roosevelt Strike Group (Gimbal / GoFast)** | Jacksonville Coast, FL | Sphere within Translucent Cube | `Radar & ATFLIR Track` | Dual-sensor ATFLIR optical and radar lock exhibiting rotational velocity and adverse-wind transit with no aerodynamic surfaces or propulsion plume. | [AARO DoD Gimbal Case](https://www.aaro.mil/UAP-Cases/GoFast-Gimbal/) |
| **`2004-11-14`** | **USS Nimitz Carrier Strike Group (FLIR1 Intercept)** | San Diego Coast, CA | Tic-Tac / White Oblong | `Multiple Intercepts` | SPY-1 radar cueing and F/A-18F Super Hornet visual/FLIR1 tracking of anomalous aerial vehicle exhibiting instantaneous kinematic acceleration from 80,000 ft to sea level. | [AARO DoD FLIR1 Case](https://www.aaro.mil/UAP-Cases/Nimitz-FLIR1/) |

---

### 🛰️ 2. NASA Scientific Study Directorate Evaluations

| Date (UTC) | Case / Study Title | Location | Phenomenon Category | Scope | Research Summary | Official Reference |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`2024-05-20`** | **NASA Earth Science Multi-Sensor Data Analytics** | Houston, TX | High-Altitude Sensor Anomaly | `Sensor Stream` | Calibration of satellite and airborne sensor telemetry for anomalous atmospheric phenomena classification. | [NASA Science Directorate](https://science.nasa.gov/uap) |
| **`2023-09-14`** | **NASA UAP Independent Study Team Final Report** | Washington, DC | Spherical / Metallic Orb | `Study Finding` | Evaluation of multi-sensor civilian/commercial satellite data and roadmap for rigorous scientific measurement. | [NASA UAP Report](https://science.nasa.gov/uap/report) |

---

### 🌐 3. Representative Public & Historical Ingestion Records

| Sighting Date & Time | Location | State / Country | Shape | Duration | Witness Observation Summary | Data Archive Reference |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`10/10/1949 20:30`** | San Marcos | Texas, USA | Cylinder | `45 minutes` | Observed cylindrical craft hovering above church tree line following Boy Scout assembly; accelerated silently toward horizon. | [TidyTuesday / NUFORC Archive](https://github.com/rfordatascience/tidytuesday/tree/master/data/2019/2019-06-25) |
| **`10/10/1949 21:00`** | Lackland AFB | Texas, USA | Light | `1-2 hours` | Lights observed racing across military airspace performing 90-degree right-angle turns at high velocity. | [Kaggle Historical Dataset](https://www.kaggle.com/datasets/NUFORC_reports) |
| **`10/10/1955 17:00`** | Chester | Cheshire, UK | Circle | `20 seconds` | Disc-shaped circular craft descending from cloud cover and hovering before rapid climb. | [TidyTuesday / NUFORC Archive](https://github.com/rfordatascience/tidytuesday/tree/master/data/2019/2019-06-25) |
| **`10/10/1956 21:00`** | Edna | Texas, USA | Circle | `20 seconds` | Luminous circular object flying low with silent propulsion over pasture terrain. | [Kaggle Historical Dataset](https://www.kaggle.com/datasets/NUFORC_reports) |
| **`10/10/1960 20:00`** | Kaneohe | Hawaii, USA | Light | `10 minutes` | Glowing light moving slowly across coastal ridgeline then rapidly accelerating out to sea. | [TidyTuesday / NUFORC Archive](https://github.com/rfordatascience/tidytuesday/tree/master/data/2019/2019-06-25) |
| **`10/10/1965 23:45`** | Norwalk | Connecticut, USA | Disk | `15 minutes` | Disk-shaped craft with rotating perimeter lighting observed above residential tree canopy. | [Kaggle Historical Dataset](https://www.kaggle.com/datasets/NUFORC_reports) |
| **`10/10/1968 13:00`** | Detroit | Michigan, USA | Chevron | `10 minutes` | Triangular / chevron wing formation flying in perfect synchronization during daylight hours. | [TidyTuesday / NUFORC Archive](https://github.com/rfordatascience/tidytuesday/tree/master/data/2019/2019-06-25) |
| **`10/10/1970 19:00`** | New York City | New York, USA | Sphere | `180 seconds` | Metallic sphere reflecting sunset light hovering stationary near Manhattan skyline. | [Kaggle Historical Dataset](https://www.kaggle.com/datasets/NUFORC_reports) |

> 📊 **Explore All 1,005 Live Plotted Records:** Visit the [**Live Geospatial & Shape Analytics Dashboard**](https://freefades2black.github.io/uap-scraper-pipeline/) to filter by city, state, date, and shape on an interactive map.

---

## ⚡ What's New in v2.0.0

- 🐳 **Docker & Docker Compose Containerization:** Multi-stage production container with non-root security context (`uapuser:10001`), health checks, and compose orchestration for API, scheduled daemon, and MinIO storage.
- ☸️ **Kubernetes Orchestration:** Native `batch/v1 CronJob` (for scheduled periodic ingestion) and `apps/v1 Deployment` (for on-demand webhook scraper).
- ⛵ **Enterprise Helm Chart (`charts/uap-scraper`):** Complete Helm chart with configurable CronJob schedules, HPA, PodDisruptionBudget, and Workload Identity secrets.
- 🚀 **High-Throughput Parallel Ingestion:** Concurrent `ThreadPoolExecutor` fetching across Kaggle, HuggingFace, NUFORC, AARO DoD, NASA Science, MUFON, and UFOStalker with SHA-256 deduplication and telemetry metrics.
- 🛰️ **FastAPI Service Daemon:** HTTP microservice exposing `/healthz`, `/readyz`, `/metrics` (Prometheus), and `/scrape` endpoints.
- 🧪 **Automated Test Suite:** 17 unit, integration, and Helm validation tests in `tests/`.

---

## 🏗️ System Architecture

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        🌐 Multi-Source Ingestion Engine (Python 3.11)                  │
│  Collectors: Kaggle, Hugging Face, NUFORC, AARO (DoD), NASA Science, MUFON, UFOStalker │
│  Orchestrator: Connection pooling, retry backoff, SHA-256 deduplication, telemetry     │
│  Resilience: Synthetic telemetry fallback circuit breaker for zero-drop lakehouse runs │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                  🐳 Container & Orchestration Execution Options                        │
│  1. Kubernetes Scheduled CronJob: `batch/v1 CronJob` (every 6 hours)                  │
│  2. Kubernetes Persistent Service: `apps/v1 Deployment` (FastAPI /metrics & webhook)   │
│  3. Docker Compose: API + Cron + Local MinIO Landing Emulator                          │
│  4. Serverless Cloud Function: Gen2 HTTP Trigger                                       │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               Google Cloud Storage (GCS)                               │
│  Format: gs://uap-scraper-lab-2026-scraper-raw/raw_ingest/uap_sightings_*.json         │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                          Databricks Medallion Lakehouse                                │
│  🥉 Bronze: workspace.default.bronze_uap_raw (Raw JSON & metadata)                     │
│  🥈 Silver: workspace.default.silver_uap_structured (Standardized location & shapes)   │
│  🥇 Gold:   workspace.default.gold_uap_* (Timeline, Location, and Quality Analytics)   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📂 Project Structure

```text
uap-scraper-pipeline/
├── Dockerfile                         # Production multi-stage container build
├── docker-compose.yml                 # Multi-container local orchestration
├── entrypoint.sh                      # Multi-mode entrypoint (api, scrape, cron, test)
├── requirements.txt                   # Root Python dependencies & testing tools
├── DEPLOYMENT_DOCKER_KUBERNETES.md    # Detailed Docker, K8s & Helm deployment guide
├── DASHBOARD.md                       # Dashboard SQL queries & visualizations
├── charts/                            # Production Helm Chart
│   └── uap-scraper/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/                 # CronJob, Deployment, Service, ConfigMap, PDB, HPA
├── docs/                              # Live GitHub Pages web dashboard
│   ├── index.html                     # Interactive Leaflet map & Chart.js visualizer
│   └── data.json                      # Ingested multi-source sighting dataset
├── k8s/                               # Raw standalone Kubernetes manifests
│   └── all-in-one.yaml
├── REPORTS/                           # Intelligence briefs
│   └── MEDALLION_ANALYTICS_REPORT.md  # 3-tier Medallion lakehouse report
├── scraper/                           # Scraper engine source tree
│   ├── Dockerfile
│   ├── requirements.txt
│   └── src/
│       ├── api.py                     # FastAPI server with Prometheus metrics & /healthz
│       ├── config.py                  # Centralized configuration dataclass
│       ├── main.py                    # Multi-source CLI & Cloud Function entrypoint
│       ├── orchestrator.py            # Parallel runner, deduplicator & telemetry
│       ├── uap_test_data.py           # Schema generator & test dataset
│       └── collectors/                # Specialized source collectors
│           ├── base.py                # Base collector (connection pool, retries, headers)
│           ├── aaro_collector.py      # DoD All-domain Anomaly Resolution Office
│           ├── huggingface_collector.py # HF UFOCR declassified datasets
│           ├── kaggle_collector.py    # Kaggle API + verified high-speed mirrors
│           ├── mufon_collector.py     # MUFON public feeds
│           ├── nasa_collector.py      # NASA Science UAP study
│           ├── nuforc_collector.py    # NUFORC web scraping
│           ├── ufostalker_collector.py# UFO Stalker geolocation database
│           └── synthetic_collector.py # Resilient fallback generator
├── tests/                             # Comprehensive Pytest suite (17 tests)
│   ├── test_api.py
│   ├── test_collectors.py
│   ├── test_helm_chart.py
│   └── test_orchestrator.py
└── notebooks/                         # Databricks Lakehouse processing notebooks
    ├── 01_bronze_ingestion.py
    ├── 02_silver_transformation.py
    └── 03_gold_summary.py
```

---

## 🚀 Quickstart & Commands

### 1. Local CLI Execution
```bash
# Run one-shot multi-source scrape and save locally
python -m scraper.src.main --local-only --output-dir ./data/output

# Run with specific sources and custom thread concurrency
python -m scraper.src.main --sources aaro_dod nasa_uap --workers 4 --local-only
```

### 2. Run Automated Pytest Suite
```bash
PYTHONPATH=. pytest -v
```

### 3. Docker & Docker Compose
```bash
# Start API daemon, scheduled cron scraper, and MinIO storage emulator
docker compose up -d

# Trigger scrape via API endpoint
curl -X POST http://localhost:8080/scrape \
  -H "Content-Type: application/json" \
  -d '{"sources": ["all"], "upload_gcs": false}'
```

### 4. Kubernetes Deployment
```bash
# Apply raw Kubernetes manifests (Namespace, ConfigMap, Service, Deployment, CronJob)
kubectl apply -f k8s/all-in-one.yaml

# Or install via Helm chart
helm install uap-scraper ./charts/uap-scraper --namespace uap-pipeline --create-namespace
```

---

## 🔒 Security & Governance

- **Least Privilege:** Containers run under dedicated non-root user `uapuser` (`UID 10001`).
- **GCP Workload Identity:** Fully compatible with Kubernetes ServiceAccount annotations for zero-secret cloud authentication.
- **Unity Catalog Volumes:** Databricks notebooks authenticate securely via volume-mounted keys (`/Volumes/workspace/default/configs/gcp-key.json`).

---

**Maintained by:** [FreeFades2Black](https://github.com/FreeFades2Black)  
**Version:** 2.0.0  
**License:** Apache-2.0
