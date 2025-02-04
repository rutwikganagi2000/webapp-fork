import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_health_check_success(client):
    """Test successful health check"""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert "no-cache" in response.headers["Cache-Control"]
    assert not response.content  # Empty response body

def test_health_check_with_payload(client):
    """Test health check with payload (should fail)"""
    response = client.get("/healthz", params={"test": "payload"})
    assert response.status_code == 400

def test_health_check_unsupported_methods(client):
    """Test unsupported HTTP methods"""
    methods = ["POST", "PUT", "DELETE", "PATCH"]
    for method in methods:
        response = client.request(method, "/healthz")
        assert response.status_code == 405

def test_health_check_database_failure(client, monkeypatch):
    """Test database connection failure"""
    def mock_db_error(*args, **kwargs):
        raise Exception("Database connection error")
    
    # Patch the database session to simulate failure
    monkeypatch.setattr("app.api.endpoints.healthcheck.HealthCheck", mock_db_error)
    
    response = client.get("/healthz")
    assert response.status_code == 503

def test_health_check_not_found(client):
    """Test undefined routes return 404"""
    response = client.get("/undefined-route")
    assert response.status_code == 404
