"""Basic tests for Local RAG Assistant."""

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.core.config import settings


def test_app_import():
    """Test that the app can be imported."""
    assert app is not None
    assert app.title == "Local RAG Assistant"


def test_health_endpoint():
    """Test health check endpoint."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_api_docs_available():
    """Test that API docs are available in debug mode."""
    if not settings.app.debug:
        pytest.skip("Docs not enabled in production mode")
    client = TestClient(app)
    response = client.get("/docs")
    assert response.status_code == 200


def test_root_endpoint():
    """Test root endpoint serves HTML."""
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"] 