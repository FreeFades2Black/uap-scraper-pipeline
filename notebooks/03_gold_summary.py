# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# DBTITLE 1,Gold Layer - UAP Summary Analytics
# MAGIC %md
# MAGIC # 03 - Gold Layer Summary
# MAGIC
# MAGIC Aggregates silver GitHub event data into business-ready analytics tables.
# MAGIC
# MAGIC **Silver → Gold transformations:**
# MAGIC - Event type distribution
# MAGIC - Actor/user activity metrics
# MAGIC - Repository activity summaries
# MAGIC - Organization activity patterns
# MAGIC - Time-series event trends
# MAGIC - Ready for BI dashboards and analytics

# COMMAND ----------

# DBTITLE 1,Configuration
# Table paths
SILVER_TABLE = "workspace.default.silver_uap_structured"
GOLD_SUMMARY_TABLE = "workspace.default.gold_github_summary"
GOLD_BY_ACTOR_TABLE = "workspace.default.gold_github_by_actor"
GOLD_BY_REPO_TABLE = "workspace.default.gold_github_by_repo"
GOLD_TIMELINE_TABLE = "workspace.default.gold_github_timeline"
CHECKPOINT_PATH = "gs://uap-scraper-lab-2026-lakehouse-data/checkpoints/gold_github"

print(f"Source: {SILVER_TABLE}")
print(f"Target Summary: {GOLD_SUMMARY_TABLE}")
print(f"Target By Actor: {GOLD_BY_ACTOR_TABLE}")
print(f"Target By Repo: {GOLD_BY_REPO_TABLE}")
print(f"Target Timeline: {GOLD_TIMELINE_TABLE}")

# COMMAND ----------

# DBTITLE 1,BATCH: Overall Summary
from pyspark.sql.functions import (
    count, countDistinct, sum, avg, min, max, 
    round as spark_round, current_timestamp, when, col
)

# Read from silver
df_silver = spark.read.table(SILVER_TABLE)

# Create overall summary
df_summary = df_silver.agg(
    count("*").alias("total_events"),
    countDistinct("event_type").alias("unique_event_types"),
    countDistinct("actor_login").alias("unique_actors"),
    countDistinct("repo_name").alias("unique_repos"),
    countDistinct("org_login").alias("unique_orgs"),
    sum(when(col("has_actor"), 1).otherwise(0)).alias("events_with_actor"),
    sum(when(col("has_repo"), 1).otherwise(0)).alias("events_with_repo"),
    sum(when(col("has_org"), 1).otherwise(0)).alias("events_with_org"),
    sum(when(col("is_public"), 1).otherwise(0)).alias("public_events"),
    min("event_timestamp").alias("earliest_event"),
    max("event_timestamp").alias("latest_event"),
    current_timestamp().alias("_summary_generated_at")
)

# Add calculated metrics
df_summary = df_summary.withColumn(
    "data_completeness_pct",
    spark_round((col("events_with_actor") / col("total_events")) * 100, 2)
).withColumn(
    "public_event_pct",
    spark_round((col("public_events") / col("total_events")) * 100, 2)
)

# Write to gold summary table
(
    df_summary.write
    .format("delta")
    .mode("overwrite")
    .saveAsTable(GOLD_SUMMARY_TABLE)
)

print(f"✅ Gold summary table created")
print(f"   Table: {GOLD_SUMMARY_TABLE}")
display(df_summary)

# COMMAND ----------

# DBTITLE 1,BATCH: Actor Activity Aggregation
from pyspark.sql.functions import count, countDistinct, min, max, round as spark_round, current_timestamp, col

# Read from silver
df_silver = spark.read.table(SILVER_TABLE)

# Aggregate by actor (user)
df_by_actor = (
    df_silver
    .filter(col("has_actor"))
    .groupBy("actor_login", "actor_id", "actor_url")
    .agg(
        count("*").alias("total_events"),
        countDistinct("event_type").alias("unique_event_types"),
        countDistinct("repo_name").alias("repos_touched"),
        countDistinct("org_login").alias("orgs_involved"),
        min("event_timestamp").alias("first_event"),
        max("event_timestamp").alias("last_event")
    )
    .withColumn("_aggregated_at", current_timestamp())
    .orderBy(col("total_events").desc())
)

# Write to gold by actor table
(
    df_by_actor.write
    .format("delta")
    .mode("overwrite")
    .saveAsTable(GOLD_BY_ACTOR_TABLE)
)

print(f"✅ Gold actor activity table created")
print(f"   Table: {GOLD_BY_ACTOR_TABLE}")
print(f"   Top 10 most active actors:")
display(df_by_actor.limit(10))

# COMMAND ----------

