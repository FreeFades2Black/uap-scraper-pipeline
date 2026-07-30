#!/bin/bash
# One-command deployment script for UAP scraper to Google Cloud Functions
# Usage: ./deploy.sh

set -e  # Exit on error

# Configuration
PROJECT_ID="uap-scraper-lab-2026"
REGION="us-central1"
FUNCTION_NAME="uap-scraper"
GCS_BUCKET="${PROJECT_ID}-scraper-raw"
SCHEDULE="0 2 * * *"  # Daily at 2 AM UTC

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║       UAP SCRAPER → CLOUD FUNCTIONS DEPLOYMENT           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "📋 Configuration:"
echo "   Project:  $PROJECT_ID"
echo "   Region:   $REGION"
echo "   Function: $FUNCTION_NAME"
echo "   Bucket:   gs://$GCS_BUCKET"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI not found"
    echo "   Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Error: Not authenticated with gcloud"
    echo "   Run: gcloud auth login"
    exit 1
fi

echo "✅ Prerequisites verified"
echo ""

# Step 1: Enable required APIs
echo "🔧 Step 1/4: Enabling required GCP APIs..."
gcloud services enable \
  cloudfunctions.googleapis.com \
  cloudscheduler.googleapis.com \
  cloudbuild.googleapis.com \
  --project=$PROJECT_ID \
  --quiet

echo "✅ APIs enabled"
echo ""

# Step 2: Deploy Cloud Function
echo "🚀 Step 2/4: Deploying Cloud Function..."
echo "   (This takes ~2-3 minutes)"

gcloud functions deploy $FUNCTION_NAME \
  --gen2 \
  --runtime=python311 \
  --region=$REGION \
  --source=. \
  --entry-point=cloud_function_entry \
  --trigger-http \
  --allow-unauthenticated \
  --memory=512MB \
  --timeout=540s \
  --set-env-vars="GCS_RAW_BUCKET=$GCS_BUCKET" \
  --project=$PROJECT_ID \
  --quiet

echo "✅ Cloud Function deployed"
echo ""

# Step 3: Get function URL
FUNCTION_URL=$(gcloud functions describe $FUNCTION_NAME \
  --gen2 \
  --region=$REGION \
  --project=$PROJECT_ID \
  --format='value(serviceConfig.uri)')

echo "📍 Function URL: $FUNCTION_URL"
echo ""

# Step 4: Set up Cloud Scheduler
echo "⏰ Step 3/4: Setting up Cloud Scheduler..."

# Check if job already exists
if gcloud scheduler jobs describe ${FUNCTION_NAME}-daily \
  --location=$REGION \
  --project=$PROJECT_ID &>/dev/null; then
  
  echo "   Scheduler job exists, updating..."
  gcloud scheduler jobs update http ${FUNCTION_NAME}-daily \
    --location=$REGION \
    --schedule="$SCHEDULE" \
    --uri=$FUNCTION_URL \
    --http-method=GET \
    --project=$PROJECT_ID \
    --quiet
else
  echo "   Creating new scheduler job..."
  gcloud scheduler jobs create http ${FUNCTION_NAME}-daily \
    --location=$REGION \
    --schedule="$SCHEDULE" \
    --uri=$FUNCTION_URL \
    --http-method=GET \
    --time-zone="UTC" \
    --project=$PROJECT_ID \
    --quiet
fi

echo "✅ Cloud Scheduler configured: Daily at 2 AM UTC"
echo ""

# Step 5: Test the function
echo "🧪 Step 4/4: Testing the function..."
echo "   Triggering scraper..."

RESPONSE=$(curl -s -w "\n%{http_code}" $FUNCTION_URL)
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Function test successful!"
    echo "   Response: $BODY"
else
    echo "⚠️  Function returned HTTP $HTTP_CODE"
    echo "   Response: $BODY"
    echo "   Check logs: gcloud functions logs read $FUNCTION_NAME --region=$REGION --limit=50"
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                   🎉 DEPLOYMENT COMPLETE!                 ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Summary:"
echo "   • Function URL:  $FUNCTION_URL"
echo "   • Schedule:      Daily at 2 AM UTC"
echo "   • GCS Bucket:    gs://$GCS_BUCKET/raw_ingest/"
echo "   • Cost:          ~\$0.10/month"
echo ""
echo "📝 Useful Commands:"
echo ""
echo "   # View logs"
echo "   gcloud functions logs read $FUNCTION_NAME --region=$REGION --limit=50"
echo ""
echo "   # Trigger manually"
echo "   curl $FUNCTION_URL"
echo ""
echo "   # Run scheduler job now"
echo "   gcloud scheduler jobs run ${FUNCTION_NAME}-daily --location=$REGION"
echo ""
echo "   # List scraped files"
echo "   gsutil ls gs://$GCS_BUCKET/raw_ingest/"
echo ""
echo "   # View latest file"
echo "   gsutil cat gs://$GCS_BUCKET/raw_ingest/uap_sightings_*.json | jq ."
echo ""
echo "🚀 Next: Update your bronze notebook to parse UAP sighting schema"
echo ""