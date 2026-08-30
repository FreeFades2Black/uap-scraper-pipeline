# ==============================================================================
# Multi-Stage Production Dockerfile for UAP Scraper Pipeline
# ==============================================================================

# Build Stage: Compile and install dependencies
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    gcc \
    libxml2-dev \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

COPY scraper/requirements.txt requirements.txt
RUN pip install --no-cache-dir --user -r requirements.txt


# Final Production Image
FROM python:3.11-slim AS runtime

LABEL maintainer="FreeFades2Black <whall4.wh@gmail.com>" \
      description="UAP Multi-Source Scraping & Lakehouse Ingestion Engine" \
      version="2.0.0"

WORKDIR /app

# Install runtime system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    libxml2 \
    libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed python wheels/packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    GCS_RAW_BUCKET=uap-scraper-lab-2026-scraper-raw \
    LOCAL_OUTPUT_DIR=/app/data/output \
    API_PORT=8080 \
    API_HOST=0.0.0.0

# Create dedicated non-root service account
RUN groupadd -g 10001 uap && \
    useradd -u 10001 -g uap -s /bin/bash -m uapuser && \
    mkdir -p /app/data/output /app/data/logs && \
    chown -R uapuser:uap /app /root/.local

# Copy application source tree
COPY --chown=uapuser:uap scraper/ ./scraper/
COPY --chown=uapuser:uap entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

USER uapuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/healthz || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["api"]
