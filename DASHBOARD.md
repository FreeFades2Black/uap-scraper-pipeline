# GitHub Events Analytics Dashboard

**Published Dashboard URL:** https://dbc-3e95d032-684c.cloud.databricks.com/dashboardsv3/01f18c3e539c18d4a13edd75a1f50656/published?o=7474643734871839

## Overview

Analytics dashboard visualizing GitHub events from the lakehouse pipeline. Tracks activity patterns across actors, repositories, and daily trends using the medallion architecture (Bronze → Silver → Gold).

## Data Flow

```
GCS Buckets (GitHub Events JSON)
    ↓
Bronze Layer (workspace.default.bronze_uap_raw)
    ↓ 01_bronze_ingestion.py
Silver Layer (workspace.default.silver_uap_structured)
    ↓ 02_silver_transformation.py
Gold Layer (4 analytics tables)
    ↓ 03_gold_summary.py
Dashboard Visualizations
```

## Gold Tables

1. **gold_github_summary** - Overall KPIs (total events, unique actors/repos/orgs, data completeness)
2. **gold_github_by_actor** - Activity aggregated by contributor
3. **gold_github_by_repo** - Activity aggregated by repository
4. **gold_github_timeline** - Daily event trends

## Dashboard Datasets

### 1. GitHub Summary Metrics
```sql
SELECT
  total_events,
  unique_actors,
  unique_repos,
  data_completeness_pct
FROM workspace.default.gold_github_summary
```

### 2. Top 10 Active Contributors
```sql
SELECT
  actor_login,
  total_events
FROM workspace.default.gold_github_by_actor
ORDER BY total_events DESC, actor_login
LIMIT 10
```

### 3. Top 10 Active Repositories
```sql
SELECT
  repo_name,
  total_events
FROM workspace.default.gold_github_by_repo
ORDER BY total_events DESC, repo_name
LIMIT 10
```

### 4. Daily Event Timeline
```sql
SELECT
  event_date,
  daily_events
FROM workspace.default.gold_github_timeline
ORDER BY event_date
```

### 5. Event Distribution (Public vs Org)
```sql
SELECT
  'Public Events' as event_category,
  SUM(public_events) as event_count
FROM workspace.default.gold_github_timeline
UNION ALL
SELECT
  'Organization Events' as event_category,
  SUM(org_events) as event_count
FROM workspace.default.gold_github_timeline
```

## Dashboard Layout

### Row 1: KPI Cards (Height: 2, Total Width: 12)
- **Total Events** - Counter (Col 0-2)
- **Unique Contributors** - Counter (Col 3-5)
- **Unique Repositories** - Counter (Col 6-8)
- **Data Completeness** - Counter (Col 9-11)

### Row 2: Side-by-Side Bar Charts (Height: 4, Total Width: 12)
- **Top 10 Active Contributors** - Horizontal bar chart (Col 0-5)
  - X-axis: actor_login
  - Y-axis: total_events
- **Top 10 Active Repositories** - Horizontal bar chart (Col 6-11)
  - X-axis: repo_name
  - Y-axis: total_events

### Row 3: Full-Width Timeline (Height: 4, Total Width: 12)
- **Daily Event Timeline** - Line chart (Col 0-11)
  - X-axis: event_date (temporal)
  - Y-axis: daily_events

### Row 4: Centered Distribution (Height: 4)
- **Event Distribution** - Pie chart (Col 3-8)
  - Category: event_category
  - Value: event_count

## Dashboard Configuration

- **Compute:** Serverless SQL Warehouse
- **Permission Mode:** Shared data permission (viewers use owner's credentials)
- **Data Refresh:** Manual or scheduled via dashboard settings
- **Grid Layout:** 12 columns, responsive sizing

## Metrics Summary (as of 2026-07-30)

- Total Events: 91
- Unique Contributors: 90
- Unique Repositories: 90
- Unique Organizations: 5
- Data Completeness: 98.9%
- Date Range: July 23-30, 2026 (7 days)

## Notes

- All visualizations use pre-aggregated gold tables for optimal performance
- Dashboard queries are lightweight (1-30 rows per query)
- Event distribution shows 90 public events vs 5 organization events
- Most activity is from individual contributors on personal repos
