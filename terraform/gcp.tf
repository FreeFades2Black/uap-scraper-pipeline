resource "google_storage_bucket" "scraper_raw_data" {
  name          = "${var.gcp_project_id}-scraper-raw"
  location      = var.gcp_region
  force_destroy = false

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }
}

resource "google_storage_bucket" "databricks_lakehouse" {
  name          = "${var.gcp_project_id}-lakehouse-data"
  location      = var.gcp_region
  force_destroy = false

  uniform_bucket_level_access = true
}
