"""
Versioned Prompt Store for Meeting Insights Studio.
Stores prompt text files in app/prompts/ as required by specification.
"""

from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "app" / "prompts"
PROMPTS_DIR.mkdir(parents=True, exist_ok=True)

PROMPT_TEMPLATES = {
    "commitment_strength_v1.txt": """You are an accountability analyst. For each action item, classify the commitment strength as:
- "firm": explicit commitment, clear owner and timeline (e.g. "I'll deliver this by Friday").
- "soft": hedged language or conditional promise (e.g. "maybe I can check", "hopefully by next sprint").
- "vague": no clear owner or no timeline.

Input tasks:
{tasks_json}

Return valid JSON with:
{
  "commitments": [
    {
      "task_id": "...",
      "strength": "firm|soft|vague",
      "reason": "1-sentence plain language rationale",
      "hedge_words": ["maybe", "if possible"]
    }
  ]
}
""",

    "unanswered_questions_v1.txt": """You are a meeting inquiry tracker. Analyze these questions asked during the meeting.
For each question, determine if it was answered in subsequent turns:
- "answered": a clear, direct answer was provided
- "partially_answered": partially addressed but key unknowns remain
- "unanswered": deflected, ignored, or left for future follow-up

Input questions and transcript:
{transcript_context}

Return valid JSON:
{
  "questions": [
    {
      "question_id": "...",
      "status": "answered|partially_answered|unanswered",
      "answer_quote": "exact quote answering the question",
      "answer_start_sec": 120
    }
  ]
}
""",

    "coaching_v1.txt": """You are an executive communication coach. Analyze observable speaking behavior for speaker {speaker_name}.
Computed metrics:
- Talk-time share: {talk_time_pct}%
- Speaking turns: {turns}
- Words per minute: {wpm}
- Filler-word rate: {filler_rate}%
- Hedging rate: {hedging_rate}%
- Interruptions made: {interruptions_made}, received: {interruptions_received}

Representative excerpts:
{excerpts}

Provide constructive, respectful coaching focusing strictly on observable behavior (never personality).
Return valid JSON:
{
  "strengths": ["Clear concise synthesis of complex architecture", "Encouraged dialogue by asking open questions"],
  "improvements": ["Reduce hedge words ('maybe', 'if possible') during final decisions", "Monitor turn duration when explaining updates"],
  "concrete_tip": "Pause for 2 seconds after asking a team question to encourage broader participation."
}
""",

    "devils_advocate_v1.txt": """You are an AI Devil's Advocate conducting a pre-mortem risk review of a formalized decision.
Decision: "{decision_text}"
Decided by: {decided_by}
Rationale: {rationale}
Transcript context:
{context}

Challenge this decision rigorously but realistically.
Every risk or hidden assumption must be supported by a transcript quote + timestamp, OR marked "inferred".
Missing stakeholders must only reference people mentioned in meeting history or generic team roles.

Return valid JSON:
{
  "overall_risk": "low|medium|high",
  "risks": [
    {"point": "...", "quote": "...", "start_sec": 120, "is_inferred": false}
  ],
  "hidden_assumptions": [
    {"point": "...", "quote": "...", "start_sec": 140, "is_inferred": false}
  ],
  "missing_stakeholders": ["Security Architect", "DevOps Team"],
  "alternatives_not_discussed": ["Retaining existing caching layer", "Third-party managed service"],
  "questions_to_ask": [
    "What is the rollback plan if customer latency increases?",
    "Has legal reviewed the data storage requirement?"
  ]
}
""",

    "lineage_v1.txt": """You are a cross-meeting decision lineage tracker.
Tracing topic: "{topic}"
Historical timeline items:
{items_json}

Classify each event as one of: "proposed", "discussed", "objection", "changed", "finalized", "reversed", "unrelated".
Discard unrelated items.

Return valid JSON:
{
  "summary": "Proposed on Sep 26, changed on Oct 4, finalized on Oct 11.",
  "events": [
    {
      "meeting_id": "...",
      "meeting_title": "...",
      "date": "YYYY-MM-DD",
      "speaker": "...",
      "type": "proposed|discussed|objection|changed|finalized|reversed",
      "quote": "verbatim quote",
      "start_sec": 100,
      "explanation": "..."
    }
  ]
}
""",

    "recurring_issues_v1.txt": """You are an organizational blocker analyst. Group the following cross-meeting issues into recurring themes:
Issues:
{issues_json}

Return valid JSON:
{
  "clusters": [
    {
      "theme": "Concise theme name (e.g. Caching Layer Instability)",
      "description": "2-sentence summary of the recurring blocker across meetings",
      "severity": "high|medium|low",
      "recommended_action": "..."
    }
  ]
}
""",

    "agenda_adherence_v1.txt": """Compare the planned agenda items against the actual transcript:
Planned Agenda:
{agenda_items}

Transcript:
{transcript_text}

Determine status for each agenda item: "covered", "partially_covered", or "skipped".
Include verbatim quotes where discussed.

Return valid JSON:
{
  "agenda_results": [
    {
      "item": "...",
      "status": "covered|partially_covered|skipped",
      "evidence_quote": "...",
      "start_sec": 45,
      "minutes_spent": 12
    }
  ],
  "off_agenda_topics": ["Discussion on team holiday schedule"]
}
""",

    "weekly_digest_v1.txt": """Generate an executive weekly digest synthesizing meetings from {start_date} to {end_date}:
Meeting Summaries:
{summaries_json}

Decisions & Tasks:
{decisions_tasks_json}

Return valid JSON:
{
  "executive_summary": "Top-level 3-sentence summary of the week",
  "key_accomplishments": ["...", "..."],
  "at_risk_commitments": ["...", "..."],
  "strategic_decisions": ["...", "..."],
  "upcoming_deadlines": ["...", "..."]
}
""",

    "compare_meetings_v1.txt": """Compare Meeting A ({title_a}) and Meeting B ({title_b}).
Analyze what is new, dropped, changed, or progressed across topics, decisions, and action items.

Meeting A:
{context_a}

Meeting B:
{context_b}

Return valid JSON:
{
  "narrative": "3-sentence narrative of evolution between Meeting A and Meeting B",
  "new_topics": ["..."],
  "dropped_items": ["..."],
  "modified_commitments": [
    {"item": "...", "change": "Deadline moved from Oct 10 to Oct 20", "type": "delay|scope_change"}
  ],
  "shared_themes": ["..."]
}
""",

    "live_summary_v1.txt": """You are generating an incremental running meeting summary.
Previous summary bullets:
{previous_summary}

New incoming transcribed speech:
{new_text}

Update the summary concisely (maximum 6 high-impact bullets total).
Return valid JSON:
{
  "current_topic": "Short active topic name",
  "summary_bullets": ["bullet 1", "bullet 2", "bullet 3"],
  "key_points": ["point 1", "point 2"]
}
"""
}


def ensure_prompts():
    for filename, content in PROMPT_TEMPLATES.items():
        p = PROMPTS_DIR / filename
        if not p.exists():
            p.write_text(content.strip(), encoding="utf-8")


ensure_prompts()
