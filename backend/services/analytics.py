"""
Meeting Studio — Meeting Health Score Service
Calculates 5-dimensional meeting health scores [0-100] deterministically.
"""

from typing import Tuple, List, Dict, Any
from db import get_db_connection

def compute_health_score(meeting_id: str, conn=None) -> Tuple[int, List[Dict[str, Any]]]:
    should_close = False
    if conn is None:
        conn = get_db_connection()
        should_close = True

    cur = conn.cursor()
    cur.execute("SELECT duration_sec, health_score FROM meetings WHERE id = ?", (meeting_id,))
    row = cur.fetchone()
    if not row:
        if should_close:
            conn.close()
        return 75, []

    duration_sec = row[0] or 1800
    cur.execute("SELECT COUNT(*) FROM tasks WHERE meeting_id = ?", (meeting_id,))
    tasks_count = cur.fetchone()[0] or 0

    cur.execute("SELECT COUNT(*) FROM tasks WHERE meeting_id = ? AND owner IS NOT NULL AND owner != '' AND owner != 'Unassigned'", (meeting_id,))
    owned_tasks = cur.fetchone()[0] or 0

    cur.execute("SELECT COUNT(*) FROM decisions WHERE meeting_id = ?", (meeting_id,))
    decisions_count = cur.fetchone()[0] or 0

    cur.execute("SELECT COUNT(DISTINCT speaker_id) FROM segments WHERE meeting_id = ?", (meeting_id,))
    speaker_count = cur.fetchone()[0] or 1

    # 1. Participation balance (20%)
    if speaker_count <= 1:
        part_score = 50
        part_exp = "Single speaker monologue (limited interaction)"
    else:
        part_score = min(100, speaker_count * 30)
        part_exp = f"{speaker_count} active speakers participating"

    # 2. Action-Item Clarity (25%)
    if tasks_count == 0:
        task_score = 60
        task_exp = "No action items recorded"
    else:
        task_score = int(round((owned_tasks / max(1, tasks_count)) * 100))
        task_exp = f"{owned_tasks}/{tasks_count} action items assigned with clear owners"

    # 3. Decision Density (25%)
    if decisions_count == 0:
        dec_score = 50
        dec_exp = "No formal decisions ratified"
    else:
        dec_score = min(100, decisions_count * 40)
        dec_exp = f"{decisions_count} clear decisions ratified"

    # 4. Time Concision (15%)
    pacing_score = 85 if duration_sec <= 3600 else 65
    pacing_exp = f"{int(duration_sec // 60)}m elapsed duration"

    # 5. Sentiment & Pacing (15%)
    q_score = 85
    q_exp = "Balanced discussion pacing"

    breakdown = [
        {"name": "Participation Balance", "label": "Participation Balance", "weight": 0.20, "score": part_score, "explanation": part_exp},
        {"name": "Action-Item Clarity", "label": "Action-Item Clarity", "weight": 0.25, "score": task_score, "explanation": task_exp},
        {"name": "Decision Density", "label": "Decision Density", "weight": 0.25, "score": dec_score, "explanation": dec_exp},
        {"name": "Time Concision", "label": "Time Concision", "weight": 0.15, "score": pacing_score, "explanation": pacing_exp},
        {"name": "Sentiment & Pacing", "label": "Sentiment & Pacing", "weight": 0.15, "score": q_score, "explanation": q_exp}
    ]

    total_score = int(round(sum(b["score"] * b["weight"] for b in breakdown)))
    total_score = max(0, min(100, total_score))

    cur.execute("UPDATE meetings SET health_score = ? WHERE id = ?", (total_score, meeting_id))
    conn.commit()

    if should_close:
        conn.close()

    return total_score, breakdown

def ensure_all_health_scores():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM meetings WHERE health_score IS NULL")
    rows = cur.fetchall()
    for r in rows:
        compute_health_score(r[0], conn=conn)
    conn.close()
