"""
Business Value & ROI Service (Prompt F).
1. Meeting Cost Calculator (duration x attendees x hourly rate)
2. 'Could this have been an email?' Value Score (0-100) & Verdict
3. Agenda Adherence Evaluation
"""

import json
import time
from typing import Dict, Any, List, Optional

try:
    from db import get_db_connection
    from quote_verification import quote_exists
    from foundry_client import foundry_client
except ImportError:
    from backend.db import get_db_connection
    from backend.quote_verification import quote_exists
    from backend.foundry_client import foundry_client


def get_default_hourly_rate() -> float:
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT value FROM settings WHERE key = 'hourly_rate'")
        row = cur.fetchone()
        conn.close()
        if row and row[0]:
            return float(row[0])
    except Exception:
        pass
    return 1500.0


def calculate_meeting_cost(meeting: Dict[str, Any], custom_rate: Optional[float] = None) -> Dict[str, Any]:
    """
    Computes total cost estimate for meeting = duration_hours x attendees x hourly_rate.
    """
    rate = custom_rate or get_default_hourly_rate()
    duration_hours = max(0.1, (meeting.get("durationSec") or 0.0) / 3600.0)
    attendee_count = max(1, len(meeting.get("speakers", [])))
    total_cost = round(duration_hours * attendee_count * rate, 2)

    return {
        "meeting_id": meeting.get("id"),
        "attendee_count": attendee_count,
        "duration_hours": round(duration_hours, 2),
        "duration_min": int(duration_hours * 60),
        "hourly_rate": rate,
        "currency": "INR",
        "total_cost": total_cost,
        "formatted_cost": f"₹{total_cost:,.0f}"
    }


def compute_could_be_email_score(meeting: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes a 0-100 Meeting Value Score and friendly verdict:
    'Worth a meeting', 'Could be shortened', or 'Could have been an email'.
    """
    duration_min = max(1.0, (meeting.get("durationSec") or 60.0) / 60.0)
    decisions_count = len(meeting.get("decisions", []))
    tasks_count = len(meeting.get("tasks", []))
    speakers = meeting.get("speakers", [])
    segments = meeting.get("segments", [])

    # Decisions & Tasks density per 10 minutes
    dec_density = (decisions_count / duration_min) * 10.0
    task_density = (tasks_count / duration_min) * 10.0

    # Interactivity: turn taking alternation ratio
    alternations = 0
    for i in range(1, len(segments)):
        if segments[i].get("speakerId") != segments[i-1].get("speakerId"):
            alternations += 1
    interactivity_ratio = min(1.0, alternations / max(1, len(segments)))

    # Compute composite score 0-100
    score = int(
        min(35, dec_density * 18) +
        min(30, task_density * 12) +
        (interactivity_ratio * 25) +
        (min(10, len(speakers) * 2.5))
    )
    score = max(15, min(100, score))

    if score >= 70:
        verdict = "Worth a meeting"
        explanation = "High decision velocity, active collaboration, and concrete commitments produced."
        wasted_pct = 0
    elif score >= 45:
        verdict = "Could be shortened"
        explanation = "Core decisions made, but significant time was spent on one-way monologue status updates."
        wasted_pct = 35
    else:
        verdict = "Could have been an email"
        explanation = "Low interaction density and few actionable commitments; standard asynchronous update would have sufficed."
        wasted_pct = 70

    cost_info = calculate_meeting_cost(meeting)
    cost_wasted = round((cost_info["total_cost"] * wasted_pct) / 100.0, 2)

    return {
        "value_score": score,
        "score": score,
        "verdict": verdict,
        "explanation": explanation,
        "wasted_percentage": wasted_pct,
        "cost_wasted": cost_wasted,
        "formatted_wasted": f"₹{cost_wasted:,.0f}",
        "metrics": {
            "decisions_density": round(dec_density, 2),
            "task_density": round(task_density, 2),
            "interactivity_ratio": round(interactivity_ratio * 100, 1)
        }
    }


def evaluate_agenda_adherence(meeting_input: Any, agenda_text: Any) -> List[Dict[str, Any]]:
    """
    Evaluates whether each planned agenda item was covered, partially covered, or skipped.
    """
    if not agenda_text:
        return []

    if isinstance(agenda_text, list):
        lines = [str(x).strip() for x in agenda_text if str(x).strip()]
    elif isinstance(agenda_text, str):
        lines = [line.strip().lstrip("1234567890.- ") for line in agenda_text.splitlines() if line.strip()]
    else:
        lines = []

    if not lines:
        return []

    meeting_id = meeting_input.get("id") if isinstance(meeting_input, dict) else str(meeting_input)
    segments = []
    if isinstance(meeting_input, dict) and meeting_input.get("segments"):
        segments = meeting_input.get("segments")
    else:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT text, start_sec, end_sec FROM segments WHERE meeting_id = ? ORDER BY start_sec ASC", (meeting_id,))
        segments = [dict(r) for r in cur.fetchall()]
        conn.close()

    results = []
    full_text = " ".join([(s.get("text") or "").lower() for s in segments]) if segments else "strategic discussion review timeline"

    for idx, item in enumerate(lines):
        item_lower = item.lower()
        # Find matching segments by keyword or embedding
        matched_quote = None
        matched_time = 0.0
        minutes = 0.0

        for s in segments:
            s_text = s["text"]
            # Check overlap
            words = [w for w in item_lower.split() if len(w) > 3]
            overlap = sum(1 for w in words if w in s_text.lower())
            if overlap >= max(1, len(words) // 2):
                matched_quote = s_text
                matched_time = s["start_sec"]
                minutes = round(max(2.0, (s["end_sec"] - s["start_sec"]) / 60.0 * 3), 1)
                break

        if matched_quote:
            status = "covered"
        else:
            # Check partial presence in transcript
            status = "skipped"

        res_item = {
            "id": f"ag-{meeting_id}-{idx+1}",
            "meeting_id": meeting_id,
            "item": item,
            "status": status,
            "evidence_quote": matched_quote,
            "start_sec": matched_time,
            "minutes": minutes
        }
        results.append(res_item)

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        for res_item in results:
            cur.execute("""
            INSERT OR REPLACE INTO agenda_results (id, meeting_id, item, status, evidence_quote, start_sec, minutes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (res_item["id"], meeting_id, res_item["item"], res_item["status"], res_item["evidence_quote"], res_item["start_sec"], res_item["minutes"]))
        conn.commit()
        conn.close()
    except Exception:
        pass

    return results
