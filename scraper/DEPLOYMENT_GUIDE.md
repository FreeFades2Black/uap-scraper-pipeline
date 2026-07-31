# 🛸 UAP Multi-Source Scraper - Deployment Guide

This guide covers three deployment methods for your multi-source UAP scraper to Google Cloud Functions.

---

## 📋 Prerequisites

Before deploying, ensure you have:

1. **Google Cloud Project** - `uap-scraper-lab-2026` (or your project ID)
2. **GCS Buckets** - Already created:
   - `uap-scraper-lab-2026-scraper-raw` (for raw JSON output)
   - `uap-scraper-lab-2026-lakehouse-data` (for staging)
3. **Appropriate IAM Permissions**:
   - Cloud Functions Admin
   - Service Account User
   - Storage Admin (for buckets)

---

## 🚀 Deployment Methods

### Method 1: Using the Automated Script (Recommended)

The fastest way to deploy - single command!

#### From Your Local Machine:

```bash
cd uap-scraper-pipeline/scraper
./deploy-multi-source.sh
```

#### What the Script Does:
* ✅ Validates gcloud CLI installation and authentication
* ✅ Enables required GCP APIs
* ✅ Deploys Cloud Function with optimal settings
* ✅ Tests the function automatically
* ✅ Shows logs and next steps

**Configuration:**
* **Memory**: 2GB (handles large datasets like Kaggle CSVs)
* **Timeout**: 540s (9 minutes for multi-source collection)
* **Max Instances**: 5 (cost optimization)
* **Trigger**: HTTP (on-demand)

---

### Method 2: Using GCP Cloud Shell

Perfect if you don't have gcloud installed locally!

#### Steps:

1. **Open Cloud Shell**
   - Go to: https://console.cloud.google.com
   - Click the Cloud Shell icon (top right)

2. **Clone Your Repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/uap-scraper-pipeline.git
   cd uap-scraper-pipeline/scraper
   ```

3. **Run the Deployment Script**
   ```bash
   chmod +x deploy-multi-source.sh
   ./deploy-multi-source.sh
   ```

4. **Save the Function URL**
   - The script outputs the URL
   - You'll need this for the Databricks pipeline

---

### Method 3: Manual Deployment (Step-by-Step)

For full control over each step:

#### Step 1: Authenticate and Set Project

```bash
gcloud auth login
gcloud config set project uap-scraper-lab-2026
```

#### Step 2: Enable Required APIs

```bash
gcloud services enable \
  cloudfunctions.googleapis.com \
  cloudbuild.googleapis.com \
  storage-api.googleapis.com \
  run.googleapis.com
```

#### Step 3: Deploy the Function

```bash
cd uap-scraper-pipeline/scraper

gcloud functions deploy uap-multi-source-scraper \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=. \
  --entry-point=cloud_function_entry \
  --trigger-http \
  --allow-unauthenticated \
  --memory=2GB \
  --timeout=540s \
  --max-instances=5 \
  --set-env-vars="PROJECT_ID=uap-scraper-lab-2026,GCS_RAW_BUCKET=uap-scraper-lab-2026-scraper-raw,GCS_STAGING_BUCKET=uap-scraper-lab-2026-lakehouse-data,PARALLEL_COLLECTION=true,MAX_RECORDS_PER_SOURCE=1000"
```

#### Step 4: Get the Function URL

```bash
gcloud functions describe uap-multi-source-scraper \
  --region=us-central1 \
  --gen2 \
  --format="value(serviceConfig.uri)"
```

#### Step 5: Test the Function

```bash
curl -X POST <YOUR_FUNCTION_URL>
```

---

## 🔍 Post-Deployment Verification

### 1. Check Logs

```bash
gcloud functions logs read uap-multi-source-scraper \
  --region=us-central1 \
  --limit=50
```

**Look for:**
* ✅ "Starting UAP data collection from X sources..."
* ✅ "Collector X collected Y records"
* ✅ "Successfully wrote Z records to GCS"
* ❌ Any ERROR or WARNING messages

### 2. Verify GCS Output

```bash
# List output files
gsutil ls gs://uap-scraper-lab-2026-scraper-raw/raw_ingest/

# Download latest file
gsutil cp gs://uap-scraper-lab-2026-scraper-raw/raw_ingest/uap_sightings_*.json ./

# Inspect the JSON
cat uap_sightings_*.json | jq . | head -100
```

**Expected Structure:**
```json
{
  "date_time": "2024-07-15 22:30:00",
  "city": "Phoenix",
  "state": "AZ",
  "country": "USA",
  "shape": "triangle",
  "duration": "5 minutes",
  "summary": "Three bright lights in triangular formation...",
  "data_source": "kaggle"
}
```

### 3. Test Databricks Integration

Run your bronze ingestion notebook:
```sql
SELECT COUNT(*), data_source
FROM workspace.default.bronze_uap_raw
GROUP BY data_source
```

**Expected Sources:**
* `kaggle` - Largest volume (~80K records)
* `nuforc` - Web-scraped (dependent on site availability)
* `huggingface` - Smaller, declassified dataset

---

## ⚙️ Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PROJECT_ID` | uap-scraper-lab-2026 | GCP project ID |
| `GCS_RAW_BUCKET` | uap-scraper-lab-2026-scraper-raw | Output bucket |
| `PARALLEL_COLLECTION` | true | Collect from sources in parallel |
| `MAX_RECORDS_PER_SOURCE` | 1000 | Limit per source (testing) |

