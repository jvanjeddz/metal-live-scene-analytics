variable "project_id" {
  description = "GCP project ID to create"
  type        = string
}

variable "billing_account" {
  description = "Billing account ID to link to the project"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "org_id" {
  description = "GCP organization ID (optional, leave empty for personal accounts)"
  type        = string
  default     = ""
}

variable "folder_id" {
  description = "GCP folder ID to create project in (optional)"
  type        = string
  default     = ""
}
