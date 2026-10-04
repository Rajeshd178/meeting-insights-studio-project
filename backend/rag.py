"""
RAG (Retrieval-Augmented Generation) & Safety engine for Meeting Studio.
Powered by:
  - Vector retrieval via `text-embedding-3-small`
  - Grounded answer synthesis via `gpt-4.1-mini`
"""

import re
from typing import List, Dict, Any, Tuple
try:
    from ai_service import get_embedding, get_embeddings_batch, cosine_similarity, answer_query_with_llm
except ImportError:
    from backend.ai_service import get_embedding, get_embeddings_batch, cosine_similarity, answer_query_with_llm


INJECTION_PATTERNS = [
    re.compile(r"\bignore (all )?(previous|above|prior) instructions\b", re.I),
    re.compile(r"\bdisregard (the )?(system|above|previous) prompt\b", re.I),
    re.compile(r"\byou are now\b", re.I),
    re.compile(r"\bforget (everything|all|your instructions)\b", re.I),
    re.compile(r"\bnew (role|instructions?|directive)\b", re.I),
]

def detect_injection(text: str) -> bool:
    """Checks if the user prompt contains jailbreak or injection patterns."""
    return any(p.search(text) for p in INJECTION_PATTERNS)

def redact_pii(text: str) -> str:
    """Redacts emails, phone numbers, and credit cards from transcripts."""
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "[EMAIL]", text)
    text = re.sub(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "[PHONE]", text)
    text = re.sub(r"\b\d{12,19}\b", "[ID]", text)
    text = re.sub(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b", "[CARD]", text)
    return text

def format_ts(sec: float) -> str:
    m = int(sec // 60)
    s = int(sec % 60)
    return f"{m}:{s:02d}"

def retrieve_chunks(query: str, segments: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
    """
    RAG vector search over segments using text-embedding-3-small embeddings.
    Batches missing segment embeddings in a single call.
    """
    if not segments:
        return []

    # Check for missing embeddings and batch them
    missing_idx = [i for i, s in enumerate(segments) if not s.get("embedding")]
    if missing_idx:
        texts_to_embed = [segments[i].get("text", "") for i in missing_idx]
        batch_vecs = get_embeddings_batch(texts_to_embed)
        for i, vec in zip(missing_idx, batch_vecs):
            segments[i]["embedding"] = vec

    q_vec = get_embedding(query)
    scored = []
    for s in segments:
        seg_vec = s.get("embedding")
        if not seg_vec:
            continue
        score = cosine_similarity(q_vec, seg_vec)
        scored.append((score, s))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [s for score, s in scored[:top_k]]


def search_keyword(query: str, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    q = query.lower()
    return [s for s in segments if q in s.get("text", "").lower()]

def generate_answer(query: str, meeting: Dict[str, Any]) -> Dict[str, Any]:
    """
    Answers questions about a single meeting using RAG retrieval + LLM synthesis.
    """
    if detect_injection(query):
        return {
            "content": "Potential prompt injection detected. Your query cannot be processed under our safety guidelines.",
            "citations": []
        }

    q = query.lower()
    segments = meeting.get("segments", [])
    retrieved = retrieve_chunks(query, segments, top_k=5)

    citations = [
        {
            "speaker": s.get("speakerLabel", "Speaker"),
            "timeSec": s.get("startSec", 0),
            "text": s.get("text", "")[:120] + ("..." if len(s.get("text", "")) > 120 else "")
        }
        for s in retrieved[:3]
    ]

    # Pre-checks for common structural meeting queries
    if "decision" in q or "decide" in q:
        decisions = meeting.get("decisions", [])
        if decisions:
            items = "\n".join([f"• {d['text']} — decided by {d.get('decidedBy', 'Team')}{' (Verified by AI Critic)' if d.get('verified') else ''}" for d in decisions])
            return {
                "content": f"Based on the transcript, {len(decisions)} decision{'s were' if len(decisions) > 1 else ' was'} made in this meeting:\n\n{items}",
                "citations": citations
            }

    if "action" in q or "task" in q or "todo" in q:
        tasks = meeting.get("tasks", [])
        if tasks:
            items = "\n".join([f"• {t['title']} — Owner: {t.get('owner', 'Unassigned')}, Deadline: {t.get('deadline') or 'not set'}, Priority: {t.get('priority', 'medium')}" for t in tasks])
            return {
                "content": f"There are {len(tasks)} action items identified from this meeting:\n\n{items}",
                "citations": citations
            }

    if "risk" in q or "blocker" in q or "concern" in q:
        insights = [i for i in meeting.get("insights", []) if i.get("kind") in ("risk", "blocker")]
        if insights:
            items = "\n".join([f"• {i['text']}" for i in insights])
            return {
                "content": f"The following risks and blockers were identified during the meeting:\n\n{items}",
                "citations": citations
            }

    if "summary" in q or "tl;dr" in q or "overview" in q:
        summary = meeting.get("summary")
        if summary and summary.get("tldr"):
            return {
                "content": summary["tldr"],
                "citations": citations
            }

    # Call gpt-4.1-mini to synthesize answer from retrieved context
    ans = answer_query_with_llm(query, retrieved, meeting.get("title", "Meeting"))
    return {
        "content": ans,
        "citations": citations
    }

def generate_answer_all_meetings(query: str, meetings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    RAG search and answer synthesis across all stored meetings.
    """
    if detect_injection(query):
        return {
            "content": "Potential prompt injection detected. Your query cannot be processed under our safety guidelines.",
            "citations": []
        }

    q = query.lower()
    meeting_results = []

    for m in meetings:
        if m.get("status") != "done" or not m.get("segments"):
            continue
        retrieved = retrieve_chunks(query, m.get("segments", []), top_k=2)
        if retrieved:
            meeting_results.append({"meeting": m, "segments": retrieved})

    if not meeting_results:
        return {
            "content": "I couldn't find relevant information across any recorded meetings for your query. Try asking about a specific decision, project milestone, or action item.",
            "citations": []
        }

    if "action" in q or "task" in q or "overdue" in q:
        all_tasks = [t for m in meetings if m.get("status") == "done" for t in m.get("tasks", [])]
        open_tasks = [t for t in all_tasks if t.get("status") != "done"]
        items = "\n".join([f"• {t.get('title')} — Owner: {t.get('owner', 'Team')}, Deadline: {t.get('deadline') or 'N/A'}, Status: {t.get('status')}" for t in open_tasks[:8]])
        return {
            "content": f"Across all meetings, there are {len(open_tasks)} open action items:\n\n{items}",
            "citations": []
        }

    if "decision" in q:
        all_decisions = [
            f"• [{m.get('title')}] {d.get('text')} — by {d.get('decidedBy', 'Team')}"
            for m in meetings if m.get("status") == "done"
            for d in m.get("decisions", [])
        ]
        return {
            "content": f"Across all meetings, {len(all_decisions)} decisions were formalized:\n\n" + "\n".join(all_decisions),
            "citations": []
        }

    # Cross meeting summary
    top_meetings = meeting_results[:3]
    parts = []
    all_citations = []
    for r in top_meetings:
        m = r["meeting"]
        m_title = m.get("title", "Meeting")
        segs = r["segments"]
        seg_lines = "\n".join([f"  • {s.get('speakerLabel')} at {format_ts(s.get('startSec', 0))}: \"{s.get('text', '')[:110]}...\"" for s in segs])
        parts.append(f"In \"{m_title}\":\n{seg_lines}")
        for s in segs:
            all_citations.append({
                "speaker": s.get("speakerLabel"),
                "timeSec": s.get("startSec"),
                "text": s.get("text", "")[:100],
                "meetingTitle": m_title
            })

    content = f"I identified relevant discussion across {len(top_meetings)} meeting{'s' if len(top_meetings) > 1 else ''}:\n\n" + "\n\n".join(parts)
    return {
        "content": content,
        "citations": all_citations
    }
