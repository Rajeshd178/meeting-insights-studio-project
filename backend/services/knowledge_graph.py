"""
Meeting Knowledge Graph Service (Prompt E).
Builds an interactive graph connecting People, Meetings, Topics, Decisions, and Tasks.
Constructed 100% in code from database records.
"""

import json
from typing import Dict, Any, List, Optional

try:
    from db import get_db_connection
except ImportError:
    from backend.db import get_db_connection


def build_knowledge_graph(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    m_type: Optional[str] = None,
    person: Optional[str] = None,
    person_focus: Optional[str] = None
) -> Dict[str, Any]:
    """
    Constructs node-link graph data for D3 / Force-directed layout.
    """
    person = person or person_focus
    conn = get_db_connection()
    cur = conn.cursor()

    sql_meetings = "SELECT id, title, meeting_date, meeting_type FROM meetings WHERE 1=1"
    params = []
    if from_date:
        sql_meetings += " AND meeting_date >= ?"
        params.append(from_date)
    if to_date:
        sql_meetings += " AND meeting_date <= ?"
        params.append(to_date)
    if m_type and m_type.lower() != "all":
        sql_meetings += " AND LOWER(meeting_type) = LOWER(?)"
        params.append(m_type)

    cur.execute(sql_meetings, params)
    meetings = cur.fetchall()
    meeting_ids = [m["id"] for m in meetings]

    if not meeting_ids:
        conn.close()
        return {"nodes": [], "edges": []}

    placeholders = ",".join("?" for _ in meeting_ids)

    # 1. Fetch Speakers / People
    cur.execute(f"SELECT meeting_id, display_name, role, color FROM speakers WHERE meeting_id IN ({placeholders})", meeting_ids)
    speakers = cur.fetchall()

    # 2. Fetch Decisions
    cur.execute(f"SELECT id, meeting_id, text, decided_by FROM decisions WHERE meeting_id IN ({placeholders})", meeting_ids)
    decisions = cur.fetchall()

    # 3. Fetch Tasks
    cur.execute(f"SELECT id, meeting_id, title, owner, status, priority FROM tasks WHERE meeting_id IN ({placeholders})", meeting_ids)
    tasks = cur.fetchall()

    # 4. Fetch Conflicts
    cur.execute(f"SELECT id, meeting_id, other_meeting_id, kind, description FROM conflicts WHERE dismissed = 0 AND meeting_id IN ({placeholders})", meeting_ids)
    conflicts = cur.fetchall()

    conn.close()

    nodes_map = {}
    edges = []

    # Add Meeting Nodes
    for m in meetings:
        nodes_map[m["id"]] = {
            "id": m["id"],
            "type": "meeting",
            "label": m["title"],
            "date": m["meeting_date"],
            "weight": 14,
            "color": "#6366f1"
        }

    # Add People Nodes (Merged case-insensitively)
    people_map = {}
    for s in speakers:
        name = s["display_name"].strip()
        if not name:
            continue
        key = name.lower()
        if key not in people_map:
            p_id = f"person-{key.replace(' ', '_')}"
            people_map[key] = {
                "id": p_id,
                "type": "person",
                "label": name,
                "role": s["role"] or "Contributor",
                "weight": 12,
                "color": "#10b981"
            }
            nodes_map[p_id] = people_map[key]

        # Edge: Person attended Meeting
        edges.append({
            "source": people_map[key]["id"],
            "target": s["meeting_id"],
            "type": "attended"
        })

    # Add Decision Nodes & Edges
    for d in decisions:
        d_id = f"dec-{d['id']}"
        nodes_map[d_id] = {
            "id": d_id,
            "type": "decision",
            "label": d["text"][:38] + ("..." if len(d["text"]) > 38 else ""),
            "full_text": d["text"],
            "weight": 10,
            "color": "#f59e0b"
        }
        # Edge: Meeting decided Decision
        edges.append({
            "source": d["meeting_id"],
            "target": d_id,
            "type": "decided"
        })
        # If decided_by matches a known person
        if d["decided_by"]:
            p_key = d["decided_by"].strip().lower()
            if p_key in people_map:
                edges.append({
                    "source": people_map[p_key]["id"],
                    "target": d_id,
                    "type": "advocated"
                })

    # Add Task Nodes & Edges
    for t in tasks:
        t_id = f"task-{t['id']}"
        nodes_map[t_id] = {
            "id": t_id,
            "type": "task",
            "label": t["title"][:36] + ("..." if len(t["title"]) > 36 else ""),
            "status": t["status"],
            "weight": 8,
            "color": "#06b6d4"
        }
        edges.append({
            "source": t["meeting_id"],
            "target": t_id,
            "type": "assigned"
        })
        if t["owner"]:
            p_key = t["owner"].strip().lower()
            if p_key in people_map:
                edges.append({
                    "source": people_map[p_key]["id"],
                    "target": t_id,
                    "type": "owns"
                })

    # Add Conflict Edges (Rendered in red)
    for c in conflicts:
        if c["meeting_id"] in nodes_map and c["other_meeting_id"] in nodes_map:
            edges.append({
                "source": c["meeting_id"],
                "target": c["other_meeting_id"],
                "type": "conflicts_with",
                "label": c["description"][:40],
                "color": "#ef4444"
            })

    # Optional person focus filter
    if person and person.lower() != "all":
        p_key = person.strip().lower()
        if p_key in people_map:
            focus_id = people_map[p_key]["id"]
            connected_ids = {focus_id}
            for e in edges:
                if e["source"] == focus_id:
                    connected_ids.add(e["target"])
                elif e["target"] == focus_id:
                    connected_ids.add(e["source"])

            nodes_map = {k: v for k, v in nodes_map.items() if k in connected_ids}
            edges = [e for e in edges if e["source"] in connected_ids and e["target"] in connected_ids]

    return {
        "nodes": list(nodes_map.values())[:300],
        "edges": edges[:500]
    }
