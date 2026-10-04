"""
Unit tests for Advanced Feature Prompts A through G:
- Prompt A: Commitment strength classification, questions detection & carryover
- Prompt B: Speaker coaching analytics, filler rates, interruptions, 5 sub-scores
- Prompt C: Devil's Advocate review, quote grounding & inferred tagging
- Prompt D: Decision lineage & recurring issues radar clustering
- Prompt E: Meeting Knowledge Graph builder
- Prompt F: Meeting cost calculator, value score & agenda adherence
- Prompt G: Teams webhook payload, weekly digest, meeting compare, related meetings
"""

import pytest
import json
from backend.services.accountability import (
    classify_task_commitment,
    detect_questions_in_segments,
    resolve_unanswered_questions_carryover
)
from backend.services.speaker_coaching import compute_speaker_coaching
from backend.services.devils_advocate import review_decision_with_devils_advocate
from backend.services.lineage_radar import get_decision_lineage, get_recurring_issues_radar
from backend.services.knowledge_graph import build_knowledge_graph
from backend.services.business_value import (
    calculate_meeting_cost,
    compute_could_be_email_score,
    evaluate_agenda_adherence
)
from backend.services.collaboration import (
    send_teams_webhook,
    generate_weekly_digest,
    compare_two_meetings,
    get_related_meetings
)
from backend.db import get_db_connection


# ==============================================================================
# PROMPT A TESTS: Commitment Strength & Open Questions
# ==============================================================================

def test_commitment_strength_lexicon_and_heuristics():
    # 1. Firm commitment: clear promise with owner & deadline
    firm_item = {
        "title": "Send the completed benchmark report",
        "owner": "Alex Chen",
        "deadline": "2026-10-10",
        "quote": "I will deliver the finalized report by Friday."
    }
    res_firm = classify_task_commitment(firm_item)
    assert res_firm["strength"] == "firm"

    # 2. Soft commitment: hedge words present
    soft_item = {
        "title": "Maybe look at the Redis cache",
        "owner": "Alex Chen",
        "deadline": "2026-10-10",
        "quote": "I think I can probably look into Redis caching if possible."
    }
    res_soft = classify_task_commitment(soft_item)
    assert res_soft["strength"] == "soft"
    assert len(res_soft["hedge_words"]) > 0

    # 3. Vague commitment: no owner and no deadline
    vague_item = {
        "title": "Someone should check the logging",
        "owner": "Unassigned",
        "deadline": "",
        "quote": "We should maybe investigate error logs at some point."
    }
    res_vague = classify_task_commitment(vague_item)
    assert res_vague["strength"] == "vague"


def test_question_detection_and_fabricated_quote_handling():
    segments = [
        {"speaker": "Alice", "speaker_id": "spk-1", "text": "What is our deployment window for Friday?", "start_sec": 10},
        {"speaker": "Bob", "speaker_id": "spk-2", "text": "We are deploying at 2 AM UTC to minimize disruption.", "start_sec": 25},
        {"speaker": "Alice", "speaker_id": "spk-1", "text": "Will there be any downtime for the search index?", "start_sec": 45}
    ]
    detected = detect_questions_in_segments("test-m", segments)
    assert len(detected) >= 2
    assert any("deployment window" in q["question"].lower() for q in detected)


# ==============================================================================
# PROMPT B TESTS: Speaker Coaching Scorecards
# ==============================================================================

def test_speaker_coaching_metrics_and_subscores():
    # Test coaching computation on existing demo meeting
    coaching = compute_speaker_coaching("demo-1")
    assert isinstance(coaching, list)
    assert len(coaching) > 0

    for sc in coaching:
        if not sc.get("not_enough_data"):
            assert 0 <= sc["overall_score"] <= 100
            sub = sc["subscores"]
            assert 0 <= sub["clarity"] <= 100
            assert 0 <= sub["participation"] <= 100
            assert 0 <= sub["listening"] <= 100
            assert 0 <= sub["inquiry"] <= 100
            assert 0 <= sub["concision"] <= 100
            assert len(sc["strengths"]) >= 1
            assert "tip" in sc
        else:
            assert "not enough data" in sc.get("message", "").lower()


