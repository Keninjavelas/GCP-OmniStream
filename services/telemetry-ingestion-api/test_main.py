import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from main import app

client = TestClient(app)

@patch("main.publisher")
def test_health_check(mock_publisher):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "environment": "dev"}

@patch("main.publisher")
def test_ingest_telemetry_success(mock_publisher):
    # Mock Pub/Sub publish response
    mock_future = MagicMock()
    mock_future.result.return_value = "mock-message-id"
    mock_publisher.publish.return_value = mock_future
    
    payload = {
        "helmet_id": "helmet-001",
        "latitude": 17.412345,
        "longitude": 78.456789,
        "threat_detected": False,
        "optical_status": "NORMAL"
    }
    
    response = client.post("/ingest", json=payload)
    
    assert response.status_code == 201
    assert response.json()["status"] == "success"
    assert "event_id" in response.json()
    assert response.json()["message_id"] == "mock-message-id"
    
    # Verify Pub/Sub call
    assert mock_publisher.publish.called

@patch("main.publisher")
def test_ingest_telemetry_invalid_payload(mock_publisher):
    # Missing required field 'helmet_id'
    payload = {
        "latitude": 17.412345,
        "longitude": 78.456789
    }
    
    response = client.post("/ingest", json=payload)
    assert response.status_code == 422 # Pydantic validation error

@patch("main.publisher")
def test_ingest_telemetry_invalid_coordinates(mock_publisher):
    # Latitude out of range
    payload = {
        "helmet_id": "helmet-001",
        "latitude": 100.0,
        "longitude": 78.456789
    }
    
    response = client.post("/ingest", json=payload)
    assert response.status_code == 422
