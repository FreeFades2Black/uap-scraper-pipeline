# GCP Always Free Tier Rules for Storage & Compute

This document outlines the hard limits and Terraform configurations enforced to ensure all GCP resources stay 100% within the Always Free Tier.

## 1. Storage Rules (Google Cloud Storage)
- **Allowed Regions:** `us-central1` (Iowa), `us-east1` (South Carolina), or `us-west1` (Oregon) ONLY.
- **Storage Class:** `STANDARD` only (Coldline/Nearline/Archive carry minimum retention fees and operation costs).
- **Max Storage Limit:** **5 GB** total combined across all buckets in the project.
- **Lifecycle Enforcement:** Raw landing bucket (`-uap-raw`) auto-deletes files after 7 days; processed staging bucket (`-uap-lakehouse`) auto-deletes after 30 days to strictly stay under the 5 GB cap.

## 2. Container Registry (Artifact Registry)
- **Free Limit:** **0.5 GB (500 MB)** storage per month for container images.
- **Image Safeguards:** Use lightweight base images (`python:3.11-slim` or `alpine`) to keep container sizes around ~150 MB.

## 3. Serverless Compute (Cloud Run Jobs)
- **Free Allowance:** 2,000,000 requests per month.
- **Compute Allowance:** 180,000 vCPU-seconds and 360,000 GiB-seconds of memory per month.
- **Resource Sizing:** Provision Cloud Run tasks with max 1 vCPU and 512MiB/1GiB RAM to maximize free execution runtime.

## 4. Egress Network Limits
- **Free Limit:** **100 GB** total internet egress per month (excluding China and Australia).
