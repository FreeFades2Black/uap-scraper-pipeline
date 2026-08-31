"""
02_silver_transformation.py

Internal Module Implementation with comprehensive inline documentation.
Part of the FreeFades2Black enterprise ecosystem.
"""
# Databricks notebook source
# DBTITLE 1,Silver Layer - Structure, Normalize & Validate UAP Sightings
# MAGIC %md
# MAGIC # 02 - Silver Layer Transformation
# MAGIC 
# MAGIC Transforms raw bronze UAP sighting data into structured, validated, and normalized Silver Delta tables.
# MAGIC 
# MAGIC **Bronze → Silver Transformations:**
# MAGIC - Deduplicate on deterministic `sighting_hash`
# MAGIC - Parse heterogeneous date/time strings to standard `sighting_timestamp`
# MAGIC - Standardize and classify UAP `shape` taxonomy
# MAGIC - Parse duration strings and numeric seconds
# MAGIC - Clean and validate geographic fields (`city`, `state`, `country`, `latitude`, `longitude`)
# MAGIC - Attach quality flags (`has_coordinates`, `has_valid_timestamp`, `has_classified_shape`)

# COMMAND ----------

# DBTITLE 1,Configuration
BRONZE_TABLE = "workspace.default.bronze_uap_raw"
SILVER_TABLE = "workspace.default.silver_uap_structured"

print(f"Source: {BRONZE_TABLE}")
print(f"Target: {SILVER_TABLE}")

# COMMAND ----------

# DBTITLE 1,BATCH: Normalize, Clean & Deduplicate
from pyspark.sql.functions import (
    col, current_timestamp, when, to_timestamp, trim, upper, initcap,
    coalesce, lit, regexp_replace, cast
)

# Read from bronze
df_bronze = spark.read.table(BRONZE_TABLE)

# Standardize and clean fields
df_silver = (
    df_bronze
    # Deduplicate on content hash
    .dropDuplicates(["sighting_hash"])
    
    # Core identifiers & sources
    .withColumn("sighting_id", coalesce(col("sighting_hash"), col("date_time")))
    .withColumn("data_source", upper(trim(coalesce(col("data_source"), lit("UNKNOWN")))))
    
    # Temporal normalization (try multiple format patterns)
    .withColumn("sighting_timestamp", 
        coalesce(
            to_timestamp(col("date_time"), "yyyy-MM-dd HH:mm:ss"),
            to_timestamp(col("date_time"), "MM/dd/yyyy HH:mm"),
            to_timestamp(col("date_time"), "yyyy-MM-dd"),
            to_timestamp(col("date_time"), "MM/dd/yyyy"),
            to_timestamp(col("date_time"))
        )
    )
    
    # Geographic normalization
    .withColumn("city", initcap(trim(coalesce(col("city"), lit("Unknown")))))
    .withColumn("state", upper(trim(coalesce(col("state"), lit("UNKNOWN")))))
    .withColumn("country", upper(trim(coalesce(col("country"), lit("USA")))))
    .withColumn("latitude", col("latitude").cast("double"))
    .withColumn("longitude", col("longitude").cast("double"))
    
    # Shape classification
    .withColumn("shape_raw", trim(coalesce(col("shape"), lit("Unknown"))))
    .withColumn("shape_classified",
        when(col("shape_raw").rlike("(?i)triang"), "Triangle")
        .when(col("shape_raw").rlike("(?i)disk|saucer"), "Disk")
        .when(col("shape_raw").rlike("(?i)sphere|orb|globe"), "Sphere")
        .when(col("shape_raw").rlike("(?i)light|flash|fireball"), "Light")
        .when(col("shape_raw").rlike("(?i)cigar|cylind"), "Cigar")
        .when(col("shape_raw").rlike("(?i)chevron|v-shape"), "Chevron")
        .when(col("shape_raw").rlike("(?i)oval|egg"), "Oval")
        .when(col("shape_raw").rlike("(?i)diamond"), "Diamond")
        .when(col("shape_raw").rlike("(?i)formation"), "Formation")
        .when(col("shape_raw").rlike("(?i)declassified|study|sensor"), "Military / Scientific")
        .otherwise("Other / Unknown")
    )
    
    # Duration and summary
    .withColumn("duration_text", trim(coalesce(col("duration"), lit("Unknown"))))
    .withColumn("summary_clean", trim(coalesce(col("summary"), lit(""))))
    .withColumn("report_link", col("report_link"))
    
    # Data Quality Flags
    .withColumn("has_valid_timestamp", col("sighting_timestamp").isNotNull())
    .withColumn("has_coordinates", col("latitude").isNotNull() & col("longitude").isNotNull())
    .withColumn("has_known_shape", col("shape_classified") != "Other / Unknown")
    .withColumn("has_summary", col("summary_clean") != "")
    
    # Audit timestamps
    .withColumn("_silver_timestamp", current_timestamp())
    .withColumn("_bronze_source_file", col("_source_file"))
    .withColumn("_bronze_ingest_timestamp", col("_ingest_timestamp"))
)

# Write to Silver Delta Table
(
    df_silver.write
    .format("delta")
    .mode("overwrite")
    .option("mergeSchema", "true")
    .option("overwriteSchema", "true")
    .saveAsTable(SILVER_TABLE)
)

print(f"✅ Silver Transformation Complete")
print(f"   Clean Records Processed: {df_silver.count()}")
print(f"   Table: {SILVER_TABLE}")

# COMMAND ----------

# DBTITLE 1,Data Quality Metrics
# MAGIC %sql
# MAGIC SELECT 
# MAGIC     COUNT(*) as total_clean_sightings,
# MAGIC     COUNT(DISTINCT data_source) as unique_sources,
# MAGIC     COUNT(DISTINCT state) as unique_states,
# MAGIC     COUNT(DISTINCT shape_classified) as unique_shapes,
# MAGIC     SUM(CASE WHEN has_valid_timestamp THEN 1 ELSE 0 END) as valid_timestamps,
# MAGIC     SUM(CASE WHEN has_coordinates THEN 1 ELSE 0 END) as with_coordinates,
# MAGIC     SUM(CASE WHEN has_known_shape THEN 1 ELSE 0 END) as classified_shapes,
# MAGIC     ROUND((SUM(CASE WHEN has_known_shape THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 2) as shape_classification_pct,
# MAGIC     MIN(sighting_timestamp) as earliest_sighting,
# MAGIC     MAX(sighting_timestamp) as latest_sighting
# MAGIC FROM workspace.default.silver_uap_structured
