"""
Tests for card actions: rename, tag normalization, and delete with media removal.
"""

import pytest
import os
from pathlib import Path
from backend.app import app
from backend.store import store


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_rename_meeting(client):
    # Create temporary meeting
    temp_m = {
        "id": "test-rename-m",
        "title": "Initial Title",
        "meetingDate": "2026-10-04",
        "durationSec": 120,
        "meetingType": "general",
        "status": "done"
    }
    store.add_meeting(temp_m)

    res = client.patch("/api/meetings/test-rename-m", json={"title": "Updated Modern Title"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert data["data"]["title"] == "Updated Modern Title"

    # Verify DB
    m = store.get_meeting("test-rename-m")
    assert m["title"] == "Updated Modern Title"

    # Cleanup
    store.delete_meeting("test-rename-m")


def test_tag_normalization(client):
    temp_m = {
        "id": "test-tags-m",
        "title": "Tag Normalization Test",
        "meetingDate": "2026-10-04",
        "durationSec": 120,
        "meetingType": "general",
        "status": "done"
    }
    store.add_meeting(temp_m)

    raw_tags = ["  Sprint  ", "PLANNING", "sprint", "Agile", "tag4", "tag5", "tag6", "tag7", "tag8", "tag9_overflow"]
    res = client.patch("/api/meetings/test-tags-m", json={"tags": raw_tags})
    assert res.status_code == 200
    data = res.get_json()
    tags = data["data"]["tags"]

    # Verify max 8 tags, trimmed, deduplicated, lowercase
    assert len(tags) == 8
    assert "sprint" in tags
    assert "planning" in tags
    assert tags.count("sprint") == 1
    assert "tag9_overflow" not in tags

    store.delete_meeting("test-tags-m")


def test_delete_meeting_and_media_removal(client):
    upload_dir = Path(app.config["UPLOAD_FOLDER"])
    upload_dir.mkdir(parents=True, exist_ok=True)
    media_file = upload_dir / "test-del-m-audio.mp3"
    media_file.write_text("dummy audio data")

    temp_m = {
        "id": "test-del-m",
        "title": "Meeting To Delete",
        "meetingDate": "2026-10-04",
        "sourceFilename": "test-del-m-audio.mp3",
        "durationSec": 60,
        "status": "done"
    }
    store.add_meeting(temp_m)

    assert media_file.exists()

    res = client.delete("/api/meetings/test-del-m")
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True

    # Check database removal
    assert store.get_meeting("test-del-m") is None
    # Check media file was deleted
    assert not media_file.exists()
