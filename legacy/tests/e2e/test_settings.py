import os
import json
import pytest

def test_app_settings_get_endpoint(api_client):
    """Verify GET /api/v1/app-settings returns default settings structure."""
    response = api_client.get("/api/v1/app-settings")
    assert response.status_code == 200
    data = response.json()
    assert "api_base_url" in data
    assert "database_url" in data
    assert "offline_mode" in data
    assert "logging_level" in data

def test_app_settings_post_endpoint(api_client):
    """Verify POST /api/v1/app-settings updates and persists app config."""
    payload = {
        "api_base_url": "/api/v1",
        "database_url": "sqlite:///baseball_optimizer.db",
        "offline_mode": True,
        "logging_level": "DEBUG",
        "cache_ttl_seconds": 120,
        "default_team_id": 111,
        "mock_api_latency_ms": 250
    }
    response = api_client.post("/api/v1/app-settings", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["database_url"] == "sqlite:///baseball_optimizer.db"
    assert data["offline_mode"] is True
    assert data["logging_level"] == "DEBUG"
    assert data["cache_ttl_seconds"] == 120
    assert data["default_team_id"] == 111
    assert data["mock_api_latency_ms"] == 250
    
    # Restore original settings
    original = {
        "api_base_url": "/api/v1",
        "database_url": "sqlite:///baseball_optimizer.db",
        "offline_mode": False,
        "logging_level": "INFO",
        "cache_ttl_seconds": 3600,
        "default_team_id": 112,
        "mock_api_latency_ms": 100
    }
    restore_res = api_client.post("/api/v1/app-settings", json=original)
    assert restore_res.status_code == 200
