resource "google_compute_instance" "monitoring" {
  name         = "terraform-monitoring-${var.edge_nodes_count+1}"
  machine_type = "e2-highcpu-2"

  metadata_startup_script = "${file("./scripts/monitoring/start.sh")}"

  service_account {
    scopes = ["cloud-platform"]
  }

  boot_disk {
    initialize_params {
      image = "projects/ubuntu-os-cloud/global/images/ubuntu-2204-jammy-v20240119a"
    }
  }

  network_interface {
    # A default network is created for all GCP projects
    subnetwork  = google_compute_subnetwork.vpc_subnet.self_link
    access_config {
    }
  }
}
