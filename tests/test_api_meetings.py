"""
Tests for GET /api/meetings endpoint with search, filter, and sort capabilities.
"""

import pytest
from backend.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_api_meetings_list(client):
    res = client.get("/api/meetings")
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert isinstance(data["data"], list)
    assert data["total"] >= 1


def test_api_meetings_search(client):
    res = client.get("/api/meetings?q=sprint")
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert len(data["data"]) >= 1
    for m in data["data"]:
        text = (m["title"] + " " + (m["summary"]["tldr"] if m.get("summary") else "")).lower()
        tags = [t.lower() for t in m.get("tags", [])]
        speakers = [s.get("displayName", "").lower() for s in m.get("speakers", [])]
        assert "sprint" in text or any("sprint" in t for t in tags) or any("sprint" in spk for spk in speakers)


def test_api_meetings_filter_type(client):
    res = client.get("/api/meetings?type=planning")
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    for m in data["data"]:
        assert m["meetingType"].lower() == "planning"


def test_api_meetings_sort_order(client):
    res_health = client.get("/api/meetings?sort=highest_health")
    assert res_health.status_code == 200
    data = res_health.get_json()
    scores = [m["healthScore"] for m in data["data"] if m.get("healthScore") is not None]
    assert scores == sorted(scores, reverse=True)
