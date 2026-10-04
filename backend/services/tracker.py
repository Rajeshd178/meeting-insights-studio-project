"""
Meeting Studio — Cross-Meeting Contradiction and Conflict Tracker
"""

import json
import time
from typing import Dict, Any, List
from db import get_db_connection
from quote_verification import quote_exists

def verify_quote_in_transcript(conn, meeting_id: str, quote: str) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT text FROM segments WHERE meeting_id = ?", (meeting_id,))
    rows = cur.fetchall()
    full_text = " ".join(r[0] for r in rows)
    return quote_exists(quote, full_text, threshold=0.70)

def judge_pair_with_llm(text_a: str, text_b: str, title_a: str = "", title_b: str = "") -> Dict[str, Any]:
    # Deterministic comparison heuristic with fallback
    lower_a = text_a.lower()
    lower_b = text_b.lower()
    
    # If discussing completely different things:
    words_a = set(lower_a.split())
    words_b = set(lower_b.split())
    overlap = len(words_a.intersection(words_b)) / max(1, min(len(words_a), len(words_b)))
    
    if overlap < 0.2:
        return {"verdict": "unrelated", "explanation": "Different operational topics"}
    
    # Contradiction keywords
    if any(neg in lower_a or neg in lower_b for neg in ["cancel", "delayed", "push back", "unfulfilled"]):
        return {"verdict": "contradiction", "explanation": "Conflicting commitments or timelines detected"}
        
    return {"verdict": "update", "explanation": "Related follow-up item"}

def run_conflict_tracker(meeting_id: Any = None) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, meeting_id, other_meeting_id, kind, description, evidence_json FROM conflicts WHERE dismissed = 0")
    rows = cur.fetchall()
    conflicts = []
    for r in rows:
        conflicts.append({
            "id": r[0],
            "meetingId": r[1],
            "otherMeetingId": r[2],
            "kind": r[3],
            "detail": r[4],
            "evidence": json.loads(r[5]) if r[5] else []
        })
    conn.close()
    return conflicts
