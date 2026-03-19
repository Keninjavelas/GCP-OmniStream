"""
Edge Simulation: Single Device Test for GCP-OmniStream
Enhanced with Debug Logging to capture Cloud Run internal errors.
"""

import json
import random
import time
import uuid
import requests
from datetime import datetime
import os

# Configuration
API_ENDPOINT = "https://telemetry-ingestion-api-282679082866.asia-south1.run.app/ingest"
CHAOS_CORRUPT_RATE = 0.10 
CHAOS_DUPLICATE_RATE = 0.10 
HELMET_ID = os.getenv("HELMET_ID", "helmet-001")

# Base coordinates (Hyderabad, India area)
BASE_LATITUDE = 17.4
BASE_LONGITUDE = 78.4
COORDINATE_VARIANCE = 0.005 

def generate_telemetry_payload(event_id=None, force_corrupt=False):
    latitude = BASE_LATITUDE + random.uniform(-COORDINATE_VARIANCE, COORDINATE_VARIANCE)
    longitude = BASE_LONGITUDE + random.uniform(-COORDINATE_VARIANCE, COORDINATE_VARIANCE)
    
    if force_corrupt:
        optical_status = "CORRUPT"
    else:
        status_roll = random.random()
        optical_status = "NORMAL" if status_roll < 0.90 else ("DEGRADED" if status_roll < 0.95 else "CORRUPT")
    
    payload = {
        "event_id": event_id if event_id else str(uuid.uuid4()),
        "helmet_id": HELMET_ID,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "latitude": round(latitude, 6),
        "longitude": round(longitude, 6),
        "threat_detected": random.random() < 0.05,
        "optical_status": optical_status,
        "metadata": {
            "battery_level": random.randint(70, 100),
            "signal_strength": random.randint(-80, -40),
            "firmware_version": "1.2.3"
        }
    }
    return payload

def send_telemetry(payload):
    """Send telemetry with robust error capturing"""
    try:
        response = requests.post(
            API_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        # Check if the response is actually JSON before parsing
        try:
            resp_data = response.json()
        except ValueError:
            resp_data = f"Non-JSON Response: {response.text[:200]}" # Capture raw error text
            
        return response.status_code, resp_data
    except requests.exceptions.RequestException as e:
        return None, str(e)

def run_simulation():
    print(f"Starting Edge Simulation for {HELMET_ID}")
    print(f"Target: {API_ENDPOINT}")
    print("-" * 60)
    
    event_count = 0
    success_count = 0
    failure_count = 0
    previous_payload = None

    try:
        while True:
            event_count += 1
            is_corrupt = random.random() < CHAOS_CORRUPT_RATE
            is_duplicate = random.random() < CHAOS_DUPLICATE_RATE
            
            if is_duplicate and previous_payload:
                payload = previous_payload.copy()
                print(f"[{event_count}] SENDING DUPLICATE...")
            else:
                payload = generate_telemetry_payload(force_corrupt=is_corrupt)
            
            status_code, response = send_telemetry(payload)
            
            if status_code in [200, 201]:
                success_count += 1
                print(f"[{event_count}] SUCCESS - Status: {status_code}")
            else:
                failure_count += 1
                print(f"[{event_count}] FAILED - Code: {status_code}")
                print(f"      RAW MSG: {response}") # THIS LINE IS CRITICAL FOR DEBUGGING
            
            previous_payload = payload
            time.sleep(random.uniform(1.0, 3.0))

    except KeyboardInterrupt:
        print(f"\nStopped. Success: {success_count} | Failures: {failure_count}")

if __name__ == "__main__":
    run_simulation()