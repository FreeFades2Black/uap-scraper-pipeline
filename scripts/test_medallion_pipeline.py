#!/usr/bin/env python3
"""Local Test Runner for Medallion Architecture (Bronze -> Silver -> Gold)."""
import glob
import json
import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath("."))

import pandas as pd
import numpy as np

OUTPUT_DIR = "./data/output"


def run_bronze_stage(file_path: str) -> pd.DataFrame:
    """Stage 1 (Bronze): Ingest raw JSON envelope and explode individual sightings."""
    print(f"\n[1/3] 🥉 Executing Bronze Ingestion on: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        envelope = json.load(f)

    sightings = envelope.get("all_sightings", [])
    if not sightings:
        raise ValueError("No sightings array found in raw JSON envelope")

    df_bronze = pd.DataFrame(sightings)
    df_bronze["_ingest_timestamp"] = pd.Timestamp.now(tz="UTC")
    df_bronze["_source_file"] = os.path.basename(file_path)
    df_bronze["_envelope_successful_sources"] = envelope.get("successful_sources", 0)

    print(f"      ✅ Bronze records extracted: {len(df_bronze)}")
    print(f"      ✅ Bronze schema columns: {list(df_bronze.columns)}")
    return df_bronze


def run_silver_stage(df_bronze: pd.DataFrame) -> pd.DataFrame:
    """Stage 2 (Silver): Normalize, clean, classify shapes, and attach quality flags."""
    print(f"\n[2/3] 🥈 Executing Silver Transformation & Normalization...")
    df_silver = df_bronze.copy()

    # Deduplicate on content hash
    initial_len = len(df_silver)
    if "sighting_hash" in df_silver.columns:
        df_silver = df_silver.drop_duplicates(subset=["sighting_hash"])
    print(f"      Deduplication: {initial_len} -> {len(df_silver)} records")

    # Temporal Normalization (handling mixed dates like MM/DD/YYYY HH:MM and YYYY-MM-DD)
    df_silver["sighting_timestamp"] = pd.to_datetime(df_silver["date_time"], format="mixed", errors="coerce")
    df_silver["sighting_year"] = df_silver["sighting_timestamp"].dt.year

    # Geographic Normalization
    df_silver["city"] = df_silver["city"].fillna("Unknown").astype(str).str.strip().str.title()
    df_silver["state"] = df_silver["state"].fillna("UNKNOWN").astype(str).str.strip().str.upper()
    df_silver["country"] = df_silver["country"].fillna("USA").astype(str).str.strip().str.upper()
    df_silver["latitude"] = pd.to_numeric(df_silver.get("latitude"), errors="coerce")
    df_silver["longitude"] = pd.to_numeric(df_silver.get("longitude"), errors="coerce")

    # Shape Classification Taxonomy
    def classify_shape(val: str) -> str:
        s = str(val).lower().strip()
        if "triang" in s:
            return "Triangle"
        elif "disk" in s or "saucer" in s:
            return "Disk"
        elif "sphere" in s or "orb" in s or "globe" in s:
            return "Sphere"
        elif "light" in s or "flash" in s or "fireball" in s:
            return "Light"
        elif "cigar" in s or "cylind" in s:
            return "Cigar"
        elif "chevron" in s or "v-shape" in s:
            return "Chevron"
        elif "oval" in s or "egg" in s:
            return "Oval"
        elif "diamond" in s:
            return "Diamond"
        elif "formation" in s:
            return "Formation"
        elif any(k in s for k in ["declassified", "study", "sensor"]):
            return "Military / Scientific"
        return "Other / Unknown"

    df_silver["shape_raw"] = df_silver.get("shape", "Unknown")
    df_silver["shape_classified"] = df_silver["shape_raw"].apply(classify_shape)

    # Data Quality Flags
    df_silver["has_valid_timestamp"] = df_silver["sighting_timestamp"].notna()
    df_silver["has_coordinates"] = df_silver["latitude"].notna() & df_silver["longitude"].notna()
    df_silver["has_known_shape"] = df_silver["shape_classified"] != "Other / Unknown"

    print(f"      ✅ Silver clean records: {len(df_silver)}")
    print(f"      ✅ Valid Timestamps: {df_silver['has_valid_timestamp'].sum()} ({round(df_silver['has_valid_timestamp'].mean()*100, 1)}%)")
    print(f"      ✅ With Geocoordinates: {df_silver['has_coordinates'].sum()} ({round(df_silver['has_coordinates'].mean()*100, 1)}%)")
    print(f"      ✅ Classified Shapes: {df_silver['has_known_shape'].sum()} ({round(df_silver['has_known_shape'].mean()*100, 1)}%)")
    return df_silver


def run_gold_stage(df_silver: pd.DataFrame) -> dict:
    """Stage 3 (Gold): Business aggregations, KPIs, and analytics tables."""
    print(f"\n[3/3] 🥇 Executing Gold Summary & Analytics Aggregations...")

    # 1. Overall Scorecard
    total_records = len(df_silver)
    scorecard = {
        "total_sightings": total_records,
        "unique_sources": int(df_silver["data_source"].nunique()),
        "unique_states": int(df_silver["state"].nunique()),
        "unique_cities": int(df_silver["city"].nunique()),
        "earliest_sighting": str(df_silver["sighting_timestamp"].min()),
        "latest_sighting": str(df_silver["sighting_timestamp"].max()),
        "coordinate_coverage_pct": round(df_silver["has_coordinates"].mean() * 100, 2),
        "shape_classification_pct": round(df_silver["has_known_shape"].mean() * 100, 2)
    }

    # 2. Location Distribution (Top 10 States)
    by_location = (
        df_silver.groupby(["country", "state"])
        .agg(
            total_sightings=("city", "count"),
            unique_cities=("city", "nunique"),
            geocoded_count=("has_coordinates", "sum")
        )
        .reset_index()
        .sort_values(by="total_sightings", ascending=False)
    )

    # 3. Shape Distribution
    by_shape = (
        df_silver.groupby("shape_classified")
        .agg(
            sighting_count=("city", "count"),
            states_reported=("state", "nunique"),
            sources=("data_source", "nunique")
        )
        .reset_index()
        .sort_values(by="sighting_count", ascending=False)
    )
    by_shape["pct_of_total"] = (by_shape["sighting_count"] / total_records * 100).round(2)

    # 4. Source Breakdown & Quality
    by_source = (
        df_silver.groupby("data_source")
        .agg(
            total_records=("city", "count"),
            valid_timestamps=("has_valid_timestamp", "sum"),
            with_coordinates=("has_coordinates", "sum"),
            with_known_shape=("has_known_shape", "sum")
        )
        .reset_index()
        .sort_values(by="total_records", ascending=False)
    )
    by_source["quality_score_pct"] = (
        (by_source["valid_timestamps"] + by_source["with_coordinates"] + by_source["with_known_shape"]) /
        (by_source["total_records"] * 3) * 100
    ).round(2)

    # 5. Timeline Distribution (Top Recent Years)
    by_year = (
        df_silver[df_silver["sighting_year"].notna()]
        .groupby("sighting_year")
        .agg(
            annual_sightings=("city", "count"),
            states_reporting=("state", "nunique")
        )
        .reset_index()
        .sort_values(by="sighting_year", ascending=False)
    )
    by_year["sighting_year"] = by_year["sighting_year"].astype(int)

    return {
        "scorecard": scorecard,
        "by_location": by_location,
        "by_shape": by_shape,
        "by_source": by_source,
        "by_year": by_year
    }


def main():
    print("=" * 70)
    print("🛸 UAP LAKEHOUSE MEDALLION PIPELINE TEST RUNNER")
    print("=" * 70)

    # Re-run fresh multi-source scrape with improved column mapping
    from scraper.src.main import run_pipeline
    print("🚀 Triggering fresh multi-source ingestion run...")
    result = run_pipeline(parallel=True, upload_gcs=False, local_output=OUTPUT_DIR)
    
    json_files = sorted(glob.glob(f"{OUTPUT_DIR}/uap_sightings_*.json"))
    latest_file = json_files[-1]
    print(f"Target Input File: {latest_file}")

    try:
        # Run Bronze -> Silver -> Gold
        df_bronze = run_bronze_stage(latest_file)
        df_silver = run_silver_stage(df_bronze)
        gold = run_gold_stage(df_silver)

        print("\n" + "=" * 70)
        print("📊 GOLD ANALYTICS RESULTS & BUSINESS INTELLIGENCE")
        print("=" * 70)

        print("\n🏆 1. Overall Scorecard Summary:")
        for k, v in gold["scorecard"].items():
            print(f"   • {k:25}: {v}")

        print("\n🗺️ 2. Top 10 Sightings by Location (State/Country):")
        print(gold["by_location"].head(10).to_string(index=False))

        print("\n🛸 3. Object Shape Classification Distribution:")
        print(gold["by_shape"].to_string(index=False))

        print("\n📡 4. Source Reliability & Ingestion Quality Scorecard:")
        print(gold["by_source"].to_string(index=False))

        print("\n📅 5. Annual Sighting Timeline (Most Recent Active Years):")
        print(gold["by_year"].head(10).to_string(index=False))

        print("\n" + "=" * 70)
        print("✅ ALL 3 MEDALLION PROCESSES COMPLETED WITH ZERO STALLS")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Pipeline stalled during Medallion execution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
