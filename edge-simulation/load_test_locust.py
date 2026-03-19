#!/usr/bin/env python3
"""
Load test script for OmniStream using Locust
Simulates 500+ edge devices sending telemetry data
"""

import random
import uuid
from datetime import datetime, timezone
from locust import HttpUser, task, between, events
import gevent

# Configuration
NUM_DEVICES = 500
SEND_INTERVAL_MIN = 0.5
SEND_INTERVAL_MAX = 2.0

# Device pool
devices = [
    {
        "device_id": str(uuid.uuid4()),
        "base_accel": random.uniform(0.3, 0.7),
        "base_gyro": random.uniform(0.05, 0.15),
        "start_time": datetime.now(timezone.utc)
    }
    for _ in range(NUM_DEVICES)
]

def generate_telemetry(device: dict) -> dict:
    """Generate telemetry data for a device"""
    elapsed = (datetime.now(timezone.utc) - device["start_time"]).total_seconds()
    
    # Simulate battery drain
    battery_level = max(20, 100 - int(elapsed / 3600))
    
    # Simulate activity patterns
    is_active = random.random() < 0.3
    
    payload = {
        "device_id": device["device_id"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sensor_data": {
            "accelerometer": {
                "x": round(device["base_accel"] + random.uniform(-0.3, 0.3) * (1.5 if is_active else 1), 3),
                "y": round(device["base_accel"] + random.uniform(-0.3, 0.3) * (1.5 if is_active else 1), 3),
                "z": round(device["base_accel"] + random.uniform(-0.3, 0.3) * (1.5 if is_active else 1), 3)
            },
            "gyroscope": {
                "x": round(device["base_gyro"] + random.uniform(-0.05, 0.05) * (2 if is_active else 1), 3),
                "y": round(device["base_gyro"] + random.uniform(-0.05, 0.05) * (2 if is_active else 1), 3),
                "z": round(device["base_gyro"] + random.uniform(-0.05, 0.05) * (2 if is_active else 1), 3)
            },
            "heart_rate": random.randint(60, 80) + (random.randint(20, 40) if is_active else 0),
            "battery_level": battery_level
        },
        "metadata": {
            "device_status": "active" if battery_level > 30 else "low_battery",
            "firmware_version": "1.2.3",
            "signal_strength": random.randint(-80, -40)
        },
        "event_type": "telemetry"
    }
    
    return payload

class TelemetryLoadTest(HttpUser):
    """Load test user class"""
    wait_time = between(SEND_INTERVAL_MIN, SEND_INTERVAL_MAX)
    
    @task(1)
    def send_telemetry(self):
        """Send telemetry data"""
        device = random.choice(devices)
        payload = generate_telemetry(device)
        
        response = self.client.post("/ingest", json=payload)
        
        if response.status_code != 200:
            print(f"Failed to send telemetry: {response.status_code}")
    
    def on_start(self):
        """Called when a user starts"""
        self.device = random.choice(devices)
        print(f"Starting test for device: {self.device['device_id']}")

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts"""
    print(f"Starting load test with {NUM_DEVICES} simulated devices")
    print(f"Target: {environment.host}")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops"""
    print(f"Test completed. Total requests: {environment.stats.total.num_requests}")

if __name__ == "__main__":
    import sys
    import subprocess
    
    print("OmniStream Load Test")
    print(f"Simulating {NUM_DEVICES} devices")
    print("\nTo run with Locust:")
    print("1. Install: pip install locust")
    print("2. Run: locust -f load_test_locust.py --host=http://localhost:8080")
    print("3. Open browser: http://localhost:8089")
