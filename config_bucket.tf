resource "google_storage_bucket" "config_bucket" {
    location      = "US"
    name          = "kubeedge-config-bucket"
    force_destroy = true
}

output "config_bucket_url" {
  value = google_storage_bucket.config_bucket.url
}

output "config_bucket_name" {
  value = google_storage_bucket.config_bucket.name
}

resource "google_storage_bucket_object" "scripts" {
  for_each = fileset("${path.module}/scripts", "*")

  name   = each.value
  source = "./scripts/${each.value}"
  bucket = google_storage_bucket.config_bucket.name
}

# resource "google_storage_bucket_object" "common" {
#   name   = "common.sh"
#   source = "./scripts/common.sh"
#   bucket = google_storage_bucket.config_bucket.name
# }

# resource "google_storage_bucket_object" "master" {
#   name   = "master.sh"
#   source = "./scripts/master.sh"
#   bucket = google_storage_bucket.config_bucket.name
# }

# resource "google_storage_bucket_object" "edge" {
#   name   = "edge.sh"
#   source = "./scripts/edge.sh"
#   bucket = google_storage_bucket.config_bucket.name
# }

# resource "google_storage_bucket_object" "echo_yaml" {
#   name   = "echo.yaml"
#   source = "./scripts/echo.yaml"
#   bucket = google_storage_bucket.config_bucket.name
# }

# resource "google_storage_bucket_object" "master_edgemesh" {
#   name   = "master_edgemesh.sh"
#   source = "./scripts/master_edgemesh.sh"
#   bucket = google_storage_bucket.config_bucket.name
# }

# resource "google_storage_bucket_object" "edge_edgemesh" {
#   name   = "edge_edgemesh.sh"
#   source = "./scripts/edge_edgemesh.sh"
#   bucket = google_storage_bucket.config_bucket.name
# }
