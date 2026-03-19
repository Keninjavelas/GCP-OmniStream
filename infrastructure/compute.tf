# 1. The Ingestion API (With the Command Override Fix)
resource "google_cloud_run_v2_service" "ingestion_api" {
  name     = "telemetry-ingestion-api"
  location = var.region

  template {
    containers {
      image = "asia-south1-docker.pkg.dev/${var.project_id}/omnistream-repo/ingestion-api:latest" 
      
      # FIX: Override the container's broken CMD string directly in Terraform
      command = ["uvicorn"]
      args    = ["main:app", "--host", "0.0.0.0", "--port", "8080"]

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
    }
    scaling {
      max_instance_count = 10 
    }
    max_instance_request_concurrency = 80
  }
}

# 2. Cloud Function Prep: Zip the local code
data "archive_file" "function_zip" {
  type        = "zip"
  source_dir  = "../services/analytics-processor"
  output_path = "analytics_processor.zip"
}

# 3. Cloud Function Prep: Create a bucket (With the Security Policy Fix)
resource "google_storage_bucket" "functions_bucket" {
  name                        = "${var.project_id}-gcf-source"
  location                    = var.region
  uniform_bucket_level_access = true 
}

# MISSING LINK RESTORED: Upload the zip file into the bucket
resource "google_storage_bucket_object" "analytics_processor_source" {
  name   = "analytics-processor-${data.archive_file.function_zip.output_md5}.zip"
  bucket = google_storage_bucket.functions_bucket.name
  source = data.archive_file.function_zip.output_path
}

# 4. The Analytics Processor Cloud Function
resource "google_cloudfunctions_function" "analytics_processor" {
  name                  = "analytics-processor-${var.environment}"
  runtime               = "python311"
  region                = var.region
  entry_point           = "process_telemetry"
  source_archive_bucket = google_storage_bucket.functions_bucket.name
  source_archive_object = google_storage_bucket_object.analytics_processor_source.name
  
  event_trigger {
    event_type = "google.pubsub.topic.publish"
    resource   = "projects/${var.project_id}/topics/telemetry-events"
  }
  
  environment_variables = {
    BIGQUERY_DATASET = var.bigquery_dataset_id
    ENVIRONMENT      = var.environment
  }
}