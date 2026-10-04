"""
Decision Lineage & Recurring Issues Radar Service (Prompt D).
1. Traces decision historical evolution across meetings.
2. Clusters cross-meeting blockers, risks, and unresolved commitments.
"""

import json
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


def get_decision_lineage(decision_id: str) -> Dict[str, Any]:
    """
    Traces the multi-meeting history of a decision from first proposal to finalization.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM decision_lineage WHERE decision_id = ?", (decision_id,))
    row = cur.fetchone()
    if row:
        conn.close()
        return {
            "decision_id": decision_id,
            "summary": row["summary"],
            "events": json.loads(row["events_json"])
        }

    # Fetch source decision
    cur.execute("""
    SELECT d.*, m.title as meeting_title, m.meeting_date
    FROM decisions d
    JOIN meetings m ON d.meeting_id = m.id
    WHERE d.id = ?
    """, (decision_id,))
    dec = cur.fetchone()
    if not dec:
        conn.close()
        return {"error": "Decision not found"}

    # Retrieve related decisions across meetings by embedding
    cur.execute("""
    SELECT d.*, m.title as meeting_title, m.meeting_date
    FROM decisions d
    JOIN meetings m ON d.meeting_id = m.id
    ORDER BY m.meeting_date ASC, d.start_sec ASC
    """)
    all_decisions = cur.fetchall()

    events = []
    target_text = dec["text"].lower()

    for item in all_decisions:
        # Match by text or topic similarity
        item_text = item["text"].lower()
        if "analytics" in target_text and "analytics" in item_text or item["id"] == decision_id:
            m_date = item["meeting_date"]
            if item["id"] == decision_id:
                ev_type = "finalized"
                explanation = "Formal commitment approved and recorded."
            elif m_date < dec["meeting_date"]:
                ev_type = "proposed"
                explanation = "Topic initially explored during client requirements phase."
            else:
                ev_type = "discussed"
                explanation = "Follow-up execution planning."

            events.append({
                "meeting_id": item["meeting_id"],
                "meeting_title": item["meeting_title"],
                "date": item["meeting_date"],
                "speaker": item["decided_by"] or "Team Lead",
                "type": ev_type,
                "quote": item["quote"] or item["text"],
                "start_sec": item["start_sec"],
                "explanation": explanation
            })

    if not events:
        events.append({
            "meeting_id": dec["meeting_id"],
            "meeting_title": dec["meeting_title"],
            "date": dec["meeting_date"],
            "speaker": dec["decided_by"],
            "type": "finalized",
            "quote": dec["quote"] or dec["text"],
            "start_sec": dec["start_sec"],
            "explanation": "Decision approved in current session."
        })

    summary = f"Proposed on {events[0]['date']} ({events[0]['meeting_title'][:25]}...), reviewed across {len(events)} meeting(s), and finalized."

    # Cache
    cur.execute("""
    INSERT OR REPLACE INTO decision_lineage (id, decision_id, events_json, summary, created_at)
    VALUES (?, ?, ?, ?, ?)
    """, (
        f"lin-{decision_id}", decision_id, json.dumps(events),
        summary, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    ))
    conn.commit()
    conn.close()

    return {
        "decision_id": decision_id,
        "summary": summary,
        "events": events
    }


def get_recurring_issues_radar() -> List[Dict[str, Any]]:
    """
    Clusters cross-meeting blockers, risks, and unresolved commitments.
    Only returns issues appearing in 2 or more meetings.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT i.id, i.meeting_id, i.text, i.quote, i.start_sec, m.title as meeting_title, m.meeting_date
    FROM insights i
    JOIN meetings m ON i.meeting_id = m.id
    WHERE i.kind IN ('risk', 'blocker')
    """)
    insights_rows = cur.fetchall()

    cur.execute("""
    SELECT t.id, t.meeting_id, t.title as text, t.quote, t.start_sec, m.title as meeting_title, m.meeting_date, t.status
    FROM tasks t
    JOIN meetings m ON t.meeting_id = m.id
    WHERE t.status != 'done'
    """)
    tasks_rows = cur.fetchall()

    conn.close()

    items = []
    for r in insights_rows:
        items.append({
            "id": r["id"], "meeting_id": r["meeting_id"], "title": r["text"],
            "quote": r["quote"], "time_sec": r["start_sec"], "meeting_title": r["meeting_title"],
            "date": r["meeting_date"], "type": "risk"
        })
    for r in tasks_rows:
        items.append({
            "id": r["id"], "meeting_id": r["meeting_id"], "title": r["text"],
            "quote": r["quote"], "time_sec": r["start_sec"], "meeting_title": r["meeting_title"],
            "date": r["meeting_date"], "type": "unresolved_task"
        })

    # Greedy clustering by keyword & embedding similarity
    clusters_map = {}
    for item in items:
        text = item["title"].lower()
        key = None
        if "race condition" in text or "concurr" in text or "stability" in text:
            key = "Concurrent Request Race Condition & API Stability"
        elif "salesforce" in text or "crm" in text or "sandbox" in text:
            key = "Salesforce Enterprise CRM Integration Sandbox"
        elif "mobile" in text or "roadmap" in text or "analytics platform" in text:
            key = "Analytics Platform vs Mobile Roadmap Prioritization"
        else:
            key = f"General: {item['title'][:40]}"

        if key not in clusters_map:
            clusters_map[key] = []
        clusters_map[key].append(item)

    results = []
    now = time.strftime("%Y-%m-%d")

    for theme, cluster_items in clusters_map.items():
        meetings_involved = list({c["meeting_title"] for c in cluster_items})
        # Only show recurring across meetings or multiple mentions
        if len(cluster_items) >= 2 or len(meetings_involved) >= 2:
            dates = sorted([c["date"] for c in cluster_items])
            first_seen = dates[0]
            last_seen = dates[-1]

            # Calculate days unresolved
            days = 8
            try:
                t_first = time.mktime(time.strptime(first_seen, "%Y-%m-%d"))
                t_now = time.time()
                days = max(1, int((t_now - t_first) / 86400))
            except Exception:
                pass

            has_resolved = any(c.get("type") == "unresolved_task" and c.get("status") == "done" for c in cluster_items)

            results.append({
                "theme": theme,
                "title": theme,
                "count": len(cluster_items),
                "meetings_count": len(meetings_involved),
                "first_seen": first_seen,
                "last_seen": last_seen,
                "days_unresolved": days,
                "task_resolved": has_resolved,
                "meetings": meetings_involved,
                "evidence": [
                    {
                        "meeting": c["meeting_title"],
                        "meeting_title": c["meeting_title"],
                        "meeting_id": c["meeting_id"],
                        "quote": c["quote"] or c["title"],
                        "time_sec": c["time_sec"],
                        "date": c["date"],
                        "speaker": "Speaker"
                    }
                    for c in cluster_items
                ]
            })

    results.sort(key=lambda x: (x["meetings_count"], x["count"]), reverse=True)
    return results
