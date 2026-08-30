# 🛸 UAP Sightings Data Lakehouse & Scraper Pipeline

**High-Throughput Multi-Source UAP (Unidentified Aerial Phenomena) Data Aggregator, Containerized Orchestrator & End-to-End Lakehouse Analytics**

Automated pipeline collecting UAP sighting data from 8+ open-source repositories and government feeds, processing through medallion architecture, and delivering analytics-ready tables in Databricks Unity Catalog.

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
├── k8s/                               # Raw standalone Kubernetes manifests
│   └── all-in-one.yaml
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
