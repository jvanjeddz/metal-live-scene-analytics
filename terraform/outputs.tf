output "project_id" {
  value = google_project.metal_analytics.project_id
}

output "data_lake_bucket" {
  value = google_storage_bucket.data_lake.name
}

output "service_account_email" {
  value = google_service_account.pipeline.email
}

output "sa_key_path" {
  value     = local_file.sa_key.filename
  sensitive = true
}
