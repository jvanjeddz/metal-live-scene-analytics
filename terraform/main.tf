terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ─── GCP Project ────────────────────────────────────────────────────────────────

resource "google_project" "metal_analytics" {
  name            = "Metal Live Scene Analytics"
  project_id      = var.project_id
  billing_account = var.billing_account
  org_id          = var.org_id != "" ? var.org_id : null
  folder_id       = var.folder_id != "" ? var.folder_id : null
}

# Enable required APIs
resource "google_project_service" "bigquery" {
  project = google_project.metal_analytics.project_id
  service = "bigquery.googleapis.com"

  disable_on_destroy = false
}

resource "google_project_service" "storage" {
  project = google_project.metal_analytics.project_id
  service = "storage.googleapis.com"

  disable_on_destroy = false
}

resource "google_project_service" "iam" {
  project = google_project.metal_analytics.project_id
  service = "iam.googleapis.com"

  disable_on_destroy = false
}

# ─── GCS Bucket (Data Lake) ─────────────────────────────────────────────────────

resource "google_storage_bucket" "data_lake" {
  name          = "${var.project_id}-data-lake"
  location      = var.region
  project       = google_project.metal_analytics.project_id
  force_destroy = true

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [google_project_service.storage]
}

# ─── BigQuery Datasets ──────────────────────────────────────────────────────────

resource "google_bigquery_dataset" "raw" {
  dataset_id = "raw"
  project    = google_project.metal_analytics.project_id
  location   = var.region

  delete_contents_on_destroy = true

  depends_on = [google_project_service.bigquery]
}

resource "google_bigquery_dataset" "staging" {
  dataset_id = "staging"
  project    = google_project.metal_analytics.project_id
  location   = var.region

  delete_contents_on_destroy = true

  depends_on = [google_project_service.bigquery]
}

resource "google_bigquery_dataset" "marts" {
  dataset_id = "marts"
  project    = google_project.metal_analytics.project_id
  location   = var.region

  delete_contents_on_destroy = true

  depends_on = [google_project_service.bigquery]
}

# ─── Service Account ────────────────────────────────────────────────────────────

resource "google_service_account" "pipeline" {
  account_id   = "metal-analytics-pipeline"
  display_name = "Metal Analytics Pipeline"
  project      = google_project.metal_analytics.project_id

  depends_on = [google_project_service.iam]
}

# BigQuery Admin (manage datasets + load data)
resource "google_project_iam_member" "bq_admin" {
  project = google_project.metal_analytics.project_id
  role    = "roles/bigquery.admin"
  member  = "serviceAccount:${google_service_account.pipeline.email}"
}

# Storage Admin (upload to GCS)
resource "google_project_iam_member" "storage_admin" {
  project = google_project.metal_analytics.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.pipeline.email}"
}

# ─── Service Account Key (JSON) ─────────────────────────────────────────────────

resource "google_service_account_key" "pipeline_key" {
  service_account_id = google_service_account.pipeline.name
}

resource "local_file" "sa_key" {
  content  = base64decode(google_service_account_key.pipeline_key.private_key)
  filename = "${path.module}/keys/sa-key.json"

  file_permission = "0600"
}
