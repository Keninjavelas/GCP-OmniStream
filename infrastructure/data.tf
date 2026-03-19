# 1. BigQuery Dataset & Table (Perfectly matched to the Python API)
resource "google_bigquery_dataset" "analytics_dataset" {
  dataset_id = "omnistream_analytics"
  location   = var.region
}

resource "google_bigquery_table" "telemetry_table" {
  dataset_id = google_bigquery_dataset.analytics_dataset.dataset_id
  table_id   = "helmet_telemetry_raw"
  deletion_protection = false

  time_partitioning {
    type  = "DAY"
    field = "timestamp"
  }

  schema = <<EOF
[
  {"name": "event_id", "type": "STRING", "mode": "REQUIRED"},
  {"name": "helmet_id", "type": "STRING", "mode": "REQUIRED"},
  {"name": "timestamp", "type": "TIMESTAMP", "mode": "REQUIRED"},
  {"name": "latitude", "type": "FLOAT", "mode": "NULLABLE"},
  {"name": "longitude", "type": "FLOAT", "mode": "NULLABLE"},
  {"name": "threat_detected", "type": "BOOLEAN", "mode": "REQUIRED"},
  {"name": "optical_status", "type": "STRING", "mode": "NULLABLE"}
]
EOF
}

# 2. Firestore Database for Situational Awareness Stream State
resource "google_firestore_database" "default" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
}