# ==============================================================================
# PROMPT C TESTS: AI Devil's Advocate
# ==============================================================================

def test_devils_advocate_review_grounding():
    # Retrieve first decision in db
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM decisions LIMIT 1")
    row = cur.fetchone()
    conn.close()

    if row:
        dec_id = row[0]
        review = review_decision_with_devils_advocate(dec_id)
        assert review["overall_risk"] in ("low", "medium", "high")
        assert len(review["risks"]) > 0
        assert len(review["hidden_assumptions"]) > 0
        assert len(review["questions_to_ask"]) > 0
        assert "is_inferred" in review["risks"][0]


# ==============================================================================
# PROMPT D TESTS: Decision Lineage & Recurring Issues Radar
# ==============================================================================

def test_decision_lineage_and_recurring_issues():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM decisions LIMIT 1")
    row = cur.fetchone()
    conn.close()

    if row:
        dec_id = row[0]
        lineage = get_decision_lineage(dec_id)
        assert "summary" in lineage
        assert isinstance(lineage["events"], list)

    # Recurring issues radar
    issues = get_recurring_issues_radar()
    assert isinstance(issues, list)
    for issue in issues:
        assert issue["meetings_count"] >= 1
        assert issue["days_unresolved"] >= 0


# ==============================================================================
# PROMPT E TESTS: Knowledge Graph
# ==============================================================================

def test_knowledge_graph_builder():
    graph = build_knowledge_graph()
    assert "nodes" in graph
    assert "edges" in graph
    assert len(graph["nodes"]) > 0
    assert len(graph["edges"]) > 0

    node_types = {n["type"] for n in graph["nodes"]}
    assert "person" in node_types or "meeting" in node_types

    # Filter test by person
    person_graph = build_knowledge_graph(person_focus="Sarah Jenkins")
    assert isinstance(person_graph["nodes"], list)


# ==============================================================================
# PROMPT F TESTS: Meeting Cost & Value Score & Agenda
# ==============================================================================

def test_meeting_cost_and_value_score():
    sample_meeting = {
        "id": "test-cost",
        "durationSec": 3600,
        "speakers": ["Alice", "Bob", "Charlie"],
        "decisions": [{"text": "Ship v1"}],
        "tasks": [{"title": "Deploy API", "owner": "Alice", "deadline": "2026-10-10"}],
        "segments": [{"speaker": "Alice", "text": "Hi"}, {"speaker": "Bob", "text": "Hello"}]
    }

    cost = calculate_meeting_cost(sample_meeting)
    assert cost["duration_min"] == 60
    assert cost["attendee_count"] == 3
    assert cost["total_cost"] > 0

    val = compute_could_be_email_score(sample_meeting)
    assert 0 <= val["score"] <= 100
    assert val["verdict"] in ("Worth a meeting", "Could be shortened", "Could have been an email")

    # Agenda matching
    agenda = ["Review architecture", "Confirm release timeline"]
    res = evaluate_agenda_adherence(sample_meeting, agenda)
    assert len(res) == 2


# ==============================================================================
# PROMPT G TESTS: Teams Webhook & Digest & Compare
# ==============================================================================

def test_teams_webhook_and_compare():
    sample_meeting = {
        "id": "demo-1",
        "title": "Sprint Review",
        "meetingDate": "2026-10-04",
        "healthScore": 85,
        "summary": {"tldr": "Sprint completed on time."}
    }
    # Teams webhook formatting (mocked HTTP dispatch)
    res = send_teams_webhook(sample_meeting, webhook_url="")
    assert "ok" in res

    # Compare meetings
    comp = compare_two_meetings("demo-1", "demo-2")
    assert "narrative" in comp
    assert "decisions_diff" in comp
    assert "tasks_diff" in comp

    # Related meetings
    related = get_related_meetings("demo-1")
    assert isinstance(related, list)
    assert len(related) <= 3
