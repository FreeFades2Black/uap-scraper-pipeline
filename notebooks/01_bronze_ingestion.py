# Databricks notebook source
# MAGIC %md
# MAGIC # 01 - Bronze Layer Ingestion (GCS -> Delta)
# MAGIC Reads raw JSON payloads from GCS landing bucket and writes to Bronze Delta table.

# COMMAND ----------

from pyspark.sql.functions import current_timestamp, input_file_name

# Configuration
RAW_BUCKET_PATH = "gs://uap-scraper-lab-2026-scraper-raw/raw_ingest/*.json"
DELTA_BRONZE_PATH = "gs://uap-scraper-lab-2026-lakehouse-data/bronze/github_events"
CHECKPOINT_PATH = "gs://uap-scraper-lab-2026-lakehouse-data/checkpoints/github_events_bronze"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Read Raw JSON Data using Auto Loader (CloudFiles)

# COMMAND ----------

df_raw = (
    spark.readStream
    .format("cloudFiles")
    .option("cloudFiles.format", "json")
    .option("cloudFiles.schemaLocation", f"{CHECKPOINT_PATH}/schema")
    .load(RAW_BUCKET_PATH)
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Add Metadata Attributes

# COMMAND ----------

df_bronze = (
    df_raw
    .withColumn("_ingest_timestamp", current_timestamp())
    .withColumn("_source_file", input_file_name())
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Stream Write to Bronze Delta Lake Table

# COMMAND ----------

query = (
    df_bronze.writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", CHECKPOINT_PATH)
    .start(DELTA_BRONZE_PATH)
)

print(f"Bronze ingestion streaming query started: {query.id}")
