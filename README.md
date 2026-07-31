# 🛸 UAP Sightings Data Lakehouse

**Multi-source UAP (Unidentified Aerial Phenomena) data aggregator with end-to-end lakehouse analytics**

Automated pipeline collecting UAP sighting data from 10+ open-source repositories, processing through medallion architecture, and delivering analytics-ready tables in Databricks Unity Catalog.

## 🏗️ Architecture

This project implements a **medallion architecture** (Bronze → Silver → Gold) for processing UAP sighting data from 10+ public sources through Google Cloud Storage (GCS) into analytics-ready tables.

### 🎯 Data Sources

**Currently Implemented:**
* **Kaggle** - Structured NUFORC CSV datasets (~80K+ historical sightings)
* **Hugging Face** - FBI/DoD declassified records (via `reducto/ufocr`)
* **NUFORC** - National UFO Reporting Center web scraping

**Planned Integration:**
* MUFON (Mutual UFO Network)
* NASA UAP Independent Study reports
* AARO (All-domain Anomaly Resolution Office)
* Black Vault FOIA documents
* NARA declassified files
* UFO Stalker mapping database
* CUFOS archives

```
┌─────────────────────────────────────────────────────────────────┐
│              🌐 Multi-Source Scraper (Cloud Function)            │
│  Collectors: Kaggle, NUFORC, HuggingFace, MUFON, NASA, etc.    │
│  Orchestrator: Parallel execution with fault tolerance          │
│  Output: Consolidated JSON with unified schema                  │
│  Location: scraper/ (Python 3.11, GCP Cloud Functions Gen2)    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Google Cloud Storage (GCS)                    │
│  Buckets: uap-scraper-lab-2026-lakehouse-data (staging)        │
│           uap-scraper-lab-2026-scraper-raw (raw JSON)           │
│  Format: raw_ingest/uap_sightings_YYYYMMDD_HHMMSS.json         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  🥉 Bronze Layer (Raw Data)                      │
│  Table: workspace.default.bronze_uap_raw                        │
│  - Raw JSON UAP sighting records from GCS                       │
│  - Preserves source structure and metadata                      │
│  - Tracks data_source field (Kaggle, NUFORC, etc.)             │
│  Notebook: 01_bronze_ingestion.py                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│               🥈 Silver Layer (Structured Data)                  │
│  Table: workspace.default.silver_uap_structured                 │
│  - Parsed date/time, location (city, state, country)           │
│  - Standardized shape, duration fields                          │
│  - Quality flags and data validation                            │
│  - Geocoding and temporal normalization                         │
│  Notebook: 02_silver_transformation.py                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              🥇 Gold Layer (Analytics Tables)                    │
│  Tables:                                                         │
│  1. workspace.default.gold_uap_by_location                      │
│     → Sightings aggregated by state/country                     │
│  2. workspace.default.gold_uap_by_shape                         │
│     → Sightings aggregated by object shape                      │
│  3. workspace.default.gold_uap_timeline                         │
│     → Historical trends and temporal patterns                   │
│  4. workspace.default.gold_uap_by_source                        │
│     → Data quality metrics per collection source                │
│  Notebook: 03_gold_summary.py                                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   📊 Analytics Dashboard                         │
│  UAP Sightings Analytics (Lakeview)                             │
│  - Temporal trends, geographic heatmaps, shape distribution     │
│  - Source reliability metrics, data quality indicators          │
│  - Published URL with shared access                             │
└─────────────────────────────────────────────────────────────────┘
```

## 📂 Project Structure

```
uap-scraper-pipeline/
├── README.md                          # This file
├── DASHBOARD.md                       # Dashboard configuration and SQL queries
├── notebooks/
│   ├── 01_bronze_ingestion.py         # GCS → Bronze layer ingestion
│   ├── 02_silver_transformation.py    # Bronze → Silver transformation
│   └── 03_gold_summary.py             # Silver → Gold aggregations
├── scraper/                           # Source scraper code
├── terraform/                         # Infrastructure as code
└── .git/                              # Git repository
```

## 🚀 Getting Started

### Prerequisites

1. **Databricks Workspace** with Unity Catalog enabled
2. **Google Cloud Storage** with GitHub events data
3. **GCP Service Account Key** for GCS authentication
4. **Serverless SQL Warehouse** (or provisioned warehouse)

### Setup

#### 1. Configure GCS Access

Upload your GCP service account key to Unity Catalog Volume:

```python
# Key stored at: /Volumes/workspace/default/configs/gcp-key.json
```

