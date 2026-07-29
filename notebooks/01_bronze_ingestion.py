# Databricks notebook source

import os
from google.cloud import storage

# --- GCS Authentication ---
# Set key location if utilizing service account JSON stored in workspace / mounted paths
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/dbfs/filestore/configs/gcp-key.json"

print("Initializing GCS Bronze Ingestion Pipeline...")

try:
    # Initialize GCS client
    # Storage client auto-detects standard environment variables or GCP metadata server
    client = storage.Client()
    
    # List available buckets or perform test query
    buckets = list(client.list_buckets(max_results=5))
    print(f"Successfully connected to GCP! Found {len(buckets)} bucket(s):")
    for bucket in buckets:
        print(f" - {bucket.name}")

except Exception as e:
    print(f"GCP Connection initialization ready. Details: {e}")

