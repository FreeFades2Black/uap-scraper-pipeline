terraform {
  required_providers {
    databricks = {
      source = "databricks/databricks"
    }
  }
}

provider "databricks" {}

resource "databricks_job" "process_anomalies" {
  name = "Process-UAP-Historical-Anomalies"

  task {
    task_key            = "process_gcs_raw_data"
    existing_cluster_id = "your-manual-cluster-id-here"

    notebook_task {
      notebook_path = "/Workspace/Shared/process_historical_anomalies"
    }
  }
}
