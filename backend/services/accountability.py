"""
Accountability Service (Prompt A):
1. Commitment Strength Classification (firm, soft, vague)
2. Unanswered Questions Tracker & Cross-Meeting Carry-Over
"""

import json
import re
import time
from typing import List, Dict, Any, Optional

try:
    from db import get_db_connection
    from quote_verification import quote_exists
    from foundry_client import foundry_client
except ImportError:
    from backend.db import get_db_connection
    from backend.quote_verification import quote_exists
    from backend.foundry_client import foundry_client


HEDGE_LEXICON = [
    "maybe", "might", "probably", "i'll try", "hopefully", "we should",
    "someone", "at some point", "let's see", "if possible", "i think i can",
    "potentially", "perhaps", "look into", "explore", "consider"
]


def classify_task_commitment(task: Dict[str, Any], segments_text: str = "") -> Dict[str, Any]:
    """
    Classifies an action item as 'firm', 'soft', or 'vague' mostly in code
    using hedge lexicon and owner/deadline presence.
    """
    title = (task.get("title") or "").lower()
    quote = (task.get("quote") or "").lower()
    owner = (task.get("owner") or "").strip().lower()
    deadline = task.get("deadline") or task.get("deadlineRaw")

    text_to_scan = f"{title} {quote}"

    # Find hedge words
    detected_hedges = [h for h in HEDGE_LEXICON if h in text_to_scan]

    # Deterministic rule checks
    has_valid_owner = bool(owner and owner not in ("team", "unassigned", "anyone", "all", "tbd"))
    has_valid_deadline = bool(deadline and str(deadline).lower() not in ("none", "unscheduled", "tbd"))

    if not has_valid_owner or not has_valid_deadline:
        strength = "vague"
        reason = "Missing specific owner or explicit deadline."
    elif detected_hedges:
        strength = "soft"
        reason = f"Contains hedging or non-committal language ({', '.join(detected_hedges[:2])})."
    else:
        strength = "firm"
        reason = f"Explicit promise with dedicated owner ({task.get('owner')}) and deadline."

    return {
        "strength": strength,
        "reason": reason,
        "hedge_words": detected_hedges
    }


def detect_questions_in_segments(arg1, arg2=None) -> List[Dict[str, Any]]:
    """
    Detects substantial questions in transcript turns using sentence structure and question words.
    """
    if isinstance(arg1, str) and isinstance(arg2, list):
        meeting_id = arg1
        segments = arg2
    else:
        segments = arg1 or []
        meeting_id = arg2 or "meeting"

    questions = []
    question_starters = ("what", "why", "how", "who", "when", "where", "can we", "could we", "should we", "is there", "are we", "do we")

    for i, seg in enumerate(segments):
        text = seg.get("text", "")
        sentences = re.split(r'[.!?]+', text)
        for s in sentences:
            s_clean = s.strip()
            if not s_clean or len(s_clean) < 12:
                continue

            is_q = "?" in text or any(s_clean.lower().startswith(qs) for qs in question_starters)
            if is_q:
                # Lookahead up to 4 segments for a direct answer
                answer_quote = None
                answer_time = None
                status = "unanswered"

                for next_seg in segments[i+1 : i+5]:
                    next_text = next_seg.get("text", "")
                    if len(next_text) > 15 and not next_text.endswith("?"):
                        answer_quote = next_text
                        answer_time = next_seg.get("startSec", 0.0)
                        status = "answered"
                        break

                q_id = f"q-{seg.get('meetingId', 'm')}-{len(questions) + 1}"
                questions.append({
                    "id": q_id,
                    "meeting_id": seg.get("meetingId"),
                    "asker_speaker_id": seg.get("speakerId"),
                    "question": s_clean + ("?" if not s_clean.endswith("?") else ""),
                    "start_sec": seg.get("startSec", 0.0),
                    "status": status,
                    "answer_quote": answer_quote,
                    "answer_start_sec": answer_time,
                    "carried_from_meeting_id": None,
                    "resolved": 1 if status == "answered" else 0
                })

                if len(questions) >= 8:
                    break
        if len(questions) >= 8:
            break

    return questions


def resolve_unanswered_questions_carryover(new_meeting_id: str, segments: List[Dict[str, Any]]) -> int:
    """
    Carries over past unanswered questions and checks if new meeting segments answer them.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT id, meeting_id, question, asker_speaker_id
    FROM questions
    WHERE status != 'answered' AND resolved = 0 AND meeting_id != ?
    """, (new_meeting_id,))
    open_questions = cur.fetchall()

    resolved_count = 0
    full_text = " ".join([s.get("text", "") for s in segments])

    for q in open_questions:
        q_text = q["question"]
        q_vec = foundry_client.get_embedding(q_text)

        for s in segments:
            s_vec = foundry_client.get_embedding(s.get("text", ""))
            # Simple dot-product / cosine similarity
            sim = sum(a * b for a, b in zip(q_vec, s_vec))
            if sim >= 0.78:
                # Verify quote
                if quote_exists(s.get("text", ""), full_text):
                    cur.execute("""
                    UPDATE questions
                    SET status = 'answered', answer_quote = ?, answer_start_sec = ?, carried_from_meeting_id = ?, resolved = 1
                    WHERE id = ?
                    """, (s.get("text"), s.get("startSec"), new_meeting_id, q["id"]))
                    resolved_count += 1
                    break

    conn.commit()
    conn.close()
    return resolved_count