The notebooks use the Python GCS client (workaround for Databricks Serverless limitations on Spark GCS connectors).

#### 2. Run the Pipeline

Execute the notebooks in order:

##### Bronze Ingestion
```bash
# Run: notebooks/01_bronze_ingestion.py
# Cells: 2 (Config), 3 (Batch), 4 (Incremental), 6 (Verify)
# Output: workspace.default.bronze_uap_raw
# Records: ~80K+ UAP sightings from all sources
```

##### Silver Transformation
```bash
# Run: notebooks/02_silver_transformation.py
# Parses date/time, location, shape, duration fields
# Standardizes across different source formats
# Output: workspace.default.silver_uap_structured
# Fields: date_time, city, state, country, shape, duration, summary, data_source
```

##### Gold Aggregations
```bash
# Run: notebooks/03_gold_summary.py
# Creates analytics tables:
#   - By location (state/country aggregates)
#   - By shape (object type distribution)
#   - Timeline (historical trends)
#   - By source (data quality per collector)
```

#### 3. View the Dashboard

Open the Databricks workspace to explore UAP analytics:

**Databricks Workspace:** https://dbc-3e95d032-684c.cloud.databricks.com

Dashboards can be built from the gold tables to visualize:
* Geographic heatmaps of sightings
* Temporal trends (decades of data)
* Shape distribution analysis
* Data source reliability metrics

## 📊 Data Metrics

Current pipeline status (as of 2026-07-30):

| Metric | Value |
|--------|-------|
| **Total Events** | 91 |
| **Unique Actors** | 90 |
| **Unique Repositories** | 90 |
| **Unique Organizations** | 5 |
| **Event Types** | 3 (PushEvent, CreateEvent, etc.) |
| **Data Completeness** | 98.9% |
| **Date Range** | July 23-30, 2026 (7 days) |

## 🛠️ Technical Details

### Storage

- **Bronze/Silver/Gold Tables:** Unity Catalog (`workspace.default.*`)
- **Staging Files:** Unity Catalog Volume (`/Volumes/workspace/default/staging/`)
- **Credentials:** Unity Catalog Volume (`/Volumes/workspace/default/configs/`)
- **Source Data:** Google Cloud Storage (2 buckets)

### Compute

- **Serverless SQL Warehouse** for all notebooks and dashboard queries
- No cluster configuration required
- Auto-scaling and optimized query execution

### Data Processing

#### Bronze → Silver
- Parse and normalize date/time formats across sources
- Standardize location fields (city, state, country)
- Validate and categorize shape descriptors
- Extract duration in consistent units
- Add data_source tracking field
- Quality flags and validation checks

#### Silver → Gold
- Aggregate by location (state/country heatmaps)
- Aggregate by shape (object type patterns)
- Time-series aggregation (decades of trends)
- Source reliability metrics
- Data quality KPIs per collector

## 🔄 Incremental Updates

The bronze ingestion notebook supports both **batch** and **incremental** modes:

- **Batch Mode:** Full reload from GCS
- **Incremental Mode:** Process only new files using Auto Loader patterns
- **Checkpointing:** Track processed files to avoid duplicates

## 📈 Dashboard Visualizations

The analytics dashboard includes:

1. **KPI Cards** - Total events, contributors, repos, data quality
2. **Top Contributors** - Bar chart of most active GitHub users
3. **Top Repositories** - Bar chart of most active repos
4. **Daily Timeline** - Line chart showing event trends over time
5. **Event Distribution** - Pie chart of public vs organization events

All queries use pre-aggregated gold tables for fast performance.

## 🔒 Security & Compliance

- **Unity Catalog Volumes** for secure file storage (no DBFS root)
- **GCP Service Account Key** stored in encrypted volume
- **Unity Catalog Governance** enforces table-level access control
- **Public Data Only** - All sources are open-source UAP repositories
- **No PII** - Sighting reports contain no personal information

## 🤝 Contributing

This is a personal project. For questions or suggestions, contact the repository owner.

## 📝 License

[Add your license information here]

## 🔗 Resources

- **Databricks Lakehouse:** https://www.databricks.com/product/data-lakehouse
- **Unity Catalog:** https://docs.databricks.com/data-governance/unity-catalog/
- **Medallion Architecture:** https://www.databricks.com/glossary/medallion-architecture
- **Lakeview Dashboards:** https://docs.databricks.com/dashboards/

---

**Last Updated:** 2026-07-30  
**Version:** 1.0  
**Status:** ✅ Operational
