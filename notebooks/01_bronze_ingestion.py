# Databricks notebook source

import os
from google.cloud import storage
from google.oauth2 import service_account

# --- GCS Authentication Configuration ---
# Path to service account key stored inside workspace / DBFS / Volume
KEY_PATH = "/dbfs/filestore/configs/gcp-key.json"

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

