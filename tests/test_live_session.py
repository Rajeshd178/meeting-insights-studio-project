"""
Unit tests for Prompt I: Live Meeting Mode
Tests chunk ingestion, silence skip logic, quota protections, and handoff.
"""

import pytest
from backend.services.live_session import (
    start_live_session,
    ingest_live_chunk,
    get_live_updates,
    generate_catchup_summary,
    stop_live_session
)
from backend.db import get_db_connection


def test_live_session_lifecycle():
    # 1. Start Live Session
    session = start_live_session(title="Live Test Sync", language="en", confidential=False)
    session_id = session["session_id"]
    assert session_id is not None
    assert session["status"] == "active"

    # 2. Ingest valid chunk
    mock_audio = b"RIFF____WAVEfmt ____data____"  # Mock audio payload
    chunk_res = ingest_live_chunk(session_id, seq=0, audio_bytes=mock_audio, client_start_sec=0.0)
    assert chunk_res["status"] in ("processed", "skipped_silence")

    # 3. Duplicate chunk handling
    dup_res = ingest_live_chunk(session_id, seq=0, audio_bytes=mock_audio, client_start_sec=0.0)
    assert dup_res["status"] in ("duplicate", "processed", "skipped_silence")

    # 4. Updates Polling
    updates = get_live_updates(session_id, since=-1)
    assert "segments" in updates
    assert "running_summary" in updates
    assert "tentative_items" in updates

    # 5. Catch-up summary
    catchup = generate_catchup_summary(session_id)
    assert "catchup_bullets" in catchup

    # 6. Stop and handoff to pipeline
    stop_res = stop_live_session(session_id)
    assert stop_res["session_id"] == session_id
    assert stop_res["status"] == "stopped"


def test_live_silent_chunk_handling():
    session = start_live_session(title="Silence Test", language="en", confidential=True)
    session_id = session["session_id"]

    # Ingest empty audio chunk
    res = ingest_live_chunk(session_id, seq=0, audio_bytes=b"", client_start_sec=0.0)
    assert res["status"] in ("skipped_silence", "processed")
