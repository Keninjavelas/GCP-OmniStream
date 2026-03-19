# GCP-OmniStream Architecture

## Overview

GCP-OmniStream is a serverless, event-driven data pipeline for processing real-time telemetry from Edge-AI Integrated Tactical Helmets. The architecture follows FinOps principles with scale-to-zero services staying within a 5,000 INR/month budget using GCP Free Tier services.

## Architecture Diagram

```
┌─────────────────┐     ┌──────────────────────┐     ┌──────────────────┐
│                 │     │                      │     │                  │
│  Edge Devices   │────▶│  Telemetry Ingestion │────▶│  Pub/Sub Topic   │
│  (Helmet AI)    │     │   Cloud Run Service  │     │  tactical-stream │
│                 │     │                      │     │                  │
└─────────────────┘     └──────────────────────┘     └────────┬─────────┘
                                                              │
                                                              │ (DLQ Policy)
                                                              │
                                              ┌───────────────┴───────────────┐
                                              │                               │
                                              ▼                               ▼
                                    ┌─────────────────┐             ┌─────────────────┐
                                    │  Pub/Sub        │             │  Pub/Sub DLQ    │
                                    │  Subscription   │             │  Topic          │
                                    │  (5 attempts)   │             │                 │
                                    └────────┬────────┘             └─────────────────┘
                                             │
                                             ▼
                                    ┌─────────────────┐
                                    │  Analytics      │
                                    │  Processor      │
                                    │  Cloud Function │
                                    └────────┬────────┘
                                             │
                                             ▼
                                    ┌─────────────────┐
                                    │  BigQuery       │
                                    │  Dataset:       │
                                    │  omnistream_    │
                                    │  analytics      │
                                    │  Table:         │
                                    │  helmet_telem-  │
                                    │  etry_raw       │
                                    └─────────────────┘
```

## Components

### 1. Telemetry Ingestion API (Cloud Run)

- **Runtime**: Python 3.11 + FastAPI
- **Purpose**: REST API endpoint for helmet telemetry ingestion
- **Features**:
  - Structured logging with Google Cloud Logging
  - Idempotent event processing via event_id
  - Distributed tracing with trace_id
  - Scale-to-zero (max 10 instances, 80 concurrency)
  - Free Tier eligible

### 2. Pub/Sub with Dead-Letter Queue

- **Main Topic**: `tactical-telemetry-stream`
- **DLQ Topic**: `tactical-telemetry-dlq`
- **Subscription**: 60s ack deadline, 5 max delivery attempts
- **Retry Policy**: 10s minimum backoff, 600s maximum

### 3. Analytics Processor (Cloud Functions)

- **Runtime**: Python 3.11
- **Trigger**: Pub/Sub topic
- **Features**:
  - Structured logging
  - BigQuery insertion
  - Chaos testing: CORRUPT status triggers NACK → DLQ
  - Idempotent processing via event_id

### 4. BigQuery Analytics

- **Dataset**: `omnistream_analytics`
- **Table**: `helmet_telemetry_raw`
- **Partitioning**: DAY on timestamp field
- **Schema**: event_id, helmet_id, timestamp, latitude, longitude, threat_detected, optical_status

## Data Flow

1. Edge device sends telemetry to `/ingest` endpoint
2. API validates payload, generates event_id, logs with trace_id
3. Message published to `tactical-telemetry-stream` with event_id as attribute
4. Pub/Sub subscription routes to analytics processor
5. Analytics processor:
   - Decodes Pub/Sub message
   - If optical_status == "CORRUPT": raises ValueError → NACK → DLQ
   - Otherwise: inserts into BigQuery
6. Success logged with event_id for traceability

## FinOps Considerations

| Service | Free Tier | Cost Control |
|---------|-----------|--------------|
| Cloud Run | 2M requests/month | Scale to 0, max 10 instances |
| Cloud Functions | 2M invocations/month | Event-driven, scale to 0 |
| Pub/Sub | 10GB/month | Minimal message retention |
| BigQuery | 10GB storage, 1TB/query/month | Partitioned tables, columnar storage |

## Chaos Testing

The edge-simulation tool tests:
- **10% CORRUPT rate**: Verifies DLQ routing
- **10% duplicate rate**: Tests idempotency
- **Coordinate variance**: Simulates realistic movement

## Monitoring

- Cloud Logging for structured logs
- Cloud Trace for distributed tracing
- Cloud Monitoring for metrics and alerts
- Pub/Sub dead-letter queue monitoring
