"""
Tests for meeting processing status and retry / reprocess flow.
"""

import pytest
from backend.app import app
from backend.store import store


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_meeting_status_endpoint(client):
    meetings = store.get_meetings()
    assert len(meetings) > 0
    m_id = meetings[0]["id"]

    res = client.get(f"/api/meetings/{m_id}/status")
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert "status" in data["data"]
    assert "progress_pct" in data["data"]
    assert "stage" in data["data"]


def test_meeting_reprocess_flow(client):
    meetings = store.get_meetings()
    m_id = meetings[0]["id"]

    res = client.post(f"/api/meetings/{m_id}/reprocess")
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert data["data"]["status"] == "processing"

    # Status check reflects processing
    status_res = client.get(f"/api/meetings/{m_id}/status")
    status_data = status_res.get_json()
    assert status_data["data"]["status"] in ("processing", "done")
