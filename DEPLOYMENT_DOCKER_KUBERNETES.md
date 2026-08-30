# 🛸 UAP Scraper Pipeline: Docker, Kubernetes & Helm Guide

Enterprise containerization, orchestration, and scheduling guide for the **UAP Multi-Source Scraper & Lakehouse Ingestion Engine**.

---

## 🏗️ Architecture Overview

```text
                                  ┌────────────────────────┐
                                  │  Multi-Source Scrapers │
                                  │  NUFORC / Kaggle / HF  │
                                  │  AARO / NASA / MUFON   │
                                  └───────────┬────────────┘
                                              │
                                              ▼
                        ┌──────────────────────────────────────────┐
                        │   MultiSourceOrchestrator (Parallel)     │
                        │   - Connection pooling & retries         │
                        │   - Content hashing deduplication (SHA)  │
                        │   - Latency & success rate telemetry     │
                        │   - Synthetic fallback circuit breaker   │
                        └─────────────┬──────────────┬─────────────┘
                                      │              │
                                      ▼              ▼
           ┌────────────────────────────┐          ┌───────────────────────────┐
           │   Kubernetes Scheduled     │          │    FastAPI Webhook / API  │
           │   CronJob (every 6 hours)  │          │    Daemon (:8080)         │
           │   `batch/v1 CronJob`       │          │    /healthz, /readyz,     │
           │                            │          │    /metrics, /scrape      │
           └──────────────┬─────────────┘          └─────────────┬─────────────┘
                          │                                      │
                          └──────────────────┬───────────────────┘
                                             │
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │    GCS Ingestion Bucket / Local Volume       │
                      │    `gs://.../raw_ingest/uap_*.json`          │
                      └──────────────────────┬───────────────────────┘
                                             │
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │    Databricks Medallion Lakehouse (Delta)    │
                      │    Bronze Raw ➔ Silver Transformed ➔ Gold    │
                      └──────────────────────────────────────────────┘
```

---

## 🐳 1. Docker & Docker Compose

### Building the Production Container Image
```bash
# Build multi-stage optimized image
docker build -t ghcr.io/freefades2black/uap-scraper:latest .
```

### Running with Docker CLI
```bash
# 1. Run Scraper API Server Daemon with healthcheck
docker run -d --name uap-api -p 8080:8080 \
  -e UPLOAD_TO_GCS=false \
  ghcr.io/freefades2black/uap-scraper:latest api

# 2. Run a One-Shot Scrape Job
docker run --rm \
  -v $(pwd)/data/output:/app/data/output \
  ghcr.io/freefades2black/uap-scraper:latest scrape --local-only

# 3. Check health
curl http://localhost:8080/healthz
```

### Running with Docker Compose
```bash
# Start API service, periodic scraper daemon, and local MinIO storage emulator
docker compose up -d

# View real-time logs
docker compose logs -f uap-scraper-api
```

---

## ☸️ 2. Kubernetes Deployment (Raw Manifests)

The repository provides an all-in-one manifest in `k8s/all-in-one.yaml`:

```bash
# Deploy Namespace, ConfigMap, Service, Deployment, and CronJob
kubectl apply -f k8s/all-in-one.yaml

# Check deployed resources
kubectl get all -n uap-pipeline

# Trigger immediate test scrape job from the CronJob
kubectl create job --from=cronjob/uap-scraper-cronjob manual-scrape-001 -n uap-pipeline

# Inspect scraper job logs
kubectl logs -n uap-pipeline job/manual-scrape-001 -f
```

---

## ⛵ 3. Helm Chart Deployment

A production-grade Helm chart is located in `charts/uap-scraper/`.

### Install Chart
```bash
# 1. Lint the Helm chart
helm lint charts/uap-scraper/

# 2. Install with default settings (CronJob + API Deployment)
helm install uap-scraper ./charts/uap-scraper \
  --namespace uap-pipeline \
  --create-namespace

# 3. Install with Custom GCS Bucket & GCP Service Account Secret
helm install uap-scraper ./charts/uap-scraper \
  --namespace uap-pipeline \
  --set config.gcsRawBucket="my-production-uap-raw-bucket" \
  --set config.uploadToGcs="true" \
  --set secrets.create=true \
  --set secrets.gcpServiceAccountKeyJson="$(cat /path/to/gcp-key.json)"
```

### Customize Values
| Key | Default | Description |
| :--- | :--- | :--- |
| `cronjob.enabled` | `true` | Enables scheduled scraping CronJob |
| `cronjob.schedule` | `"0 */6 * * *"` | Scrape execution schedule (Cron syntax) |
| `deployment.enabled` | `true` | Enables persistent FastAPI scraper daemon |
| `config.parallelCollection` | `"true"` | Run multi-source collectors concurrently |
| `config.maxWorkers` | `"6"` | Parallel worker thread pool size |
| `config.enableSyntheticFallback` | `"true"` | Fallback to synthetic generation if all network scrapers block |
| `resources.requests.cpu` | `250m` | Kubernetes CPU request |
| `resources.requests.memory` | `512Mi` | Kubernetes Memory request |

---

## 🧪 4. Running the Automated Test Suite

```bash
# Run 17 unit, integration, and Helm chart validation tests
PYTHONPATH=. pytest -v
```
