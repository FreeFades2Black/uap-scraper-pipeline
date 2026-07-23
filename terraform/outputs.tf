output "raw_storage_bucket" {
  value       = google_storage_bucket.scraper_raw_data.name
  description = "GCS Bucket for raw scraper output"
}

output "lakehouse_storage_bucket" {
  value       = google_storage_bucket.databricks_lakehouse.name
  description = "GCS Bucket for Databricks Lakehouse storage"
}
