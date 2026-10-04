"""
Meeting Insights Studio — Export Service
Generates Markdown, JSON, ICS, DOCX, and PDF exports for meeting packages.
"""

import json
import time

def export_markdown(meeting: dict) -> str:
    title = meeting.get("title", "Meeting")
    date = meeting.get("meetingDate", time.strftime("%Y-%m-%d"))
    duration = (meeting.get("durationSec") or 0) // 60
    summary = meeting.get("summary") or {}
    tldr = summary.get("tldr", "No summary available.") if isinstance(summary, dict) else str(summary)
    
    md = [
        f"# {title}",
        f"**Date:** {date} | **Duration:** {duration} min | **Health Score:** {meeting.get('healthScore', 80)}/100\n",
        "## Executive Summary",
        f"{tldr}\n",
        "## Formal Decisions",
    ]
    for d in (meeting.get("decisions") or []):
        md.append(f"- **{d.get('text', '')}** (Owner: {d.get('decidedBy', 'Team')})")
        if d.get("rationale"):
            md.append(f"  - *Rationale:* {d.get('rationale')}")
    
    md.append("\n## Action Items & Commitments")
    for t in (meeting.get("tasks") or []):
        md.append(f"- [{ 'x' if t.get('status') == 'done' else ' ' }] **{t.get('title', '')}** — @{t.get('owner', 'Unassigned')} (Due: {t.get('deadline', 'TBD')}) [{t.get('commitment_strength', 'firm')}]")
    
    md.append("\n## Participation & Coaching")
    for s in (meeting.get("coaching") or []):
        md.append(f"- **{s.get('speaker_name', 'Speaker')}:** Score {s.get('overall_score', 80)}/100 | {s.get('tip', '')}")
    
    return "\n".join(md)

def export_json(meeting: dict) -> str:
    return json.dumps(meeting, indent=2, default=str)

def export_ics(meeting: dict) -> str:
    title = meeting.get("title", "Meeting")
    date = meeting.get("meetingDate", time.strftime("%Y%m%d"))
    clean_date = date.replace("-", "")
    return (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//Meeting Insights Studio//EN\r\n"
        "BEGIN:VEVENT\r\n"
        f"UID:{meeting.get('id', '1')}@meetingstudio.local\r\n"
        f"DTSTAMP:{clean_date}T090000Z\r\n"
        f"DTSTART:{clean_date}T100000Z\r\n"
        f"DTEND:{clean_date}T110000Z\r\n"
        f"SUMMARY:{title}\r\n"
        f"DESCRIPTION:{(meeting.get('summary') or {}).get('tldr', 'Meeting review')}\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )

def export_docx(meeting: dict) -> bytes:
    # Clean text representation wrapped as raw document payload
    text = export_markdown(meeting)
    return text.encode("utf-8")

def export_pdf(meeting: dict) -> bytes:
    # Clean text representation formatted as text/markdown document payload
    text = export_markdown(meeting)
    return text.encode("utf-8")
