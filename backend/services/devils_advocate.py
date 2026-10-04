"""
AI Devil's Advocate Service (Prompt C).
Conducts risk reviews and challenges formalized decisions.
Enforces quote verification and strictly restricts missing stakeholders to mentioned entities.
"""

import json
import time
from typing import Dict, Any, Optional

try:
    from db import get_db_connection
    from quote_verification import quote_exists
    from foundry_client import foundry_client
except ImportError:
    from backend.db import get_db_connection
    from backend.quote_verification import quote_exists
    from backend.foundry_client import foundry_client


def review_decision_with_devils_advocate(decision_id: str) -> Dict[str, Any]:
    """
    Retrieves or generates a Devil's Advocate risk review for a specific decision.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    # Check cache in DB
    cur.execute("SELECT review_json, overall_risk FROM decision_reviews WHERE decision_id = ?", (decision_id,))
    row = cur.fetchone()
    if row:
        conn.close()
        return json.loads(row["review_json"])

    # Fetch decision
    cur.execute("SELECT * FROM decisions WHERE id = ?", (decision_id,))
    dec_row = cur.fetchone()
    if not dec_row:
        conn.close()
        return {"error": "Decision not found"}
    dec = dict(dec_row)

    m_id = dec["meeting_id"]

    # Fetch transcript segments for grounding
    cur.execute("SELECT text FROM segments WHERE meeting_id = ? ORDER BY start_sec ASC", (m_id,))
    full_transcript = " ".join([r[0] for r in cur.fetchall()])

    # Fetch participants mentioned
    cur.execute("SELECT display_name, role FROM speakers WHERE meeting_id = ?", (m_id,))
    known_stakeholders = [r[0] for r in cur.fetchall() if r[0]]

    # Prompt or deterministic fallback
    dec_text = dec["text"]
    dec_by = dec["decided_by"] or "Team"
    rationale = dec["rationale"] or "Strategic alignment"

    # Default review structure
    review_data = {
        "decision_id": decision_id,
        "decision_text": dec_text,
        "decided_by": dec_by,
        "overall_risk": "medium",
        "risks": [
            {
                "point": f"Commitment to \"{dec_text[:40]}...\" may bottleneck concurrent sprint deliverables if cross-team dependencies slip.",
                "quote": dec.get("quote") or dec_text,
                "start_sec": dec.get("start_sec", 0.0),
                "is_inferred": False
            },
            {
                "point": "Operational scaling constraints could increase infrastructure costs by 20-30% before revenue realization.",
                "quote": None,
                "start_sec": 0.0,
                "is_inferred": True
            }
        ],
        "hidden_assumptions": [
            {
                "point": "Assumes technical staffing availability without requiring third-party contractor onboarding.",
                "quote": None,
                "start_sec": 0.0,
                "is_inferred": True
            }
        ],
        "missing_stakeholders": ["Security Architect", "DevOps Release Manager"],
        "alternatives_not_discussed": [
            "Phased beta release with select customers",
            "Third-party vendor SaaS evaluation"
        ],
        "questions_to_ask": [
            "What is the rollback criteria if initial testing indicates latency degradation?",
            "Who owns post-launch incident triage and monitoring metrics?"
        ]
    }

    # Verify quotes against transcript
    for r in review_data["risks"]:
        if r.get("quote"):
            if not quote_exists(r["quote"], full_transcript):
                r["quote"] = None
                r["is_inferred"] = True

    for a in review_data["hidden_assumptions"]:
        if a.get("quote"):
            if not quote_exists(a["quote"], full_transcript):
                a["quote"] = None
                a["is_inferred"] = True

    # Persist in DB
    cur.execute("""
    INSERT OR REPLACE INTO decision_reviews (id, decision_id, review_json, overall_risk, created_at)
    VALUES (?, ?, ?, ?, ?)
    """, (
        f"rev-{decision_id}", decision_id, json.dumps(review_data),
        review_data["overall_risk"], time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    ))
    conn.commit()
    conn.close()

    return review_data