# DBTITLE 1,BATCH: Repository Activity Aggregation
from pyspark.sql.functions import (
    count, countDistinct, min, max, current_timestamp, col
)

# Read from silver
df_silver = spark.read.table(SILVER_TABLE)

# Aggregate by repository
df_by_repo = (
    df_silver
    .filter(col("has_repo"))
    .groupBy("repo_name", "repo_id", "repo_url")
    .agg(
        count("*").alias("total_events"),
        countDistinct("event_type").alias("unique_event_types"),
        countDistinct("actor_login").alias("unique_contributors"),
        min("event_timestamp").alias("first_event"),
        max("event_timestamp").alias("last_event")
    )
    .withColumn("_aggregated_at", current_timestamp())
    .orderBy(col("total_events").desc())
)

# Write to gold by repo table
(
    df_by_repo.write
    .format("delta")
    .mode("overwrite")
    .saveAsTable(GOLD_BY_REPO_TABLE)
)

print(f"✅ Gold repository activity table created")
print(f"   Table: {GOLD_BY_REPO_TABLE}")
print(f"   Top 10 most active repos:")
display(df_by_repo.limit(10))

# COMMAND ----------

# DBTITLE 1,BATCH: Daily Timeline Aggregation
from pyspark.sql.functions import (
    date_trunc, count, countDistinct, when, current_timestamp, col
)

# Read from silver
df_silver = spark.read.table(SILVER_TABLE)

# Aggregate by date (daily timeline)
df_timeline = (
    df_silver
    .filter(col("event_timestamp").isNotNull())
    .withColumn("event_date", date_trunc("day", col("event_timestamp")))
    .groupBy("event_date")
    .agg(
        count("*").alias("daily_events"),
        countDistinct("actor_login").alias("unique_actors"),
        countDistinct("repo_name").alias("unique_repos"),
        countDistinct("event_type").alias("unique_event_types"),
        count(when(col("is_public"), 1)).alias("public_events"),
        count(when(col("has_org"), 1)).alias("org_events")
    )
    .withColumn("_aggregated_at", current_timestamp())
    .orderBy("event_date")
)

# Write to gold timeline table
(
    df_timeline.write
    .format("delta")
    .mode("overwrite")
    .saveAsTable(GOLD_TIMELINE_TABLE)
)

print(f"✅ Gold timeline table created")
print(f"   Table: {GOLD_TIMELINE_TABLE}")
print(f"   Sample timeline data:")
display(df_timeline.limit(10))

# COMMAND ----------

# DBTITLE 1,Streaming Cell (Not Used)
# This cell is not used - the BATCH versions above are used by the scheduled job

# Real-time actor activity aggregation with windowing
df_actor_stream = (
    df_silver_stream
    .filter(col("has_actor"))
    .withWatermark("event_timestamp", "1 hour")  # Handle late data
    .groupBy(
        window(col("event_timestamp"), "1 hour"),
        "actor_login", "actor_id"
    )
    .agg(
        count("*").alias("event_count"),
        countDistinct("event_type").alias("unique_event_types"),
        countDistinct("repo_name").alias("repos_touched")
    )
    .select(
        col("window.start").alias("window_start"),
        col("window.end").alias("window_end"),
        "actor_login", "actor_id",
        "event_count", "unique_event_types", "repos_touched"
    )
    .withColumn("_aggregated_at", current_timestamp())
)

# Write to gold actor activity table (streaming)
query = (
    df_actor_stream.writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", f"{CHECKPOINT_PATH}/actor")
    .trigger(processingTime="5 minutes")  # Update every 5 minutes
    .toTable(f"{GOLD_BY_ACTOR_TABLE}_stream")
)

print(f"✅ Streaming gold aggregation started")
print(f"   Query ID: {query.id}")
print(f"   Table: {GOLD_BY_ACTOR_TABLE}_stream")
print(f"   Trigger: Every 5 minutes")
print(f"\n   To stop: query.stop()")

# COMMAND ----------

# DBTITLE 1,Verify Gold Tables
# MAGIC %sql
# MAGIC -- Overall Summary
# MAGIC SELECT * FROM workspace.default.gold_github_summary;
# MAGIC
# MAGIC -- Top 10 Most Active Actors
# MAGIC SELECT * FROM workspace.default.gold_github_by_actor ORDER BY total_events DESC LIMIT 10;
# MAGIC
# MAGIC -- Top 10 Most Active Repos
# MAGIC SELECT * FROM workspace.default.gold_github_by_repo ORDER BY total_events DESC LIMIT 10;
# MAGIC
# MAGIC -- Recent Timeline (Last 10 Days)
# MAGIC SELECT * FROM workspace.default.gold_github_timeline ORDER BY event_date DESC LIMIT 10;

# COMMAND ----------

