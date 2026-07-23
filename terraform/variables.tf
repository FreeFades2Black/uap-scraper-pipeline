variable "gcp_project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "gcp_region" {
  type        = string
  description = "GCP Region for Always Free Tier eligibility"
  default     = "us-central1"
}

variable "databricks_host" {
  type        = string
  description = "Databricks Workspace URL"
}

variable "databricks_token" {
  type        = string
  description = "Databricks Personal Access Token"
  sensitive   = true
}
