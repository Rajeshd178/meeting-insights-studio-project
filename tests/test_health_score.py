"""
Unit tests for Meeting Health Score computation and overdue task queries.
Tests bounds [0, 100] and edge cases (single speaker, no tasks, no decisions).
"""

# pyrefly: ignore [missing-import]
import pytest
import sqlite3
import json
import time
from backend.services.analytics import compute_health_score
from backend.db import get_db_connection, init_db
from backend.store import MeetingStore, format_human_duration, format_meeting_type_label


@pytest.fixture
def temp_db(tmp_path):
    db_file = str(tmp_path / "test_studio.db")
    init_db(db_file)
    return db_file


def test_format_human_duration():
    assert format_human_duration(45) == "45s"
    assert format_human_duration(120) == "2 min"
    assert format_human_duration(1500) == "25 min"
    assert format_human_duration(3600) == "1h"
    assert format_human_duration(4320) == "1h 12m"


def test_format_meeting_type_label():
    assert format_meeting_type_label("client_call") == "Client Call"
    assert format_meeting_type_label("standup") == "Standup"
    assert format_meeting_type_label("retro") == "Retrospective"
    assert format_meeting_type_label("planning") == "Planning"


def test_health_score_bounds_and_breakdown(temp_db):
    conn = get_db_connection(temp_db)
    cur = conn.cursor()

    # Normal meeting test
    cur.execute("SELECT id FROM meetings LIMIT 1")
    m_id = cur.fetchone()[0]

    score, breakdown = compute_health_score(m_id, conn=conn)

    assert 0 <= score <= 100
    assert isinstance(score, int)
    assert len(breakdown) == 5
    for item in breakdown:
        assert 0 <= item["score"] <= 100
        assert item["weight"] > 0
        assert "explanation" in item
    conn.close()


def test_health_score_edge_case_single_speaker(temp_db):
    conn = get_db_connection(temp_db)
    cur = conn.cursor()

    # Create meeting with single speaker, no decisions, no tasks
    cur.execute("""
    INSERT INTO meetings (id, title, meeting_date, duration_sec, meeting_type)
    VALUES ('edge-1', 'Monologue Presentation', '2026-10-04', 300.0, 'general')
    """)
    cur.execute("""
    INSERT INTO segments (id, meeting_id, idx, speaker_id, speaker_label, start_sec, end_sec, text, sentiment)
    VALUES ('seg-e1', 'edge-1', 0, 'spk-1', 'Solo Speaker', 0, 300, 'I spoke for the entire duration alone.', 'neutral')
    """)
    conn.commit()

    score, breakdown = compute_health_score('edge-1', conn=conn)

    assert 0 <= score <= 100
    # Participation balance should handle single speaker gracefully
    part_item = next(b for b in breakdown if b["label"] == "Participation Balance")
    assert part_item["score"] <= 70
    assert "Single" in part_item["explanation"]
    conn.close()


def test_health_score_edge_case_no_tasks_no_decisions(temp_db):
    conn = get_db_connection(temp_db)
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO meetings (id, title, meeting_date, duration_sec, meeting_type)
    VALUES ('edge-2', 'Brainstorm Session', '2026-10-04', 600.0, 'brainstorm')
    """)
    cur.execute("""
    INSERT INTO segments (id, meeting_id, idx, speaker_id, speaker_label, start_sec, end_sec, text, sentiment)
    VALUES ('seg-e2', 'edge-2', 0, 'spk-1', 'Alice', 0, 100, 'Great idea!', 'positive'),
           ('seg-e3', 'edge-2', 1, 'spk-2', 'Bob', 100, 200, 'I agree with this direction.', 'positive')
    """)
    conn.commit()

    score, breakdown = compute_health_score('edge-2', conn=conn)

    assert 0 <= score <= 100
    dec_item = next(b for b in breakdown if b["label"] == "Decision Density")
    task_item = next(b for b in breakdown if b["label"] == "Action-Item Clarity")
    assert "No formal decisions" in dec_item["explanation"]
    assert "No action items" in task_item["explanation"]
    conn.close()


def test_overdue_tasks_query(temp_db):
    conn = get_db_connection(temp_db)
    cur = conn.cursor()

    cur.execute("SELECT id FROM meetings LIMIT 1")
    m_id = cur.fetchone()[0]

    # Insert an overdue task (deadline in past, status != 'done')
    cur.execute("""
    INSERT INTO tasks (id, meeting_id, title, owner, deadline, status, quote, created_at, updated_at)
    VALUES ('t-overdue', ?, 'Overdue Report', 'Raj Patel', '2026-09-01', 'todo', 'quote', '2026-09-01', '2026-09-01')
    """, (m_id,))

    # Insert a task in the past but marked done
    cur.execute("""
    INSERT INTO tasks (id, meeting_id, title, owner, deadline, status, quote, created_at, updated_at)
    VALUES ('t-done-past', ?, 'Completed Task', 'Raj Patel', '2026-09-01', 'done', 'quote', '2026-09-01', '2026-09-01')
    """, (m_id,))
    conn.commit()

    # Query overdue tasks
    today = time.strftime("%Y-%m-%d")
    cur.execute("""
    SELECT COUNT(*) FROM tasks WHERE status != 'done' AND deadline IS NOT NULL AND deadline != '' AND date(deadline) < date(?)
    """, (today,))
    overdue_count = cur.fetchone()[0]

    assert overdue_count >= 1
    conn.close()
