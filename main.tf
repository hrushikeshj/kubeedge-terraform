provider "google" {
  project = "kube-edge-412213"
  region  = "us-central1"
  zone    = "us-central1-c" # todo change location
}

resource "google_compute_instance" "master" {
  name         = "terraform-master"
  machine_type = "e2-highcpu-4"#e2-highcpu-4

  metadata_startup_script = "${file("./scripts/master_start.sh")}"

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

resource "google_compute_instance" "workers" {
  count        = var.edge_nodes_count
  name         = "terraform-worker-${count.index+1}"
  machine_type = "e2-medium"

  metadata_startup_script = "${file("./scripts/worker_start.sh")}"

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
