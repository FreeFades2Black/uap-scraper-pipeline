#!/bin/bash
# ========================================
# UAP Multi-Source Scraper Deployment
# ========================================

set -e  # Exit on error

# Configuration
PROJECT_ID="uap-scraper-lab-2026"
FUNCTION_NAME="uap-multi-source-scraper"
REGION="us-central1"
RUNTIME="python311"
ENTRY_POINT="cloud_function_entry"
GCS_RAW_BUCKET="uap-scraper-lab-2026-scraper-raw"
GCS_STAGING_BUCKET="uap-scraper-lab-2026-lakehouse-data"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   🛸 UAP MULTI-SOURCE SCRAPER DEPLOYMENT               ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "📋 Configuration:"
echo "   Project:     ${PROJECT_ID}"
echo "   Function:    ${FUNCTION_NAME}"
echo "   Region:      ${REGION}"
echo "   Runtime:     ${RUNTIME}"
echo "   Entry Point: ${ENTRY_POINT}"
echo "   Raw Bucket:  gs://${GCS_RAW_BUCKET}"
echo ""

# Check prerequisites
echo "🔍 Checking prerequisites..."

if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI not found"
    echo "   Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Error: Not authenticated with gcloud"
    echo "   Run: gcloud auth login"
    exit 1
fi

echo "✅ Prerequisites verified"
echo ""

# Set the project
echo "🔧 Setting project to ${PROJECT_ID}..."
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable \
  cloudfunctions.googleapis.com \
  cloudbuild.googleapis.com \
  cloudscheduler.googleapis.com \
  storage-api.googleapis.com \
  run.googleapis.com \
  --project=${PROJECT_ID} \
  --quiet 2>/dev/null || echo "   APIs already enabled"

echo "✅ APIs enabled"
echo ""

# Deploy the function
echo "🚀 Deploying Cloud Function (Gen2)..."
echo "   This may take 3-5 minutes..."
echo ""

gcloud functions deploy ${FUNCTION_NAME} \
  --gen2 \
  --runtime=${RUNTIME} \
  --region=${REGION} \
  --source=. \
  --entry-point=${ENTRY_POINT} \
  --trigger-http \
  --allow-unauthenticated \
  --memory=2GB \
  --timeout=540s \
  --max-instances=5 \
  --min-instances=0 \
  --set-env-vars="PROJECT_ID=${PROJECT_ID},GCS_RAW_BUCKET=${GCS_RAW_BUCKET},GCS_STAGING_BUCKET=${GCS_STAGING_BUCKET},PARALLEL_COLLECTION=true,MAX_RECORDS_PER_SOURCE=1000" \
  --project=${PROJECT_ID} \
  --quiet

echo ""
echo "✅ Cloud Function deployed successfully!"
echo ""

# Get function URL
echo "📍 Retrieving function URL..."
FUNCTION_URL=$(gcloud functions describe ${FUNCTION_NAME} \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --gen2 \
  --format="value(serviceConfig.uri)")

echo "   Function URL: ${FUNCTION_URL}"
echo ""

# Test the function
echo "🧪 Testing the function..."
echo "   Triggering multi-source collection..."
echo ""

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST ${FUNCTION_URL})
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Function test successful!"
    echo "   Response preview:"
    echo "$BODY" | head -20
else
    echo "⚠️  Function returned HTTP $HTTP_CODE"
    echo "   Response: $BODY"
    echo "   Check logs below..."
fi

echo ""
echo "📊 Recent logs:"
gcloud functions logs read ${FUNCTION_NAME} \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --limit=20 \
  --format="table(time_utc, severity, log)"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║              🎉 DEPLOYMENT COMPLETE!                      ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Summary:"
echo "   • Function:      ${FUNCTION_NAME}"
echo "   • URL:           ${FUNCTION_URL}"
echo "   • Raw Bucket:    gs://${GCS_RAW_BUCKET}/raw_ingest/"
echo "   • Memory:        2GB"
echo "   • Timeout:       540s (9 minutes)"
echo "   • Max Instances: 5"
echo ""
echo "🎯 Active Data Sources:"
echo "   • Kaggle         - NUFORC CSV datasets (~80K records)"
echo "   • NUFORC         - Web scraping with fallback URLs"
echo "   • HuggingFace    - FBI/DoD declassified records"
echo "   • MUFON          - Placeholder (needs API key)"
echo "   • NASA UAP       - Placeholder"
echo "   • UFO Stalker    - Placeholder"
echo ""
echo "📝 Useful Commands:"
echo ""
echo "   # View logs"
echo "   gcloud functions logs read ${FUNCTION_NAME} --region=${REGION} --limit=50"
echo ""
echo "   # Trigger manually"
echo "   curl -X POST ${FUNCTION_URL}"
echo ""
echo "   # List scraped files"
echo "   gsutil ls gs://${GCS_RAW_BUCKET}/raw_ingest/"
echo ""
echo "   # Download latest file"
echo "   gsutil cp gs://${GCS_RAW_BUCKET}/raw_ingest/uap_sightings_*.json ./"
echo ""
echo "   # View latest file (pretty print)"
echo "   gsutil cat gs://${GCS_RAW_BUCKET}/raw_ingest/uap_sightings_*.json | jq . | head -100"
echo ""
echo "🚀 Next Steps:"
echo "   1. Check GCS bucket for output files"
echo "   2. Run Databricks bronze ingestion notebook"
echo "   3. Verify data loaded into workspace.default.bronze_uap_raw"
echo "   4. Set up Cloud Scheduler for recurring scrapes (optional)"
echo ""
