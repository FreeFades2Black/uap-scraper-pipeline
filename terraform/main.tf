resource "google_compute_instance" "scraper_node" {
  name         = "cloudwire-scraper-node"
  machine_type = "e2-micro"
  zone         = "us-central1-a"

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
    }
  }

  network_interface {
    network = "default"
    access_config {
      // Ephemeral public IP
    }
  }

  service_account {
    scopes = [
      "https://www.googleapis.com/auth/devstorage.read_write", 
      "https://www.googleapis.com/auth/logging.write"
    ]
  }

  metadata_startup_script = <<-EOT
    #!/bin/bash
    apt-get update
    apt-get install -y python3-pip python3-requests
  EOT
}
