# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# DBTITLE 1,Silver Layer - Parse and Structure UAP Data
# MAGIC %md
# MAGIC # 02 - Silver Layer Transformation
# MAGIC
# MAGIC Transforms raw bronze GitHub event data into structured, validated silver tables.
# MAGIC
# MAGIC **Bronze → Silver transformations:**
# MAGIC - Parse nested GitHub event structures (actor, org, payload, repo)
# MAGIC - Extract and flatten nested fields
# MAGIC - Convert timestamp strings to proper datetime
# MAGIC - Add data quality flags
# MAGIC - Separate event metadata from payload details

# COMMAND ----------

# DBTITLE 1,Configuration
# Table paths
BRONZE_TABLE = "workspace.default.bronze_uap_raw"
SILVER_TABLE = "workspace.default.silver_uap_structured"

print(f"Source: {BRONZE_TABLE}")
print(f"Target: {SILVER_TABLE}")

# COMMAND ----------

# DBTITLE 1,BATCH: Parse and Structure
from pyspark.sql.functions import (
    col, current_timestamp, when, to_timestamp, trim
)

# Read from bronze
df_bronze = spark.read.table(BRONZE_TABLE)

# Parse GitHub event data
df_silver = (
    df_bronze
    # Core event fields
    .withColumn("event_id", col("id"))
    .withColumn("event_type", col("type"))
    .withColumn("event_timestamp", to_timestamp(col("created_at")))
    .withColumn("is_public", col("public"))
    
    # Actor (user who triggered the event)
    .withColumn("actor_id", col("actor.id"))
    .withColumn("actor_login", col("actor.login"))
    .withColumn("actor_display_login", col("actor.display_login"))
    .withColumn("actor_url", col("actor.url"))
    
    # Organization
    .withColumn("org_id", col("org.id"))
    .withColumn("org_login", col("org.login"))
    .withColumn("org_url", col("org.url"))
    
    # Repository
    .withColumn("repo_id", col("repo.id"))
    .withColumn("repo_name", col("repo.name"))
    .withColumn("repo_url", col("repo.url"))
    
    # Payload details (varies by event type)
    .withColumn("payload_ref", col("payload.ref"))
    .withColumn("payload_ref_type", col("payload.ref_type"))
    .withColumn("payload_push_id", col("payload.push_id"))
    .withColumn("payload_before", col("payload.before"))
    .withColumn("payload_head", col("payload.head"))
    .withColumn("payload_description", col("payload.description"))
    
    # Metadata fields
    .withColumn("extraction_timestamp", to_timestamp(col("extraction_timestamp")))
    .withColumn("status", col("status"))
    .withColumn("regions", col("regions"))
    
    # Data quality flags
    .withColumn("has_actor", col("actor_id").isNotNull())
    .withColumn("has_repo", col("repo_id").isNotNull())
    .withColumn("has_org", col("org_id").isNotNull())
    .withColumn("has_timestamp", col("event_timestamp").isNotNull())
    
    # Silver metadata
    .withColumn("_silver_timestamp", current_timestamp())
    .withColumn("_bronze_source_file", col("_source_file"))
    .withColumn("_bronze_ingest_timestamp", col("_ingest_timestamp"))
)

# Write to silver table
(
    df_silver.write
    .format("delta")
    .mode("overwrite")
    .option("mergeSchema", "true")
    .option("overwriteSchema", "true")
    .saveAsTable(SILVER_TABLE)
)

print(f"✅ Batch silver transformation complete")
print(f"   Records processed: {df_silver.count()}")
print(f"   Table: {SILVER_TABLE}")

# COMMAND ----------

# DBTITLE 1,Parse and Structure (Batch)
# This cell is not used - the BATCH version above is used by the scheduled job

