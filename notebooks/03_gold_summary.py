# Databricks notebook source
# DBTITLE 1,Gold Layer - UAP Summary Analytics & Business Aggregations
# MAGIC %md
# MAGIC # 03 - Gold Layer Summary Analytics
# MAGIC 
# MAGIC Aggregates normalized Silver UAP sightings into analytics-ready Gold tables optimized for Lakeview dashboards and geospatial intelligence.
# MAGIC 
# MAGIC **Gold Analytics Tables Produced:**
# MAGIC 1. `workspace.default.gold_uap_summary` - High-level KPIs and data quality scorecard
# MAGIC 2. `workspace.default.gold_uap_by_location` - Geographic distribution by State & Country
# MAGIC 3. `workspace.default.gold_uap_by_shape` - Morphology and phenomenon classification patterns
# MAGIC 4. `workspace.default.gold_uap_timeline` - Decadal and annual temporal volume trends
# MAGIC 5. `workspace.default.gold_uap_by_source` - Collector performance and reliability metrics

# COMMAND ----------

# DBTITLE 1,Configuration
SILVER_TABLE = "workspace.default.silver_uap_structured"
GOLD_SUMMARY_TABLE = "workspace.default.gold_uap_summary"
GOLD_BY_LOCATION_TABLE = "workspace.default.gold_uap_by_location"
GOLD_BY_SHAPE_TABLE = "workspace.default.gold_uap_by_shape"
GOLD_TIMELINE_TABLE = "workspace.default.gold_uap_timeline"
GOLD_BY_SOURCE_TABLE = "workspace.default.gold_uap_by_source"

print(f"Source: {SILVER_TABLE}")
print(f"Target Summary:     {GOLD_SUMMARY_TABLE}")
print(f"Target By Location: {GOLD_BY_LOCATION_TABLE}")
print(f"Target By Shape:    {GOLD_BY_SHAPE_TABLE}")
print(f"Target Timeline:    {GOLD_TIMELINE_TABLE}")
print(f"Target By Source:   {GOLD_BY_SOURCE_TABLE}")

# COMMAND ----------

# DBTITLE 1,BATCH: 1. Overall Summary & Scorecard
from pyspark.sql.functions import (
    count, countDistinct, sum, min, max, round as spark_round, current_timestamp, when, col, year, avg
)

df_silver = spark.read.table(SILVER_TABLE)

df_summary = df_silver.agg(
    count("*").alias("total_sightings"),
    countDistinct("data_source").alias("active_data_sources"),
    countDistinct("state").alias("unique_states"),
    countDistinct("city").alias("unique_cities"),
    countDistinct("shape_classified").alias("unique_shape_categories"),
    sum(when(col("has_coordinates"), 1).otherwise(0)).alias("sightings_with_coordinates"),
    sum(when(col("has_valid_timestamp"), 1).otherwise(0)).alias("sightings_with_valid_dates"),
    sum(when(col("has_known_shape"), 1).otherwise(0)).alias("sightings_with_known_shape"),
    min("sighting_timestamp").alias("earliest_sighting"),
    max("sighting_timestamp").alias("latest_sighting"),
    current_timestamp().alias("_summary_generated_at")
).withColumn(
    "coordinate_coverage_pct",
    spark_round((col("sightings_with_coordinates") / col("total_sightings")) * 100, 2)
).withColumn(
    "shape_classification_pct",
    spark_round((col("sightings_with_known_shape") / col("total_sightings")) * 100, 2)
)

(
    df_summary.write
    .format("delta")
    .mode("overwrite")
    .saveAsTable(GOLD_SUMMARY_TABLE)
)
print(f"✅ Gold Summary Table Created: {GOLD_SUMMARY_TABLE}")

# COMMAND ----------

# DBTITLE 1,BATCH: 2. Geographic Aggregation (By State & Country)
df_by_location = (
    df_silver
    .groupBy("country", "state")
    .agg(
        count("*").alias("total_sightings"),
        countDistinct("city").alias("unique_cities"),
        avg("latitude").alias("avg_latitude"),
        avg("longitude").alias("avg_longitude"),
        sum(when(col("has_coordinates"), 1).otherwise(0)).alias("geocoded_sightings")
    )
    .withColumn("_aggregated_at", current_timestamp())
    .orderBy(col("total_sightings").desc())
)

(
    df_by_location.write
    .format("delta")
    .mode("overwrite")
    .saveAsTable(GOLD_BY_LOCATION_TABLE)
)
print(f"✅ Gold By Location Table Created: {GOLD_BY_LOCATION_TABLE}")

# COMMAND ----------

# DBTITLE 1,BATCH: 3. Shape & Morphology Distribution
df_by_shape = (
    df_silver
    .groupBy("shape_classified")
    .agg(
        count("*").alias("sighting_count"),
        countDistinct("state").alias("states_reported"),
        countDistinct("data_source").alias("reporting_sources")
    )
    .withColumn("pct_of_total", spark_round((col("sighting_count") / df_silver.count()) * 100, 2))
    .withColumn("_aggregated_at", current_timestamp())
    .orderBy(col("sighting_count").desc())
)

(
    df_by_shape.write
    .format("delta")
    .mode("overwrite")
    .saveAsTable(GOLD_BY_SHAPE_TABLE)
)
print(f"✅ Gold By Shape Table Created: {GOLD_BY_SHAPE_TABLE}")

# COMMAND ----------

# DBTITLE 1,BATCH: 4. Historical Timeline Trends
df_timeline = (
    df_silver
    .filter(col("sighting_timestamp").isNotNull())
    .withColumn("sighting_year", year(col("sighting_timestamp")))
    .groupBy("sighting_year")
    .agg(
        count("*").alias("annual_sightings"),
        countDistinct("state").alias("states_reporting"),
        countDistinct("shape_classified").alias("distinct_shapes")
    )
    .withColumn("_aggregated_at", current_timestamp())
    .orderBy(col("sighting_year").asc())
)

(
    df_timeline.write
    .format("delta")
    .mode("overwrite")
    .saveAsTable(GOLD_TIMELINE_TABLE)
)
print(f"✅ Gold Timeline Table Created: {GOLD_TIMELINE_TABLE}")

# COMMAND ----------

# DBTITLE 1,BATCH: 5. Collector Reliability & Source Quality
df_by_source = (
    df_silver
    .groupBy("data_source")
    .agg(
        count("*").alias("total_records"),
        sum(when(col("has_coordinates"), 1).otherwise(0)).alias("with_coordinates"),
        sum(when(col("has_valid_timestamp"), 1).otherwise(0)).alias("with_valid_dates"),
        sum(when(col("has_known_shape"), 1).otherwise(0)).alias("with_known_shape")
    )
    .withColumn("quality_score_pct", spark_round(((col("with_coordinates") + col("with_valid_dates") + col("with_known_shape")) / (col("total_records") * 3)) * 100, 2))
    .withColumn("_aggregated_at", current_timestamp())
    .orderBy(col("total_records").desc())
)

(
    df_by_source.write
    .format("delta")
    .mode("overwrite")
    .saveAsTable(GOLD_BY_SOURCE_TABLE)
)
print(f"✅ Gold By Source Table Created: {GOLD_BY_SOURCE_TABLE}")
