# Databricks notebook source
# DBTITLE 1,Bronze Layer - Ingest Raw UAP JSON Telemetry
# MAGIC %md
# MAGIC # 01 - Bronze Layer Ingestion
# MAGIC 
# MAGIC Ingests raw multi-source UAP JSON payloads from Google Cloud Storage (GCS) into Unity Catalog Bronze Delta tables.
# MAGIC 
# MAGIC **Bronze Ingestion Responsibilities:**
# MAGIC - Download JSON batches from GCS raw landing bucket (`raw_ingest/`) to Volume staging
# MAGIC - Explode `all_sightings` records from the scraper payload envelope
# MAGIC - Preserve raw payload structure, original fields, and ingestion audit metadata (`_ingest_timestamp`, `_source_file`)
# MAGIC - Append into `workspace.default.bronze_uap_raw` Delta Lake table

import os
from google.cloud import storage
from google.oauth2 import service_account

# --- GCS Authentication Configuration ---
KEY_PATH = "/Volumes/workspace/default/configs/gcp-key.json"

print("Initializing GCS Bronze Ingestion Pipeline...")

try:
    if os.path.exists(KEY_PATH):
        credentials = service_account.Credentials.from_service_account_file(KEY_PATH)
        client = storage.Client(credentials=credentials)
    else:
        print(f"Key file not found at {KEY_PATH}. Attempting default client connection...")
        client = storage.Client()
    
    buckets = list(client.list_buckets(max_results=5))
    print(f"Successfully connected to GCP! Found {len(buckets)} bucket(s):")
    for bucket in buckets:
        print(f" - {bucket.name}")
except Exception as e:
    print(f"GCP Connection Warning: {e}")

# COMMAND ----------

# DBTITLE 1,Configuration
RAW_BUCKET = "uap-scraper-lab-2026-scraper-raw"
RAW_PREFIX = "raw_ingest/"
LOCAL_STAGING_PATH = "/Volumes/workspace/default/configs/staging/"
BRONZE_TABLE = "workspace.default.bronze_uap_raw"

print(f"Source Bucket: gs://{RAW_BUCKET}/{RAW_PREFIX}")
print(f"Local Staging: {LOCAL_STAGING_PATH}")
print(f"Target Bronze Table: {BRONZE_TABLE}")

# COMMAND ----------

# DBTITLE 1,Download JSON files from GCS to Staging Volume
os.makedirs(LOCAL_STAGING_PATH, exist_ok=True)

try:
    bucket = client.bucket(RAW_BUCKET)
    blobs = list(bucket.list_blobs(prefix=RAW_PREFIX))
    downloaded_count = 0
    for blob in blobs:
        if blob.name.endswith('.json'):
            filename = blob.name.split('/')[-1]
            local_file = os.path.join(LOCAL_STAGING_PATH, filename)
            if not os.path.exists(local_file):
                blob.download_to_filename(local_file)
                print(f"✅ Downloaded: {blob.name} → {local_file}")
                downloaded_count += 1
    print(f"\n✅ Total new files downloaded: {downloaded_count}")
except Exception as e:
    print(f"GCS Download skipped or failed: {e}")

# COMMAND ----------

# DBTITLE 1,BATCH: Read and Ingest into Bronze Delta Table
from pyspark.sql.functions import current_timestamp, col, explode

# Read multiline JSON envelopes
df_raw = (
    spark.read
    .format("json")
    .option("inferSchema", "true")
    .option("multiLine", "true")
    .load(LOCAL_STAGING_PATH)
)

# Flatten / Explode sightings array if wrapped in envelope
if "all_sightings" in df_raw.columns:
    df_exploded = (
        df_raw
        .select(
            col("collection_timestamp"),
            col("duration_seconds").alias("scrape_duration_seconds"),
            col("successful_sources"),
            explode(col("all_sightings")).alias("sighting")
        )
        .select(
            col("collection_timestamp"),
            col("scrape_duration_seconds"),
            col("successful_sources"),
            col("sighting.*")
        )
    )
else:
    df_exploded = df_raw

# Add Bronze Audit Metadata
df_bronze = (
    df_exploded
    .withColumn("_ingest_timestamp", current_timestamp())
    .withColumn("_source_file", col("_metadata.file_path"))
)

# Write to Bronze Delta Table
(
    df_bronze.write
    .format("delta")
    .mode("append")
    .option("mergeSchema", "true")
    .saveAsTable(BRONZE_TABLE)
)

print(f"✅ Bronze Ingestion Complete")
print(f"   Records Written: {df_bronze.count()}")
print(f"   Table: {BRONZE_TABLE}")

# COMMAND ----------

# DBTITLE 1,Verify Bronze Table
# MAGIC %sql
# MAGIC SELECT 
# MAGIC     COUNT(*) as total_sightings_raw,
# MAGIC     COUNT(DISTINCT sighting_hash) as unique_sightings,
# MAGIC     COUNT(DISTINCT data_source) as active_sources,
# MAGIC     MIN(_ingest_timestamp) as first_ingested,
# MAGIC     MAX(_ingest_timestamp) as last_ingested
# MAGIC FROM workspace.default.bronze_uap_raw