# Parse GitHub event data (same transformations as batch)
df_silver_stream = (
    df_bronze_stream
    # Core event fields
    .withColumn("event_id", col("id"))
    .withColumn("event_type", col("type"))
    .withColumn("event_timestamp", to_timestamp(col("created_at")))
    .withColumn("is_public", col("public"))
    
    # Actor
    .withColumn("actor_id", col("actor.id"))
    .withColumn("actor_login", col("actor.login"))
    .withColumn("actor_display_login", col("actor.display_login"))
    .withColumn("actor_url", col("actor.url"))
    
    # Organization
    .withColumn("org_id", col("org.id"))
    .withColumn("org_login", col("org.login"))
    .withColumn("org_url", col("org.url"))
    
    # Repository
    .withColumn("repo_id", col("repo.id"))
    .withColumn("repo_name", col("repo.name"))
    .withColumn("repo_url", col("repo.url"))
    
    # Payload
    .withColumn("payload_ref", col("payload.ref"))
    .withColumn("payload_ref_type", col("payload.ref_type"))
    .withColumn("payload_push_id", col("payload.push_id"))
    .withColumn("payload_before", col("payload.before"))
    .withColumn("payload_head", col("payload.head"))
    .withColumn("payload_description", col("payload.description"))
    
    # Metadata
    .withColumn("extraction_timestamp", to_timestamp(col("extraction_timestamp")))
    .withColumn("status", col("status"))
    .withColumn("regions", col("regions"))
    
    # Data quality flags
    .withColumn("has_actor", col("actor_id").isNotNull())
    .withColumn("has_repo", col("repo_id").isNotNull())
    .withColumn("has_org", col("org_id").isNotNull())
    .withColumn("has_timestamp", col("event_timestamp").isNotNull())
    
    # Silver metadata
    .withColumn("_silver_timestamp", current_timestamp())
    .withColumn("_bronze_source_file", col("_source_file"))
    .withColumn("_bronze_ingest_timestamp", col("_ingest_timestamp"))
)

# Write to silver table (streaming)
query = (
    df_silver_stream.writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", CHECKPOINT_PATH)
    .option("mergeSchema", "true")
    .trigger(availableNow=True)  # Micro-batch
    .toTable(SILVER_TABLE)
)

query.awaitTermination()
print(f"✅ Streaming silver transformation complete")
print(f"   Query ID: {query.id}")
print(f"   Table: {SILVER_TABLE}")

# COMMAND ----------

# DBTITLE 1,Data Quality Check
# MAGIC %sql
# MAGIC SELECT 
# MAGIC     COUNT(*) as total_events,
# MAGIC     COUNT(DISTINCT event_type) as unique_event_types,
# MAGIC     COUNT(DISTINCT actor_login) as unique_actors,
# MAGIC     COUNT(DISTINCT org_login) as unique_orgs,
# MAGIC     COUNT(DISTINCT repo_name) as unique_repos,
# MAGIC     SUM(CASE WHEN has_actor THEN 1 ELSE 0 END) as events_with_actor,
# MAGIC     SUM(CASE WHEN has_repo THEN 1 ELSE 0 END) as events_with_repo,
# MAGIC     SUM(CASE WHEN has_org THEN 1 ELSE 0 END) as events_with_org,
# MAGIC     MIN(event_timestamp) as earliest_event,
# MAGIC     MAX(event_timestamp) as latest_event
# MAGIC FROM workspace.default.silver_uap_structured

# COMMAND ----------

# DBTITLE 1,Sample Silver Data
# MAGIC %sql
# MAGIC SELECT 
# MAGIC     event_id,
# MAGIC     event_type,
# MAGIC     event_timestamp,
# MAGIC     actor_login,
# MAGIC     repo_name,
# MAGIC     org_login,
# MAGIC     payload_ref_type,
# MAGIC     is_public,
# MAGIC     has_actor,
# MAGIC     has_repo
# MAGIC FROM workspace.default.silver_uap_structured
# MAGIC LIMIT 10

# COMMAND ----------

