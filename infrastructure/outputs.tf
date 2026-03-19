output "project_id" {
  description = "GCP Project ID"
  value       = var.project_id
}

output "region" {
  description = "GCP Region"
  value       = var.region
}

output "telemetry_events_topic" {
  description = "Pub/Sub topic for tactical telemetry events"
  value       = google_pubsub_topic.telemetry_events.name
}

output "telemetry_dlq_topic" {
  description = "Pub/Sub Dead-Letter Queue topic"
  value       = google_pubsub_topic.dlq.name
}

output "analytics_processor_subscription" {
  description = "Pub/Sub subscription for analytics processor"
  value       = google_pubsub_subscription.analytics_processor_sub.name
}

output "telemetry_ingestion_api_url" {
  description = "Cloud Run service URL for telemetry ingestion API"
  value       = google_cloud_run_v2_service.ingestion_api.uri
}

output "bigquery_dataset" {
  description = "BigQuery dataset ID"
  value       = google_bigquery_dataset.analytics_dataset.dataset_id
}

output "bigquery_table" {
  description = "BigQuery table ID"
  value       = google_bigquery_table.telemetry_table.table_id
}
