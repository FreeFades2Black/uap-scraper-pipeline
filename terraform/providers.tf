terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.0"
    }
  }

  # Remote state backend configuration (uncomment once backend bucket is created)
  # backend "gcs" {
  #   bucket = "YOUR_GCP_PROJECT_ID-tfstate"
  #   prefix = "env/dev"
  # }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

provider "databricks" {
  host = var.databricks_host
}
