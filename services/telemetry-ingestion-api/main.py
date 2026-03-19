"""
Telemetry Ingestion API for GCP-OmniStream
FastAPI service that ingests tactical helmet telemetry data and publishes to Pub/Sub
"""

import os
import json
import uuid
import logging
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from google.cloud import logging as cloud_logging
from google.cloud import pubsub_v1
from pydantic import BaseModel, Field, field_validator

# 1. FIX: Use standard Python logging integrated with Google Cloud Logging
logging_client = cloud_logging.Client()
logging_client.setup_logging()
logger = logging.getLogger("telemetry-ingestion-api")

# 2. FIX: PROJECT_ID must match the environment variable passed by Terraform
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "omnistream-dev")
PUBSUB_TOPIC = os.getenv("PUBSUB_TOPIC", "telemetry-events")
ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")

# Initialize Pub/Sub publisher
publisher = pubsub_v1.PublisherClient()
# Full path: projects/[PROJECT_ID]/topics/[TOPIC_ID]
topic_path = publisher.topic_path(PROJECT_ID, PUBSUB_TOPIC)

app = FastAPI(
    title="GCP-OmniStream Telemetry Ingestion API",
    description="Ingest tactical helmet telemetry data for real-time processing",
    version="1.0.0"
)

class TelemetryPayload(BaseModel):
    helmet_id: str = Field(..., min_length=1, max_length=64)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    threat_detected: Optional[bool] = False
    optical_status: Optional[str] = "NORMAL"
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)

    @field_validator("helmet_id")
    @classmethod
    def validate_helmet_id(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("helmet_id cannot be empty")
        return v.strip()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "environment": ENVIRONMENT}

@app.post("/ingest")
async def ingest_telemetry(payload: TelemetryPayload):
    try:
        event_id = str(uuid.uuid4())
        trace_id = f"projects/{PROJECT_ID}/traces/{event_id}"
        
        # Prepare message data as a JSON string
        message_data = {
            "event_id": event_id,
            "helmet_id": payload.helmet_id,
            "timestamp": payload.timestamp.isoformat() if payload.timestamp else datetime.utcnow().isoformat(),
            "latitude": payload.latitude,
            "longitude": payload.longitude,
            "threat_detected": payload.threat_detected,
            "optical_status": payload.optical_status,
            "trace_id": trace_id
        }
        
        # 3. FIX: Properly encode JSON for Pub/Sub
        data_str = json.dumps(message_data)
        
        # Publish to Pub/Sub
        future = publisher.publish(
            topic_path,
            data=data_str.encode("utf-8"),
            event_id=event_id # Custom attribute
        )
        
        message_id = future.result()
        
        # 4. FIX: Use standard logger.info with extra context for Cloud Logging
        logger.info(f"Ingested telemetry: {event_id}", extra={
            "json_fields": {
                "event_id": event_id,
                "message_id": message_id,
                "helmet_id": payload.helmet_id,
                "optical_status": payload.optical_status
            }
        })
        
        return JSONResponse(
            status_code=201,
            content={
                "status": "success",
                "event_id": event_id,
                "message_id": message_id
            }
        )
        
    except Exception as e:
        # 5. FIX: Use logger.exception to capture the traceback correctly
        logger.exception(f"Ingestion failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error during ingestion")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)