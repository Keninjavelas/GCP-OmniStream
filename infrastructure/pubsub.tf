# 1. The Dead-Letter Queue (DLQ) Topic
resource "google_pubsub_topic" "dlq" {
  name = "tactical-telemetry-dlq"
}

# 2. Main Telemetry Topic (Bridging the Topic Gap)
resource "google_pubsub_topic" "telemetry_events" {
  name = "telemetry-events"
}

# 3. Subscription for Analytics Processor with DLQ properly attached
resource "google_pubsub_subscription" "analytics_processor_sub" {
  name  = "analytics-processor-sub"
  topic = google_pubsub_topic.telemetry_events.name

  ack_deadline_seconds = 60

  # Failsafe: Route to DLQ after 5 failed attempts (Chaos Test catcher)
  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dlq.id
    max_delivery_attempts = 5
  }

  # Backpressure: Wait at least 10 seconds before retrying
  retry_policy {
    minimum_backoff = "10s"
  }
}
