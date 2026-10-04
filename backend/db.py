"""
SQLite Database Layer for Meeting Insights Studio.
Handles schema creation, safe incremental migrations, and pre-computed demo seeding.
"""

import sqlite3
import json
import time
import os
from pathlib import Path
from typing import Optional

try:
    from config import Config
except ImportError:
    from backend.config import Config

DB_FILE = Config.BACKEND_DIR / "meeting_studio.db"


def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    target = Path(db_path) if db_path else DB_FILE
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Optional[str] = None):
    conn = get_db_connection(db_path)
    cur = conn.cursor()

    # 1. Meetings Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS meetings (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        meeting_date TEXT NOT NULL,
        source_filename TEXT,
        media_type TEXT DEFAULT 'audio',
        duration_sec REAL DEFAULT 0.0,
        language TEXT DEFAULT 'en',
        meeting_type TEXT DEFAULT 'general',
        status TEXT DEFAULT 'done',
        status_detail TEXT,
        progress_pct INTEGER DEFAULT 100,
        confidential_mode INTEGER DEFAULT 0,
        health_score INTEGER,
        health_breakdown_json TEXT,
        tags_json TEXT,
        agenda_text TEXT,
        meeting_cost REAL DEFAULT 0.0,
        meeting_value_score INTEGER DEFAULT 82,
        meeting_value_verdict TEXT DEFAULT 'Worth a meeting',
        meeting_cost_wasted REAL DEFAULT 0.0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 2. Speakers Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS speakers (
        id TEXT PRIMARY KEY,
        meeting_id TEXT NOT NULL,
        label TEXT NOT NULL,
        display_name TEXT NOT NULL,
        suggested_name TEXT,
        role TEXT,
        speaker_source TEXT DEFAULT 'model',
        color TEXT DEFAULT '#6366f1',
        hourly_rate REAL DEFAULT 1500.0,
        FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
    )
    """)

    # 3. Segments Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS segments (
        id TEXT PRIMARY KEY,
        meeting_id TEXT NOT NULL,
        idx INTEGER NOT NULL,
        speaker_id TEXT,
        speaker_label TEXT,
        start_sec REAL NOT NULL,
        end_sec REAL NOT NULL,
        text TEXT NOT NULL,
        sentiment TEXT DEFAULT 'neutral',
        embedding_json TEXT,
        FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
    )
    """)

    # 4. Summaries Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS summaries (
        meeting_id TEXT PRIMARY KEY,
        tldr TEXT NOT NULL,
        one_minute TEXT,
        detailed_json TEXT,
        topics_json TEXT,
        output_language TEXT DEFAULT 'en',
        FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
    )
    """)

    # 5. Decisions Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS decisions (
        id TEXT PRIMARY KEY,
        meeting_id TEXT NOT NULL,
        text TEXT NOT NULL,
        decided_by TEXT,
        rationale TEXT,
        quote TEXT,
        start_sec REAL DEFAULT 0.0,
        verified INTEGER DEFAULT 1,
        confidence REAL DEFAULT 0.95,
        FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
    )
    """)

    # 6. Tasks Table (with Commitment Strength columns)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY,
        meeting_id TEXT NOT NULL,
        title TEXT NOT NULL,
        owner TEXT,
        deadline TEXT,
        deadline_raw TEXT,
        deadline_ambiguous INTEGER DEFAULT 0,
        priority TEXT DEFAULT 'medium',
        status TEXT DEFAULT 'todo',
        quote TEXT,
        start_sec REAL DEFAULT 0.0,
        verified INTEGER DEFAULT 1,
        confidence REAL DEFAULT 0.9,
        commitment_strength TEXT DEFAULT 'firm',
        commitment_reason TEXT DEFAULT 'Clear owner and deadline assigned',
        hedge_words_json TEXT DEFAULT '[]',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
    )
    """)

    # 7. Insights Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS insights (
        id TEXT PRIMARY KEY,
        meeting_id TEXT NOT NULL,
        kind TEXT DEFAULT 'insight',
        text TEXT NOT NULL,
        quote TEXT,
        start_sec REAL DEFAULT 0.0,
        confidence REAL DEFAULT 0.9,
        FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
    )
    """)

    # 8. Conflicts Table (Cross-Meeting Tracker)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS conflicts (
        id TEXT PRIMARY KEY,
        meeting_id TEXT NOT NULL,
        other_meeting_id TEXT NOT NULL,
        kind TEXT NOT NULL,
        description TEXT NOT NULL,
        evidence_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        dismissed INTEGER DEFAULT 0,
        FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
    )
    """)

    # 9. Questions Table (Unanswered Questions Tracker - Prompt A)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id TEXT PRIMARY KEY,
        meeting_id TEXT NOT NULL,
        asker_speaker_id TEXT,
        question TEXT NOT NULL,
        start_sec REAL DEFAULT 0.0,
        status TEXT DEFAULT 'unanswered',
        answer_quote TEXT,
        answer_start_sec REAL,
        carried_from_meeting_id TEXT,
        resolved INTEGER DEFAULT 0,
        FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
    )
    """)

    # 10. Speaker Coaching Scorecards (Prompt B)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS speaker_coaching (
        id TEXT PRIMARY KEY,
        meeting_id TEXT NOT NULL,
        speaker_id TEXT NOT NULL,
        metrics_json TEXT NOT NULL,
        scores_json TEXT NOT NULL,
        coaching_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
    )
    """)

    # 11. Decision Reviews Table (Devil's Advocate - Prompt C)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS decision_reviews (
        id TEXT PRIMARY KEY,
        decision_id TEXT NOT NULL,
        review_json TEXT NOT NULL,
        overall_risk TEXT DEFAULT 'medium',
        created_at TEXT NOT NULL,
        FOREIGN KEY (decision_id) REFERENCES decisions(id) ON DELETE CASCADE
    )
    """)

    # 12. Decision Lineage Table (Prompt D)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS decision_lineage (
        id TEXT PRIMARY KEY,
        decision_id TEXT NOT NULL,
        events_json TEXT NOT NULL,
        summary TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (decision_id) REFERENCES decisions(id) ON DELETE CASCADE
    )
    """)

    # 13. Agenda Results Table (Prompt F)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS agenda_results (
        id TEXT PRIMARY KEY,
        meeting_id TEXT NOT NULL,
        item TEXT NOT NULL,
        status TEXT DEFAULT 'covered',
        evidence_quote TEXT,
        start_sec REAL DEFAULT 0.0,
        minutes REAL DEFAULT 0.0,
        FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
    )
    """)

    # 14. Live Sessions & Chunks Tables (Prompt I)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS live_sessions (
        id TEXT PRIMARY KEY,
        meeting_id TEXT,
        title TEXT NOT NULL,
        started_at TEXT NOT NULL,
        ended_at TEXT,
        status TEXT DEFAULT 'active',
        language TEXT DEFAULT 'en',
        confidential_mode INTEGER DEFAULT 0,
        chunk_count INTEGER DEFAULT 0,
        audio_path TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS live_chunks (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        seq INTEGER NOT NULL,
        start_sec REAL DEFAULT 0.0,
        end_sec REAL DEFAULT 0.0,
        transcript_json TEXT,
        status TEXT DEFAULT 'transcribed',
        error TEXT,
        FOREIGN KEY (session_id) REFERENCES live_sessions(id) ON DELETE CASCADE
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS live_items (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        kind TEXT DEFAULT 'task',
        title TEXT NOT NULL,
        owner TEXT,
        deadline_raw TEXT,
        quote TEXT,
        timestamp_sec REAL DEFAULT 0.0,
        status TEXT DEFAULT 'tentative',
        FOREIGN KEY (session_id) REFERENCES live_sessions(id) ON DELETE CASCADE
    )
    """)

    # 15. Settings & LLM Calls Tables
    cur.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """)

    # 16. Chat Messages Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS chat_messages (
        id TEXT PRIMARY KEY,
        meeting_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        citations_json TEXT DEFAULT '[]',
        created_at TEXT NOT NULL,
        FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS llm_calls (
        id TEXT PRIMARY KEY,
        meeting_id TEXT,
        task TEXT,
        model TEXT,
        deployment TEXT,
        tokens_in INTEGER DEFAULT 0,
        tokens_out INTEGER DEFAULT 0,
        cost_usd REAL DEFAULT 0.0,
        latency_ms INTEGER DEFAULT 0,
        cached INTEGER DEFAULT 0,
        created_at TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS activities (
        id TEXT PRIMARY KEY,
        event_type TEXT NOT NULL,
        description TEXT NOT NULL,
        meeting_id TEXT,
        created_at TEXT NOT NULL
    )
    """)

    # SAFE INCREMENTAL MIGRATIONS (Check existing tables & add columns if missing)
    def add_col_if_missing(table, col, col_def):
        cur.execute(f"PRAGMA table_info({table})")
        existing_cols = [c[1] for c in cur.fetchall()]
        if col not in existing_cols:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_def}")

    add_col_if_missing("tasks", "commitment_strength", "TEXT DEFAULT 'firm'")
    add_col_if_missing("tasks", "commitment_reason", "TEXT DEFAULT 'Clear commitment'")
    add_col_if_missing("tasks", "hedge_words_json", "TEXT DEFAULT '[]'")
    add_col_if_missing("meetings", "agenda_text", "TEXT")
    add_col_if_missing("meetings", "meeting_cost", "REAL DEFAULT 0.0")
    add_col_if_missing("meetings", "meeting_value_score", "INTEGER DEFAULT 82")
    add_col_if_missing("meetings", "meeting_value_verdict", "TEXT DEFAULT 'Worth a meeting'")
    add_col_if_missing("meetings", "meeting_cost_wasted", "REAL DEFAULT 0.0")

    conn.commit()

    # Seed sample data if empty
    cur.execute("SELECT COUNT(*) FROM meetings")
    if cur.fetchone()[0] == 0:
        seed_initial_data(conn)

    conn.close()


def seed_initial_data(conn: sqlite3.Connection):
    """Populates database with rich pre-processed meetings and initial LLM calls."""
    try:
        from sample_data import get_initial_meetings, get_initial_llm_calls
    except ImportError:
        from backend.sample_data import get_initial_meetings, get_initial_llm_calls

    cur = conn.cursor()
    meetings = get_initial_meetings()

    for m in meetings:
        cur.execute("""
        INSERT OR REPLACE INTO meetings (
            id, title, meeting_date, source_filename, media_type, duration_sec,
            language, meeting_type, status, status_detail, progress_pct,
            confidential_mode, health_score, health_breakdown_json, tags_json,
            agenda_text, meeting_cost, meeting_value_score, meeting_value_verdict, meeting_cost_wasted,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            m["id"], m["title"], m["meetingDate"], m.get("sourceFilename", ""),
            m.get("mediaType", "audio"), m.get("durationSec", 0.0),
            m.get("language", "en"), m.get("meetingType", "planning"),
            m.get("status", "done"), m.get("statusDetail", "Processing complete"),
            m.get("progressPct", 100), 1 if m.get("confidentialMode") else 0,
            m.get("healthScore", 82),
            json.dumps(m.get("analytics", {}).get("healthBreakdown", [])),
            json.dumps(m.get("tags", [])),
            "1. Review sprint progress\n2. QA findings and bug triage\n3. Q3 platform roadmap decision",
            10500.0, 85, "Worth a meeting", 0.0,
            m.get("createdAt", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
            m.get("updatedAt", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        ))

        for spk in m.get("speakers", []):
            cur.execute("""
            INSERT OR REPLACE INTO speakers (id, meeting_id, label, display_name, suggested_name, role, speaker_source, color, hourly_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                spk["id"], m["id"], spk.get("label", ""), spk.get("displayName", ""),
                spk.get("suggestedName"), spk.get("role", ""), spk.get("speakerSource", "model"),
                spk.get("color", "#6366f1"), 1500.0
            ))

        for s in m.get("segments", []):
            cur.execute("""
            INSERT OR REPLACE INTO segments (id, meeting_id, idx, speaker_id, speaker_label, start_sec, end_sec, text, sentiment, embedding_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                s["id"], m["id"], s.get("idx", 0), s.get("speakerId"), s.get("speakerLabel"),
                s.get("startSec", 0.0), s.get("endSec", 0.0), s.get("text", ""),
                s.get("sentiment", "neutral"), json.dumps(s.get("embedding")) if s.get("embedding") else None
            ))

        summ = m.get("summary")
        if summ:
            cur.execute("""
            INSERT OR REPLACE INTO summaries (meeting_id, tldr, one_minute, detailed_json, topics_json, output_language)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                m["id"], summ.get("tldr", ""), summ.get("oneMinute", ""),
                json.dumps(summ.get("detailed", [])), json.dumps(summ.get("topics", [])),
                summ.get("outputLanguage", "en")
            ))

        for d in m.get("decisions", []):
            cur.execute("""
            INSERT OR REPLACE INTO decisions (id, meeting_id, text, decided_by, rationale, quote, start_sec, verified, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                d["id"], m["id"], d["text"], d.get("decidedBy", ""), d.get("rationale", ""),
                d.get("quote", ""), d.get("startSec", 0.0), 1 if d.get("verified", True) else 0,
                d.get("confidence", 0.95)
            ))

        for t in m.get("tasks", []):
            cur.execute("""
            INSERT OR REPLACE INTO tasks (
                id, meeting_id, title, owner, deadline, deadline_raw, deadline_ambiguous,
                priority, status, quote, start_sec, verified, confidence,
                commitment_strength, commitment_reason, hedge_words_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                t["id"], m["id"], t["title"], t.get("owner", "Team"), t.get("deadline"),
                t.get("deadlineRaw", ""), 1 if t.get("deadlineAmbiguous") else 0,
                t.get("priority", "medium"), t.get("status", "todo"), t.get("quote", ""),
                t.get("startSec", 0.0), 1 if t.get("verified", True) else 0,
                t.get("confidence", 0.9),
                t.get("commitmentStrength", "firm"),
                t.get("commitmentReason", "Clear promise with defined timing"),
                json.dumps(t.get("hedgeWords", [])),
                t.get("createdAt", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
                t.get("updatedAt", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
            ))

        for ins in m.get("insights", []):
            cur.execute("""
            INSERT OR REPLACE INTO insights (id, meeting_id, kind, text, quote, start_sec, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                ins["id"], m["id"], ins.get("kind", "insight"), ins["text"],
                ins.get("quote", ""), ins.get("startSec", 0.0), ins.get("confidence", 0.9)
            ))

    # Seed Sample Questions (Prompt A)
    cur.execute("""
    INSERT OR REPLACE INTO questions (id, meeting_id, asker_speaker_id, question, start_sec, status, answer_quote, answer_start_sec, carried_from_meeting_id, resolved)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "q-1", "demo-1", "s1", "Raj, can you walk us through the engineering updates?", 0.0,
        "answered", "Sure. So this sprint we completed the authentication refactor and the new API endpoints.", 12.0, None, 1
    ))
    cur.execute("""
    INSERT OR REPLACE INTO questions (id, meeting_id, asker_speaker_id, question, start_sec, status, answer_quote, answer_start_sec, carried_from_meeting_id, resolved)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "q-2", "demo-1", "s4", "What are the infrastructure requirements for the test sandbox?", 305.0,
        "unanswered", None, None, None, 0
    ))
    cur.execute("""
    INSERT OR REPLACE INTO questions (id, meeting_id, asker_speaker_id, question, start_sec, status, answer_quote, answer_start_sec, carried_from_meeting_id, resolved)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "q-3", "demo-2", "s2b", "Can we integrate directly with Salesforce custom enterprise objects?", 35.0,
        "partially_answered", "The analytics platform handles real-time CRM data integration.", 55.0, None, 0
    ))

    # Seed Sample Devil's Advocate Review (Prompt C)
    cur.execute("""
    INSERT OR REPLACE INTO decision_reviews (id, decision_id, review_json, overall_risk, created_at)
    VALUES (?, ?, ?, ?, ?)
    """, (
        "rev-d1", "d1",
        json.dumps({
            "overall_risk": "medium",
            "risks": [
                {"point": "Deferring the mobile app to Q4 risks customer churn if competitors launch mobile-first analytics.", "quote": "The mobile app can wait until Q4", "start_sec": 178, "is_inferred": False},
                {"point": "Underestimating integration complexity with legacy CRM systems may delay Q3 delivery.", "quote": "we already have the infrastructure from the dashboard work", "start_sec": 178, "is_inferred": False}
            ],
            "hidden_assumptions": [
                {"point": "Assumes existing Redis and backend APIs will scale linearly without database bottleneck.", "quote": "completed the authentication refactor and new API endpoints", "start_sec": 12, "is_inferred": False}
            ],
            "missing_stakeholders": ["Mobile Platform Architect", "Customer Support Lead"],
            "alternatives_not_discussed": ["Dual-track hybrid mobile prototype", "Outsourced mobile frontend wrapper"],
            "questions_to_ask": [
                "What is the SLA threshold if real-time ingestion latency exceeds 500ms?",
                "Do we have client confirmation that desktop web access satisfies their mobile workforce?"
            ]
        }),
        "medium",
        time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    ))

    # Seed Sample Decision Lineage (Prompt D)
    cur.execute("""
    INSERT OR REPLACE INTO decision_lineage (id, decision_id, events_json, summary, created_at)
    VALUES (?, ?, ?, ?, ?)
    """, (
        "lin-d1", "d1",
        json.dumps([
            {
                "meeting_id": "demo-2",
                "meeting_title": "Client Kickoff Call — Acme Corp",
                "date": "2026-09-26",
                "speaker": "Alex Rivera",
                "type": "proposed",
                "quote": "The main goal is to get a custom analytics dashboard built that integrates with our Salesforce CRM.",
                "start_sec": 20,
                "explanation": "Client initially requested dedicated Salesforce analytics capabilities."
            },
            {
                "meeting_id": "demo-1",
                "meeting_title": "Sprint Review & Q3 Planning",
                "date": "2026-10-04",
                "speaker": "Raj Patel",
                "type": "discussed",
                "quote": "I strongly recommend we prioritize the analytics platform. The client has been asking for it since Q1.",
                "start_sec": 178,
                "explanation": "Engineering advocated for analytics platform over mobile exploration."
            },
            {
                "meeting_id": "demo-1",
                "meeting_title": "Sprint Review & Q3 Planning",
                "date": "2026-10-04",
                "speaker": "Priya Sharma",
                "type": "finalized",
                "quote": "let's go with the analytics platform for Q3 then. That's decided.",
                "start_sec": 228,
                "explanation": "Decision formalized to prioritize analytics for Q3."
            }
        ]),
        "Proposed on Sep 26 (Acme Kickoff), evaluated on Oct 4, and finalized for Q3 release.",
        time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    ))

    # Seed Sample Conflict (Prompt 5)
    cur.execute("""
    INSERT OR REPLACE INTO conflicts (id, meeting_id, other_meeting_id, kind, description, evidence_json, created_at, dismissed)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "conf-1", "demo-1", "demo-2", "commitment",
        "Commitment unfulfilled: In Client Kickoff Call (Sep 26), David promised analytics mockups by Oct 1. In Sprint Review (Oct 4), Sarah stated base components will only be ready by Oct 20.",
        json.dumps([
            {"meeting": "Client Kickoff Call — Acme Corp", "meetingId": "demo-2", "quote": "David will prepare analytics mockups for the client review by October 1st", "timeSec": 260, "date": "2026-09-26"},
            {"meeting": "Sprint Review & Q3 Planning", "meetingId": "demo-1", "quote": "I'll have the base components ready by the 20th", "timeSec": 268, "date": "2026-10-04"}
        ]),
        time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        0
    ))

    # Seed Sample Agenda Results (Prompt F)
    agenda_sample = [
        ("ag-1", "demo-1", "Engineering and sprint velocity update", "covered", "Velocity was 42 points, up from 38 last sprint.", 12.0, 7.0),
        ("ag-2", "demo-1", "QA race condition review", "covered", "I found three medium-priority issues in the new API endpoints.", 98.0, 6.0),
        ("ag-3", "demo-1", "Q3 roadmap priority decision", "covered", "let's go with the analytics platform for Q3 then. That's decided.", 228.0, 8.0),
        ("ag-4", "demo-1", "Budget review for external cloud licenses", "skipped", None, 0.0, 0.0)
    ]
    for ag in agenda_sample:
        cur.execute("""
        INSERT OR REPLACE INTO agenda_results (id, meeting_id, item, status, evidence_quote, start_sec, minutes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ag)

    # Seed Settings Default Values (Prompt F & G)
    cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('hourly_rate', '1500')")
    cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('currency', 'INR')")
    cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('teams_webhook_url', '')")

    # Seed Activities Log
    cur.execute("""
    INSERT INTO activities (id, event_type, description, meeting_id, created_at)
    VALUES ('act-1', 'meeting_processed', 'Processed Sprint Review & Q3 Planning', 'demo-1', ?)
    """, (time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),))
    cur.execute("""
    INSERT INTO activities (id, event_type, description, meeting_id, created_at)
    VALUES ('act-2', 'conflict_found', 'Cross-meeting commitment contradiction detected', 'demo-1', ?)
    """, (time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),))

    conn.commit()


# Initialize database schema on module load
init_db()
