variable "project_id" {
  description = "GCP Project ID for deployment"
  type        = string
}

variable "region" {
  description = "GCP region for deployment"
  type        = string
  default     = "asia-south1"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "allowed_ip_ranges" {
  description = "List of allowed IP ranges for API access"
  type        = list(string)
  default     = []
}

variable "max_instances" {
  description = "Maximum Cloud Run instances"
  type        = number
  default     = 100
}

variable "bigquery_dataset_id" {
  description = "BigQuery dataset ID for analytics"
  type        = string
  default     = "omnistream_analytics"
}

variable "firestore_mode" {
  description = "Firestore database mode"
  type        = string
  default     = "NATIVE"
}
