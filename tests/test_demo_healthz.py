"""
Tests for Demo mode loader (zero network calls assertion) and /healthz endpoint.
"""

import pytest
from unittest.mock import patch
from backend.app import app
from backend.store import store


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_demo_load_zero_network_calls(client):
    # Patch requests and openai to assert zero network calls during demo load
    with patch("requests.get") as mock_req, patch("requests.post") as mock_post:
        res = client.post("/api/demo/load?force=1")
        assert res.status_code == 200
        data = res.get_json()
        assert data["ok"] is True

        # Assert no network calls were made
        assert mock_req.call_count == 0
        assert mock_post.call_count == 0

        # Assert database has meetings
        meetings = store.get_meetings()
        assert len(meetings) >= 3


def test_healthz_endpoint(client):
    res = client.get("/healthz")
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert "status" in data
    assert "deployments" in data
    assert "chat" in data["deployments"]
    assert "embeddings" in data["deployments"]
    assert "transcription" in data["deployments"]