### Function Settings

| Setting | Value | Why? |
|---------|-------|------|
| Memory | 2GB | Kaggle CSV datasets can be large |
| Timeout | 540s | Multi-source collection takes time |
| Max Instances | 5 | Cost control |
| Min Instances | 0 | Scale to zero when idle |

---

## 🔧 Troubleshooting

### Issue: "Permission Denied" Error

**Solution:**
```bash
# Grant necessary roles
gcloud projects add-iam-policy-binding uap-scraper-lab-2026 \
  --member="user:YOUR_EMAIL@gmail.com" \
  --role="roles/cloudfunctions.admin"

gcloud projects add-iam-policy-binding uap-scraper-lab-2026 \
  --member="user:YOUR_EMAIL@gmail.com" \
  --role="roles/iam.serviceAccountUser"
```

### Issue: Function Times Out

**Symptoms:** 503 errors, "deadline exceeded"

**Solutions:**
1. Reduce `MAX_RECORDS_PER_SOURCE` (e.g., 500)
2. Disable slow sources temporarily
3. Increase timeout to 540s (maximum)

### Issue: No Data in GCS

**Debugging:**
```bash
# Check if function ran
gcloud functions logs read uap-multi-source-scraper --limit=20

# Verify bucket permissions
gsutil iam get gs://uap-scraper-lab-2026-scraper-raw

# Test write access
echo "test" | gsutil cp - gs://uap-scraper-lab-2026-scraper-raw/test.txt
```

### Issue: Kaggle API Not Working

**Error:** "401 Unauthorized" or "Kaggle credentials not found"

**Solution:**
Kaggle requires API credentials. For now, other sources (NUFORC, HuggingFace) will still work. The function is fault-tolerant - one source failing doesn't stop the others.

---

## 📅 Optional: Set Up Scheduled Runs

### Using Cloud Scheduler

Run the scraper daily at 2 AM UTC:

```bash
# Create scheduler job
gcloud scheduler jobs create http uap-daily-scrape \
  --location=us-central1 \
  --schedule="0 2 * * *" \
  --uri="<YOUR_FUNCTION_URL>" \
  --http-method=POST \
  --time-zone="UTC"

# Trigger manually
gcloud scheduler jobs run uap-daily-scrape --location=us-central1

# View scheduler logs
gcloud scheduler jobs describe uap-daily-scrape --location=us-central1
```

### Cost Estimate

With daily runs:
* **Cloud Function**: ~$0.10/month
* **Storage (GCS)**: ~$0.05/month (100MB)
* **Total**: **~$0.15/month**

---

## 🚀 Next Steps

After successful deployment:

1. **Trigger First Scrape**
   ```bash
   curl -X POST <YOUR_FUNCTION_URL>
   ```

2. **Monitor GCS Bucket**
   ```bash
   watch -n 5 'gsutil ls gs://uap-scraper-lab-2026-scraper-raw/raw_ingest/'
   ```

3. **Run Databricks Pipeline**
   - Open [Databricks Job 848810085365964](#job-848810085365964)
   - Click "Run Now"
   - Monitor bronze → silver → gold flow

4. **Verify Data Quality**
   ```sql
   SELECT 
     data_source,
     COUNT(*) as records,
     COUNT(DISTINCT city) as unique_cities,
     MIN(date_time) as earliest,
     MAX(date_time) as latest
   FROM workspace.default.silver_uap_structured
   GROUP BY data_source
   ```

5. **Set Up Monitoring** (Optional)
   - Cloud Function metrics dashboard
   - GCS bucket size alerts
   - Databricks job success/failure alerts

---

## 📚 Additional Resources

* **Cloud Functions Docs**: https://cloud.google.com/functions/docs
* **GCS Python Client**: https://cloud.google.com/storage/docs/reference/libraries#client-libraries-install-python
* **Cloud Scheduler**: https://cloud.google.com/scheduler/docs
* **Project README**: [../README.md](../README.md)
* **Scraper Architecture**: [MULTI_SOURCE_README.md](MULTI_SOURCE_README.md)

---

## 💡 Tips

* **Start Small**: Use `MAX_RECORDS_PER_SOURCE=100` for initial testing
* **Monitor Costs**: Check GCP billing dashboard weekly
* **Incremental Updates**: The orchestrator supports resuming failed collections
* **Source Failures**: If one source fails, others continue (fault tolerance)
* **Logs Are Your Friend**: Always check logs after deployment

---

**Need Help?**

Check the logs first:
```bash
gcloud functions logs read uap-multi-source-scraper --region=us-central1 --limit=100
```

Look for ERROR or WARNING messages and search the [troubleshooting section](#troubleshooting) above.
