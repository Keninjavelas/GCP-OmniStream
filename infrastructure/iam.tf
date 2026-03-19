resource "google_service_account" "telemetry_api" { 
  account_id   = "telemetry-api-sa" 
  display_name = "Telemetry API Service Account" 
} 

resource "google_project_iam_member" "telemetry_api_pubsub_publisher" { 
  project = var.project_id 
  role    = "roles/pubsub.publisher" 
  member  = "serviceAccount:${google_service_account.telemetry_api.email}" 
} 

resource "google_project_iam_member" "telemetry_api_logging_writer" { 
  project = var.project_id 
  role    = "roles/logging.logWriter" 
  member  = "serviceAccount:${google_service_account.telemetry_api.email}" 
} 

resource "google_service_account" "analytics_processor" { 
  account_id   = "analytics-processor-sa" 
  display_name = "Analytics Processor Service Account" 
} 

resource "google_project_iam_member" "analytics_processor_bigquery_editor" { 
  project = var.project_id 
  role    = "roles/bigquery.dataEditor" 
  member  = "serviceAccount:${google_service_account.analytics_processor.email}" 
} 

resource "google_project_iam_member" "analytics_processor_logging_writer" { 
  project = var.project_id 
  role    = "roles/logging.logWriter" 
  member  = "serviceAccount:${google_service_account.analytics_processor.email}" 
} 
