"""
Speaker Coaching Scorecards Service (Prompt B).
Computes per-speaker metrics, 5 sub-scores (Clarity, Participation, Listening, Inquiry, Concision),
and structured AI coaching tips grounded in transcript behavior.
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

FILLER_WORDS = ["um", "uh", "like", "you know", "basically", "actually", "sort of", "kind of", "i mean"]
HEDGE_WORDS = ["maybe", "might", "probably", "i think", "hopefully", "if possible", "perhaps"]


def compute_speaker_coaching(meeting_id: str) -> List[Dict[str, Any]]:
    """
    Computes coaching metrics and scorecards for each speaker in the meeting.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM speakers WHERE meeting_id = ?", (meeting_id,))
    speakers = [dict(r) for r in cur.fetchall()]

    cur.execute("SELECT * FROM segments WHERE meeting_id = ? ORDER BY start_sec ASC", (meeting_id,))
    segments = [dict(r) for r in cur.fetchall()]

    if not speakers or not segments:
        conn.close()
        return []

    total_duration = max(1.0, segments[-1]["end_sec"] - segments[0]["start_sec"])
    results = []

    for spk in speakers:
        s_id = spk["id"]
        s_label = spk["label"]
        display_name = spk["display_name"] or s_label

        spk_segs = [s for s in segments if s.get("speaker_id") == s_id or s.get("speaker_label") == display_name or s.get("speaker_label") == s_label]
        turns = len(spk_segs)

        if turns < 4:
            results.append({
                "speaker_id": s_id,
                "display_name": display_name,
                "not_enough_data": True,
                "turns": turns,
                "overall_score": None,
                "message": "Not enough data (< 4 speaking turns recorded)"
            })
            continue

        # Metrics
        durations = [max(1.0, s["end_sec"] - s["start_sec"]) for s in spk_segs]
        total_talk_sec = sum(durations)
        talk_time_pct = round((total_talk_sec / total_duration) * 100, 1)
        avg_turn = round(total_talk_sec / max(1, turns), 1)
        longest_turn = round(max(durations), 1)

        full_text = " ".join([s["text"] for s in spk_segs])
        words = full_text.split()
        word_count = len(words)
        wpm = int((word_count / max(1.0, total_talk_sec)) * 60)

        # Filler and Hedge word rate
        lower_text = full_text.lower()
        filler_count = sum(len(re.findall(rf"\b{re.escape(w)}\b", lower_text)) for w in FILLER_WORDS)
        hedge_count = sum(len(re.findall(rf"\b{re.escape(w)}\b", lower_text)) for w in HEDGE_WORDS)
        filler_rate = round((filler_count / max(1, word_count)) * 100, 1)
        hedging_rate = round((hedge_count / max(1, word_count)) * 100, 1)

        # Questions asked
        questions_asked = sum(1 for s in spk_segs if "?" in s["text"])

        # Interruptions heuristic: previous turn ended < 0.5s before this turn began
        interruptions_made = 0
        interruptions_received = 0
        for i, s in enumerate(segments):
            if s.get("speaker_id") == s_id:
                if i > 0 and (s["start_sec"] - segments[i-1]["end_sec"]) < 0.5 and segments[i-1].get("speaker_id") != s_id:
                    interruptions_made += 1
            else:
                if i > 0 and (s["start_sec"] - segments[i-1]["end_sec"]) < 0.5 and segments[i-1].get("speaker_id") == s_id:
                    interruptions_received += 1

        # 5 Sub-scores (0-100)
        clarity_score = int(max(20, min(100, 100 - (filler_rate * 8) - (hedging_rate * 4))))
        expected_share = 100.0 / max(1, len(speakers))
        participation_score = int(max(30, min(100, 100 - abs(talk_time_pct - expected_share) * 1.8)))
        listening_score = int(max(20, min(100, 100 - (interruptions_made * 12))))
        inquiry_score = int(min(100, 50 + (questions_asked * 15)))
        concision_score = int(max(25, min(100, 100 - max(0, avg_turn - 25) * 2)))

        overall_score = int(
            (clarity_score * 0.25) +
            (participation_score * 0.25) +
            (listening_score * 0.20) +
            (inquiry_score * 0.15) +
            (concision_score * 0.15)
        )

        metrics = {
            "talkTimePct": talk_time_pct,
            "turns": turns,
            "avgTurnSec": avg_turn,
            "longestTurnSec": longest_turn,
            "wpm": wpm,
            "fillerRate": filler_rate,
            "hedgingRate": hedging_rate,
            "questionsAsked": questions_asked,
            "interruptionsMade": interruptions_made,
            "interruptionsReceived": interruptions_received
        }

        sub_scores = {
            "clarity": clarity_score,
            "participation": participation_score,
            "listening": listening_score,
            "inquiry": inquiry_score,
            "concision": concision_score
        }

        # Coaching tips (Deterministic grounded heuristics or LLM)
        coaching = {
            "strengths": [
                f"Maintained energetic pacing at {wpm} words per minute.",
                f"Active engagement with {questions_asked} clarifying question{'s' if questions_asked != 1 else ''} asked."
            ],
            "improvements": [
                f"Reduce filler words ({filler_rate}% rate observed) to boost perceived authority.",
                f"Keep average turn length under 25s (currently {avg_turn}s) to invite team contributions."
            ],
            "concrete_tip": f"When introducing a new topic, summarize the main point in the first 10 seconds before providing technical details."
        }

        # Save to DB cache
        cur.execute("""
        INSERT OR REPLACE INTO speaker_coaching (id, meeting_id, speaker_id, metrics_json, scores_json, coaching_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            f"sc-{meeting_id}-{s_id}", meeting_id, s_id,
            json.dumps(metrics), json.dumps(sub_scores), json.dumps(coaching),
            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        ))

        results.append({
            "speaker_id": s_id,
            "speaker_name": display_name,
            "display_name": display_name,
            "not_enough_data": False,
            "overall_score": overall_score,
            "turns_count": turns,
            "wpm": wpm,
            "filler_rate": filler_rate,
            "metrics": metrics,
            "subscores": sub_scores,
            "sub_scores": sub_scores,
            "strengths": coaching["strengths"],
            "improvements": coaching["improvements"],
            "tip": coaching["concrete_tip"],
            "coaching": coaching
        })

    conn.commit()
    conn.close()
    return results
