# Cloud Scraper & Lakehouse Infrastructure

Automated data ingestion pipeline targeting GCP Cloud Storage and Databricks.

## Structure
- `scraper/`: Python scraper codebase and Docker setup.
- `terraform/`: GCP and Databricks Infrastructure-as-Code.
# UAP Lakehouse Pipeline

A complete end-to-end data lakehouse pipeline for ingesting, transforming, and analyzing GitHub events data using Databricks and Unity Catalog.

## 🏗️ Architecture

This project implements a **medallion architecture** (Bronze → Silver → Gold) for processing GitHub events from Google Cloud Storage (GCS) into analytics-ready tables.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Google Cloud Storage (GCS)                    │
│  Buckets: uap-scraper-lab-2026-lakehouse-data (staging)        │
│           uap-scraper-lab-2026-scraper-raw (raw data)           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  🥉 Bronze Layer (Raw Data)                      │
│  Table: workspace.default.bronze_uap_raw                        │
│  - Raw JSON events from GCS                                     │
│  - Preserves source structure                                   │
│  - Includes extraction metadata                                 │
│  Notebook: 01_bronze_ingestion.py                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│               🥈 Silver Layer (Structured Data)                  │
│  Table: workspace.default.silver_uap_structured                 │
│  - Parsed and flattened GitHub events                           │
│  - Extracted actor, repo, org, payload fields                   │
│  - Quality flags and data type conversions                      │
│  - 40 structured fields                                         │
│  Notebook: 02_silver_transformation.py                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              🥇 Gold Layer (Analytics Tables)                    │
│  Tables:                                                         │
│  1. workspace.default.gold_github_summary                       │
│     → Overall KPIs and data quality metrics                     │
│  2. workspace.default.gold_github_by_actor                      │
│     → Activity aggregated by contributor                        │
│  3. workspace.default.gold_github_by_repo                       │
│     → Activity aggregated by repository                         │
│  4. workspace.default.gold_github_timeline                      │
│     → Daily event trends and patterns                           │
│  Notebook: 03_gold_summary.py                                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   📊 Analytics Dashboard                         │
│  GitHub Events Analytics Dashboard (Lakeview)                   │
│  - 4 KPI cards, 2 bar charts, 1 line chart, 1 pie chart        │
│  - Published URL with shared data permissions                   │
│  Documentation: DASHBOARD.md                                     │
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
# Records: 91 GitHub events
```

##### Silver Transformation
```bash
# Run: notebooks/02_silver_transformation.py
# Cells: 2 (Config), 3 (Batch Transform), 5 (Quality Check), 6 (Sample)
# Output: workspace.default.silver_uap_structured
# Fields: 40 structured columns
```

##### Gold Aggregations
```bash
# Run: notebooks/03_gold_summary.py
# Cells: 2 (Config), 3-6 (Batch Aggregations), 7 (Verify)
# Output: 4 gold analytics tables
```

#### 3. View the Dashboard

Open the published dashboard to explore your analytics:

**[GitHub Events Analytics Dashboard →](https://dbc-3e95d032-684c.cloud.databricks.com/dashboardsv3/01f18c3e539c18d4a13edd75a1f50656/published?o=7474643734871839)**

See `DASHBOARD.md` for complete configuration details.

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
- Flatten nested JSON structures (actor, repo, org, payload)
- Extract and parse timestamps
- Add quality flags (has_actor, has_repo, has_org)
- Type conversions and null handling

#### Silver → Gold
- Aggregate by actor (contributor activity)
- Aggregate by repository (repo activity)
- Time-series aggregation (daily trends)
- Overall summary metrics and KPIs

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

## 🔒 Security

- **Unity Catalog Volumes** replace deprecated DBFS root for secure file storage
- **GCP Service Account Key** stored in encrypted volume
- **Dashboard Permissions** use shared credential mode (viewers use owner's credentials)
- **Unity Catalog Governance** enforces table-level access control

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
