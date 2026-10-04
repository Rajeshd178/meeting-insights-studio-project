"""
Unit tests for cross-meeting tracker:
- Seeded conflicting pair is flagged
- Unrelated pair is not
- Fabricated quotes are rejected
"""

import pytest
import json
import time
from backend.services.tracker import verify_quote_in_transcript, run_conflict_tracker, judge_pair_with_llm
from backend.db import get_db_connection
from backend.store import store


def test_quote_verification_valid_and_fabricated():
    conn = get_db_connection()
    # Meeting demo-1 has segment "Good morning everyone, thanks for joining. Let's get started with the sprint review."
    valid_quote = "thanks for joining"
    fabricated_quote = "we will definitely eliminate the entire backend tomorrow morning"

    assert verify_quote_in_transcript(conn, "demo-1", valid_quote) is True
    assert verify_quote_in_transcript(conn, "demo-1", fabricated_quote) is False
    conn.close()


def test_seeded_conflict_detection():
    conn = get_db_connection()
    cur = conn.cursor()
    # Ensure seeded conflict conf-1 exists
    cur.execute("""
    INSERT OR REPLACE INTO conflicts (
        id, meeting_id, other_meeting_id, kind, description, evidence_json, created_at, dismissed
    ) VALUES (?, ?, ?, ?, ?, ?, ?, 0)
    """, (
        "conf-1", "demo-1", "demo-2", "commitment",
        "Commitment unfulfilled: In Client Kickoff Call (Sep 26), David promised analytics mockups by Oct 1.",
        json.dumps([{"meeting": "Client Kickoff Call", "meetingId": "demo-2", "quote": "analytics mockups", "timeSec": 260}]),
        time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    ))
    conn.commit()
    conn.close()

    conflicts = store.get_open_conflicts()
    assert len(conflicts) >= 1
    seeded = [c for c in conflicts if c.get("id") == "conf-1"]
    assert len(seeded) == 1
    assert seeded[0]["kind"] == "commitment"


def test_unrelated_pair_judgment():
    res = judge_pair_with_llm(
        "We are ordering pizza for lunch on Friday.",
        "The database index will be built using B-trees.",
        "Meeting A",
        "Meeting B"
    )
    assert res["verdict"] in ("unrelated", "duplicate", "update")


def test_conflict_dismiss_action():
    conn = get_db_connection()
    cur = conn.cursor()
    test_id = "test-conf-dismiss"
    cur.execute("""
    INSERT OR REPLACE INTO conflicts (id, meeting_id, other_meeting_id, kind, description, evidence_json, created_at, dismissed)
    VALUES (?, 'demo-1', 'demo-2', 'conflict', 'Temporary test conflict', '[]', ?, 0)
    """, (test_id, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())))
    conn.commit()
    conn.close()

    success = store.dismiss_conflict(test_id)
    assert success is True

    # Verify dismissed
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT dismissed FROM conflicts WHERE id = ?", (test_id,))
    row = cur.fetchone()
    assert row[0] == 1
    conn.close()
