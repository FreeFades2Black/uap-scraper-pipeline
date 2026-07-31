# Multi-Source UAP Data Aggregator

**Collects UAP (Unidentified Aerial Phenomena) sighting data from 10+ open-source repositories**

## 🎯 Supported Data Sources

### ✅ Currently Implemented
1. **Kaggle** - Structured CSV datasets (NUFORC comprehensive exports)
2. **Hugging Face** - FBI/DoD declassified records via `reducto/ufocr` dataset
3. **NUFORC** - National UFO Reporting Center (web scraping with anti-block measures)
4. **MUFON** - Mutual UFO Network (placeholder - needs API key)
5. **NASA UAP** - NASA UAP Independent Study reports (placeholder - needs parsing)
6. **UFO Stalker** - Interactive mapping database (placeholder - API investigation needed)

### 🔧 Planned Additions
7. **AARO** - All-domain Anomaly Resolution Office (aaro.mil)
8. **Black Vault** - FOIA declassified documents (theblackvault.com)
9. **NARA** - National Archives UAP files (archives.gov)
10. **CUFOS** - J. Allen Hynek Center archives (cufos.org)

---

## 📊 Architecture

```
scraper/
├── src/
│   ├── main.py                    # Orchestrator entry point
│   ├── orchestrator.py            # Multi-source coordinator
│   └── collectors/
│       ├── base.py               # Base collector class
│       ├── nuforc_collector.py
│       ├── kaggle_collector.py
│       ├── mufon_collector.py
│       ├── nasa_collector.py
│       ├── huggingface_collector.py
│       └── ufostalker_collector.py
├── requirements.txt
└── main.py                        # Cloud Functions entry point
```

---

## 🚀 How It Works

1. **Orchestrator** instantiates all collectors
2. Runs collectors in **parallel** (configurable) with error handling
3. Each collector normalizes data to a **standard schema**:
   ```json
   {
     "date_time": "MM/DD/YYYY HH:MM",
     "city": "Phoenix",
     "state": "AZ",
     "country": "USA",
     "shape": "Triangle",
     "duration": "5 minutes",
     "summary": "Large triangular craft with lights...",
     "report_link": "https://...",
     "data_source": "NUFORC"
   }
   ```
4. Consolidates all sources into **single JSON payload**
5. Uploads to **GCS bucket** for Databricks ingestion

---

## 🔑 Environment Variables

```bash
# Required
GCS_RAW_BUCKET=uap-scraper-lab-2026-scraper-raw

# Optional
PARALLEL_COLLECTION=true          # Run collectors in parallel
MAX_WORKERS=5                      # Max parallel threads
```

---

## 📦 Installation

```bash
cd scraper
pip install -r requirements.txt
```

---

## 🧪 Local Testing

```bash
python -m src.main
```

---

## ☁️ Cloud Function Deployment

```bash
gcloud functions deploy uap-scraper \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=. \
  --entry-point=cloud_function_entry \
  --trigger-http \
  --memory=512MB \
  --timeout=540s \
  --set-env-vars="GCS_RAW_BUCKET=uap-scraper-lab-2026-scraper-raw" \
  --project=uap-scraper-lab-2026
```

---

## 📈 Output Format

```json
{
  "collection_timestamp": "2026-07-31T08:00:00.000Z",
  "total_sightings": 1243,
  "successful_sources": 3,
  "source_breakdown": {
    "Kaggle": {"count": 1000, "success": true},
    "NUFORC": {"count": 243, "success": true},
    "HuggingFace": {"count": 0, "success": false, "error": "..."}
  },
  "all_sightings": [...]
}
```

---

## 🔍 Adding New Sources

1. Create new collector in `src/collectors/<source>_collector.py`
2. Inherit from `BaseCollector`
3. Implement `collect()` method
4. Add to orchestrator in `src/orchestrator.py`
5. Update `requirements.txt` if new dependencies needed

---

## 🛠️ Troubleshooting

**403 Forbidden from NUFORC**
- Cloud IPs are often blocked
- Scraper retries with exponential backoff
- Falls back to other sources automatically

**Kaggle API Authentication**
- Requires `KAGGLE_USERNAME` and `KAGGLE_KEY` env vars
- Or place `~/.kaggle/kaggle.json` credential file

**Hugging Face Datasets**
- Requires `datasets` library
- Some datasets may need HF account token

---

## 📝 License

Open-source for UAP research and transparency.
