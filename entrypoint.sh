#!/usr/bin/env bash
# ==============================================================================
# UAP Scraper Multi-Mode Container Entrypoint Script
# Modes:
#   - "api" / "server" : Starts FastAPI daemon on port 8080 with health checks
#   - "scrape" / "run" : Runs a one-time multi-source scrape pipeline execution
#   - "cron"           : Runs recurring scraper daemon every $CRON_INTERVAL
#   - "test"           : Runs automated pytest test suite
# ==============================================================================
set -e

MODE="${1:-api}"

echo "========================================================"
echo "🛸 UAP Scraper Container Initializing [Mode: ${MODE}]"
echo "========================================================"

mkdir -p /app/data/output /app/data/logs

if [ "$MODE" = "api" ] || [ "$MODE" = "server" ]; then
    echo "[+] Launching UAP Scraper FastAPI Daemon on port ${API_PORT:-8080}..."
    exec python -m uvicorn scraper.src.api:app --host "${API_HOST:-0.0.0.0}" --port "${API_PORT:-8080}" --workers "${UVICORN_WORKERS:-2}"

elif [ "$MODE" = "scrape" ] || [ "$MODE" = "run" ] || [ "$MODE" = "cli" ]; then
    shift || true
    echo "[+] Running one-shot UAP multi-source scrape job..."
    exec python -m scraper.src.main "$@"

elif [ "$MODE" = "cron" ]; then
    INTERVAL="${CRON_INTERVAL:-21600}" # Default: every 6 hours (21600s)
    echo "[+] Starting continuous Cron Daemon with interval: ${INTERVAL}s..."
    while true; do
        echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Starting scheduled scrape iteration..."
        python -m scraper.src.main || echo "⚠️ Scrape run encountered errors, continuing schedule..."
        echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Sleeping for ${INTERVAL} seconds..."
        sleep "$INTERVAL"
    done

elif [ "$MODE" = "test" ]; then
    echo "[+] Running automated test suite..."
    exec pytest -v tests/

else
    echo "[+] Executing custom command: $@"
    exec "$@"
fi
