# Databricks notebook source
import os
from google.cloud import storage
from google.oauth2 import service_account

# --- GCS Authentication Configuration ---
# Path to service account key stored in Unity Catalog Volume
# Upload your gcp-key.json file to this volume via Catalog UI
KEY_PATH = "/Volumes/workspace/default/configs/gcp-key.json"

print("Initializing GCS Bronze Ingestion Pipeline...")

try:
    if os.path.exists(KEY_PATH):
        # Instantiate credentials directly from file
        credentials = service_account.Credentials.from_service_account_file(KEY_PATH)
        client = storage.Client(credentials=credentials)
    else:
        # Fallback to default auth if key file is not present at DBFS path
        print(f"Key file not found at {KEY_PATH}. Attempting default client connection...")
        client = storage.Client()
    
    # List buckets to confirm access
    buckets = list(client.list_buckets(max_results=5))
    print(f"Successfully connected to GCP! Found {len(buckets)} bucket(s):")
    for bucket in buckets:
        print(f" - {bucket.name}")

except Exception as e:
    print(f"GCP Connection Error: {e}")


# COMMAND ----------

# DBTITLE 1,Configuration
# Configuration paths
RAW_BUCKET = "gs://uap-scraper-lab-2026-scraper-raw/raw_ingest/"
BRONZE_TABLE = "workspace.default.bronze_uap_raw"
CHECKPOINT_PATH = "gs://uap-scraper-lab-2026-lakehouse-data/checkpoints/bronze_uap"

print(f"Source: {RAW_BUCKET}")
print(f"Target: {BRONZE_TABLE}")
print(f"Checkpoint: {CHECKPOINT_PATH}")

# COMMAND ----------

# DBTITLE 1,Download JSON files from GCS to Volume
# Download JSON files from GCS to Unity Catalog Volume
# This bridges the GCS → Databricks gap on serverless compute

from google.cloud import storage
from google.oauth2 import service_account
import json

# Initialize GCS client
credentials = service_account.Credentials.from_service_account_file(KEY_PATH)
client = storage.Client(credentials=credentials)

# GCS source bucket and prefix
SOURCE_BUCKET = "uap-scraper-lab-2026-scraper-raw"
SOURCE_PREFIX = "raw_ingest/"

# Local volume path for staging
LOCAL_STAGING_PATH = "/Volumes/workspace/default/configs/staging/"

# Create staging directory if it doesn't exist
os.makedirs(LOCAL_STAGING_PATH, exist_ok=True)

# List and download files from GCS
bucket = client.bucket(SOURCE_BUCKET)
blobs = list(bucket.list_blobs(prefix=SOURCE_PREFIX))

downloaded_count = 0
for blob in blobs:
    if blob.name.endswith('.json'):
        filename = blob.name.split('/')[-1]
        local_file = os.path.join(LOCAL_STAGING_PATH, filename)
        blob.download_to_filename(local_file)
        print(f"✅ Downloaded: {blob.name} → {local_file}")
        downloaded_count += 1

print(f"\n✅ Downloaded {downloaded_count} JSON files from GCS")
print(f"   Staging path: {LOCAL_STAGING_PATH}")d_files = []
for blob in blobs:
    if blob.name.endswith('.json'):
        # Download to staging volume
        local_file = os.path.join(LOCAL_STAGING_PATH, blob.name.split('/')[-1])
        blob.download_to_filename(local_file)
        downloaded_files.append(local_file)
        print(f"✅ Downloaded: {blob.name} → {local_file}")

print(f"\n✅ Downloaded {len(downloaded_files)} JSON files from GCS")
print(f"   Staging path: {LOCAL_STAGING_PATH}")

# COMMAND ----------

# DBTITLE 1,BATCH: Read and Write Bronze
from pyspark.sql.functions import current_timestamp, col

# Read JSON files from staging volume (downloaded from GCS)
df_raw = (
    spark.read
    .format("json")
    .option("inferSchema", "true")
    .option("multiLine", "true")
    .load(LOCAL_STAGING_PATH)
)

# Add metadata columns (Unity Catalog uses _metadata.file_path)
df_bronze = (
    df_raw
    .withColumn("_ingest_timestamp", current_timestamp())
    .withColumn("_source_file", col("_metadata.file_path"))
)

# Write to Bronze Delta table
(
    df_bronze.write
    .format("delta")
    .mode("append")
    .option("mergeSchema", "true")
    .saveAsTable(BRONZE_TABLE)
)

print(f"✅ Batch ingestion complete")
print(f"   Records written: {df_bronze.count()}")
print(f"   Table: {BRONZE_TABLE}")

# COMMAND ----------

# DBTITLE 1,Incremental Bronze Ingestion (Batch)
# Incremental ingestion: Download new files from GCS and append to bronze
# Run this cell as part of the scheduled job

from google.cloud import storage
from google.oauth2 import service_account
from pyspark.sql.functions import current_timestamp, col
import os

# Initialize GCS client
credentials = service_account.Credentials.from_service_account_file(KEY_PATH)
client = storage.Client(credentials=credentials)

# Get list of already processed files (NO RDD - use DataFrame collect)
if spark.catalog.tableExists(BRONZE_TABLE):
    processed_df = spark.read.table(BRONZE_TABLE).select("_source_file").distinct().collect()
    processed_files = set([row._source_file.split('/')[-1] for row in processed_df])
else:
    processed_files = set()

print(f"Already processed: {len(processed_files)} files")

# List files in GCS
bucket = client.bucket("uap-scraper-lab-2026-scraper-raw")
blobs = list(bucket.list_blobs(prefix="raw_ingest/"))

# Download only new files
new_files = []
for blob in blobs:
    if blob.name.endswith('.json'):
        filename = blob.name.split('/')[-1]
        if filename not in processed_files:
            local_file = os.path.join(LOCAL_STAGING_PATH, filename)
            blob.download_to_filename(local_file)
            new_files.append(filename)
            print(f"✅ New file: {blob.name}")

if new_files:
    # Read and append new files
    df_new = (
        spark.read
        .format("json")
        .option("inferSchema", "true")
        .option("multiLine", "true")
        .load(LOCAL_STAGING_PATH)
    )
    
    df_new_bronze = (
        df_new
        .withColumn("_ingest_timestamp", current_timestamp())
        .withColumn("_source_file", col("_metadata.file_path"))
    )
    
    records_count = df_new_bronze.count()
    
    (
        df_new_bronze.write
        .format("delta")
        .mode("append")
        .option("mergeSchema", "true")
        .saveAsTable(BRONZE_TABLE)
    )
    
    print(f"\n✅ Incremental ingestion complete")
    print(f"   New files processed: {len(new_files)}")
    print(f"   Records added: {records_count}")
else:
    print("ℹ️ No new files to process")

# COMMAND ----------

# DBTITLE 1,Verify Bronze Table
# MAGIC %sql
# MAGIC SELECT 
# MAGIC     COUNT(*) as total_records,
# MAGIC     COUNT(DISTINCT _source_file) as total_files,
# MAGIC     MIN(_ingest_timestamp) as first_ingested,
# MAGIC     MAX(_ingest_timestamp) as last_ingested
# MAGIC FROM workspace.default.bronze_uap_raw