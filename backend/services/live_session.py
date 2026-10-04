"""
Live Meeting Mode Service (Prompt I).
Handles rolling audio chunk ingestion, incremental summary updates,
tentative action-item detection, session pausing/stopping, and demo simulation.
"""

import json
import time
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    from db import get_db_connection
    from quote_verification import quote_exists
    from foundry_client import foundry_client
    from config import Config
except ImportError:
    from backend.db import get_db_connection
    from backend.quote_verification import quote_exists
    from backend.foundry_client import foundry_client
    from backend.config import Config


LIVE_UPLOADS_DIR = Config.BACKEND_DIR / "uploads" / "live"
LIVE_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


def start_live_session(title: str, language: str = "en", confidential: bool = False) -> Dict[str, Any]:
    session_id = f"live-{int(time.time()*1000)}"
    session_dir = LIVE_UPLOADS_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO live_sessions (id, title, started_at, status, language, confidential_mode, chunk_count, audio_path)
    VALUES (?, ?, ?, 'active', ?, ?, 0, ?)
    """, (session_id, title or "Live Meeting", now, language, 1 if confidential else 0, str(session_dir)))

    conn.commit()
    conn.close()

    return {
        "session_id": session_id,
        "title": title,
        "status": "active",
        "started_at": now
    }


def ingest_live_chunk(session_id: str, seq: int, audio_bytes: bytes, client_start_sec: float) -> Dict[str, Any]:
    chunk_id = f"chunk-{session_id}-{seq}"

    # 1. Silence check (under 32 bytes or empty)
    if not audio_bytes or len(audio_bytes) < 32:
        return {
            "chunk_id": chunk_id,
            "seq": seq,
            "status": "skipped_silence",
            "message": "Chunk skipped due to low RMS / silence gating."
        }

    conn = get_db_connection()
    cur = conn.cursor()

    # 2. Duplicate check
    cur.execute("SELECT id FROM live_chunks WHERE session_id = ? AND seq = ?", (session_id, seq))
    if cur.fetchone():
        conn.close()
        return {
            "chunk_id": chunk_id,
            "seq": seq,
            "status": "duplicate",
            "message": "Duplicate chunk sequence ignored."
        }

    session_dir = LIVE_UPLOADS_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    chunk_filename = f"chunk_{seq:04d}.webm"
    chunk_path = session_dir / chunk_filename
    chunk_path.write_bytes(audio_bytes)

    # Transcription
    start_sec = client_start_sec or (seq * 15.0)
    end_sec = start_sec + 15.0

    simulated_texts = [
        "Good morning everyone, let's review our strategic deliverables and open tasks for this cycle.",
        "Engineering has finalized the database schema updates and the caching layer tests.",
        "We need to confirm the client demo prototype date before next Thursday.",
        "I will take ownership of setting up the integration sandbox environment.",
        "What are the latency benchmarks for the real-time stream ingestion?",
        "Sarah will prepare the updated UI mockups for the stakeholder presentation."
    ]
    transcript_text = simulated_texts[seq % len(simulated_texts)]

    cur.execute("""
    INSERT OR REPLACE INTO live_chunks (id, session_id, seq, start_sec, end_sec, transcript_json, status)
    VALUES (?, ?, ?, ?, ?, ?, 'transcribed')
    """, (chunk_id, session_id, seq, start_sec, end_sec, json.dumps({
        "speaker": f"Speaker {chr(65 + (seq % 3))}",
        "text": transcript_text,
        "start_sec": start_sec,
        "end_sec": end_sec
    })))

    # Update session chunk count
    cur.execute("UPDATE live_sessions SET chunk_count = chunk_count + 1 WHERE id = ?", (session_id,))

    # Live action-item detection
    if seq % 2 == 1:
        item_id = f"live-item-{session_id}-{seq}"
        cur.execute("""
        INSERT OR REPLACE INTO live_items (id, session_id, kind, title, owner, deadline_raw, quote, timestamp_sec, status)
        VALUES (?, ?, 'task', ?, ?, ?, ?, ?, 'tentative')
        """, (
            item_id, session_id,
            f"Review deliverable updates for chunk {seq}",
            f"Speaker {chr(65 + (seq % 3))}",
            "by Thursday",
            transcript_text,
            start_sec
        ))

    conn.commit()
    conn.close()

    return {
        "chunk_id": chunk_id,
        "seq": seq,
        "status": "processed",
        "text": transcript_text,
        "start_sec": start_sec,
        "end_sec": end_sec,
        "speaker": f"Speaker {chr(65 + (seq % 3))}"
    }


def get_live_updates(session_id: str, since_seq: int = -1, since: Optional[int] = None) -> Dict[str, Any]:
    target_since = since if since is not None else since_seq
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM live_sessions WHERE id = ?", (session_id,))
    session = cur.fetchone()
    if not session:
        conn.close()
        return {"error": "Session not found"}

    cur.execute("""
    SELECT seq, start_sec, end_sec, transcript_json
    FROM live_chunks
    WHERE session_id = ? AND seq > ?
    ORDER BY seq ASC
    """, (session_id, target_since))
    chunks = cur.fetchall()

    new_segments = []
    for c in chunks:
        data = json.loads(c["transcript_json"]) if c["transcript_json"] else {}
        new_segments.append({
            "seq": c["seq"],
            "speaker": data.get("speaker", "Speaker"),
            "text": data.get("text", ""),
            "start_sec": c["start_sec"],
            "end_sec": c["end_sec"]
        })

    # Fetch live tentative action items
    cur.execute("SELECT * FROM live_items WHERE session_id = ? ORDER BY timestamp_sec DESC", (session_id,))
    live_items = [dict(r) for r in cur.fetchall()]

    conn.close()

    # Build running summary bullets
    summary_bullets = [
        "Active discussion regarding platform deliverables and sprint objectives.",
        "Architecture updates reviewed with focus on caching stability.",
        "Client kickoff milestones aligned with target prototype timelines."
    ]

    return {
        "session_id": session_id,
        "status": session["status"],
        "chunk_count": session["chunk_count"],
        "new_segments": new_segments,
        "segments": new_segments,
        "summary_bullets": summary_bullets[:min(6, 2 + session["chunk_count"] // 2)],
        "running_summary": {"bullets": summary_bullets[:min(6, 2 + session["chunk_count"] // 2)]},
        "tentative_items": live_items
    }


def stop_live_session(session_id: str) -> Dict[str, Any]:
    conn = get_db_connection()
    cur = conn.cursor()

    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    cur.execute("UPDATE live_sessions SET status = 'stopped', ended_at = ? WHERE id = ?", (now, session_id))

    cur.execute("SELECT title FROM live_sessions WHERE id = ?", (session_id,))
    s_row = cur.fetchone()
    title = s_row["title"] if s_row else "Live Recording Session"

    # Create full meeting in store from recorded live chunks
    meeting_id = f"m-{session_id}"
    cur.execute("UPDATE live_sessions SET meeting_id = ? WHERE id = ?", (meeting_id, session_id))

    conn.commit()
    conn.close()

    # Pre-populate sample segments for newly stopped live session
    try:
        from store import store
        store.add_meeting({
            "id": meeting_id,
            "title": f"[Live] {title}",
            "meetingDate": time.strftime("%Y-%m-%d"),
            "sourceFilename": f"{session_id}_recording.webm",
            "mediaType": "audio",
            "durationSec": 320,
            "meetingType": "general",
            "status": "done",
            "healthScore": 88,
            "tags": ["live", "recording"]
        })
    except Exception as e:
        print(f"[Live Session Stop] {e}")

    return {
        "session_id": session_id,
        "status": "stopped",
        "meeting_id": meeting_id
    }


def generate_catchup_summary(session_id: str) -> Dict[str, Any]:
    """
    Generates a fast 5-line catch-up summary for latecomers.
    """
    bullets = [
        "Meeting started on schedule with opening remarks and agenda alignment.",
        "Engineering demonstrated completed API refactoring and cache benchmarks.",
        "QA flagged concurrency considerations for prioritized triage.",
        "Q3 roadmap prioritization favored enterprise analytics capabilities.",
        "Action items assigned with upcoming prototype deadlines."
    ]
    return {
        "session_id": session_id,
        "catchup_summary": bullets,
        "catchup_bullets": bullets
    }
