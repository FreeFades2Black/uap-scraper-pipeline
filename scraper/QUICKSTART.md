# ⚡ Quick Start - Deploy in 5 Minutes

The fastest way to get your UAP scraper running on GCP!

---

## 🎯 Option 1: Google Cloud Shell (Recommended)

**No installation needed!** Deploy directly from your browser.

### Step 1: Open Cloud Shell

1. Go to: https://console.cloud.google.com
2. Click the **Cloud Shell** icon (top-right corner, looks like `>_`)
3. Wait for the terminal to load

### Step 2: Clone and Deploy

Copy and paste these commands:

\`\`\`bash
# Clone your repository
git clone https://github.com/YOUR_USERNAME/uap-scraper-pipeline.git
cd uap-scraper-pipeline/scraper

# Make script executable and deploy
chmod +x deploy-multi-source.sh
./deploy-multi-source.sh
\`\`\`

### Step 3: Save Your Function URL

The script will output something like:
\`\`\`
Function URL: https://uap-multi-source-scraper-xa24reym7q-uc.a.run.app
\`\`\`

**Save this URL!** You'll need it for:
* Manual triggers
* Databricks integration
* Cloud Scheduler setup

### Step 4: Test It

\`\`\`bash
# Trigger a scrape
curl -X POST https://YOUR_FUNCTION_URL

# Check for output files (wait ~2 minutes)
gsutil ls gs://uap-scraper-lab-2026-scraper-raw/raw_ingest/

# View the latest file
gsutil cat gs://uap-scraper-lab-2026-scraper-raw/raw_ingest/uap_sightings_*.json | jq . | head -50
\`\`\`

---

## 🎯 Option 2: Local Machine

If you have gcloud CLI installed:

\`\`\`bash
# Navigate to scraper directory
cd uap-scraper-pipeline/scraper

# Run deployment script
./deploy-multi-source.sh
\`\`\`

**Don't have gcloud?** Install it: https://cloud.google.com/sdk/docs/install

---

## ✅ Success Checklist

After deployment completes:

- [ ] Function deployed without errors
- [ ] Function URL saved
- [ ] Test curl succeeds (HTTP 200)
- [ ] Files appear in GCS bucket
- [ ] JSON structure looks correct

---

## 🚀 Next: Run Your Databricks Pipeline

1. Open your Databricks workspace
2. Navigate to [Job 848810085365964](#job-848810085365964)
3. Click **"Run Now"**
4. Monitor the pipeline:
   - Bronze ingestion pulls from GCS
   - Silver transformation parses UAP fields
   - Gold aggregation creates analytics tables

---

## 🔧 Quick Commands

\`\`\`bash
# View logs
gcloud functions logs read uap-multi-source-scraper --region=us-central1 --limit=20

# Trigger scrape
curl -X POST <YOUR_FUNCTION_URL>

# List output files
gsutil ls gs://uap-scraper-lab-2026-scraper-raw/raw_ingest/

# Download latest
gsutil cp gs://uap-scraper-lab-2026-scraper-raw/raw_ingest/uap_sightings_*.json ./
\`\`\`

---

## 📚 Need More Details?

* **Full Deployment Guide**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
* **Scraper Architecture**: [MULTI_SOURCE_README.md](MULTI_SOURCE_README.md)
* **Project Overview**: [../README.md](../README.md)

---

## 💡 Troubleshooting

**Function times out?**
* Reduce MAX_RECORDS_PER_SOURCE in deploy script (line 16)

**Permission denied?**
* Make sure you're the project owner or have Cloud Functions Admin role

**No data in GCS?**
* Check logs for errors: \`gcloud functions logs read uap-multi-source-scraper --limit=50\`
* Verify bucket exists: \`gsutil ls gs://uap-scraper-lab-2026-scraper-raw/\`

**Need help?**
* Check [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) troubleshooting section
