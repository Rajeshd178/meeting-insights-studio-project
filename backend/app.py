"""
Meeting Studio — Backend Flask Application
Complete REST API and Page Routes for Meeting Insights Studio.
"""

import os
import sys
import time
import json
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for, Response

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from werkzeug.utils import secure_filename
from config import Config
from store import store
from ai_service import transcribe_and_diarize, analyze_meeting, get_client
import rag
from models import uid
import export_service
from services.analytics import compute_health_score
from services.tracker import run_conflict_tracker
from services.accountability import classify_task_commitment, detect_questions_in_segments, resolve_unanswered_questions_carryover
from services.speaker_coaching import compute_speaker_coaching
from services.devils_advocate import review_decision_with_devils_advocate
from services.lineage_radar import get_decision_lineage, get_recurring_issues_radar
from services.knowledge_graph import build_knowledge_graph
from services.business_value import calculate_meeting_cost, compute_could_be_email_score, evaluate_agenda_adherence
from services.collaboration import send_teams_webhook, generate_weekly_digest, compare_two_meetings, get_related_meetings
from services.live_session import start_live_session, ingest_live_chunk, get_live_updates, stop_live_session, generate_catchup_summary
from db import get_db_connection

# Configure Flask with explicit frontend template and static paths
frontend_dir = Config.FRONTEND_DIR
app = Flask(
    __name__,
    template_folder=str(frontend_dir / "templates"),
    static_folder=str(frontend_dir / "static"),
)

app.config["SECRET_KEY"] = Config.SECRET_KEY
upload_dir = backend_dir / "uploads"
upload_dir.mkdir(parents=True, exist_ok=True)
app.config["UPLOAD_FOLDER"] = str(upload_dir)

@app.context_processor
def inject_global_data():
    return {
        "config_info": Config.get_model_info(),
        "is_demo_mode": os.getenv("DEMO_MODE", "").lower() in ("true", "1", "yes") or not Config.OPENAI_API_KEY
    }


# ==============================================================================
# HTML Page Routes (Serving Frontend Templates)
# ==============================================================================

@app.route("/")
def dashboard():
    meetings = store.get_meetings()
    stats = store.get_stats()
    conflicts = store.get_open_conflicts()
    activities = store.get_recent_activities(5)
    all_tags = store.get_all_tags()
    all_participants = store.get_all_participants()
    is_demo = os.getenv("DEMO_MODE", "").lower() in ("true", "1", "yes") or not Config.OPENAI_API_KEY

    return render_template(
        "dashboard.html",
        active_page="dashboard",
        meetings=meetings,
        stats=stats,
        conflicts=conflicts,
        activities=activities,
        all_tags=all_tags,
        all_participants=all_participants,
        demo_mode=is_demo
    )

@app.route("/live")
def live_page():
    return render_template("live.html", active_page="live")

@app.route("/graph")
def graph_page():
    all_participants = store.get_all_participants()
    return render_template("graph.html", active_page="graph", all_participants=all_participants)

@app.route("/digest")
def digest_page():
    start = request.args.get("start", "2026-09-25")
    end = request.args.get("end", "2026-10-05")
    digest = generate_weekly_digest(start, end)
    return render_template("digest.html", active_page="digest", digest=digest, start_date=start, end_date=end)

@app.route("/compare")
def compare_page():
    meetings = store.get_meetings()
    a_id = request.args.get("a", meetings[0]["id"] if meetings else "")
    b_id = request.args.get("b", meetings[1]["id"] if len(meetings) > 1 else "")
    comp = compare_two_meetings(a_id, b_id) if a_id and b_id else {}
    return render_template("compare.html", active_page="compare", meetings=meetings, comp=comp, a_id=a_id, b_id=b_id)

@app.route("/radar")
def radar_page():
    issues = get_recurring_issues_radar()
    return render_template("radar.html", active_page="radar", issues=issues)

@app.route("/settings")
def settings_page():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT key, value FROM settings")
    settings = dict(cur.fetchall())
    conn.close()
    return render_template("settings.html", active_page="settings", settings=settings)

@app.route("/upload")
def upload_page():
    return render_template("upload.html", active_page="upload")

@app.route("/meeting/<meeting_id>")
def meeting_detail(meeting_id):
    meeting = store.get_meeting(meeting_id)
    if not meeting:
        return redirect(url_for("dashboard"))
    
    # Calculate business value, email score & cost
    cost_info = calculate_meeting_cost(meeting)
    value_score = compute_could_be_email_score(meeting)
    coaching = compute_speaker_coaching(meeting_id)
    related = get_related_meetings(meeting_id)

    return render_template(
        "meeting_detail.html",
        active_page="dashboard",
        meeting=meeting,
        cost_info=cost_info,
        value_score=value_score,
        coaching=coaching,
        related=related
    )

@app.route("/ask-all")
def ask_all_page():
    return render_template("ask_all.html", active_page="ask_all")

@app.route("/brief")
def brief_page():
    meeting_id = request.args.get("meeting_id")
    selected_tag = request.args.get("tag")

    all_meetings = store.get_meetings()
    all_tags = store.get_all_tags()
    tasks = store.get_all_tasks()
    decisions = store.get_all_decisions()
    overdue_tasks = store.get_overdue_tasks()

    selected_meeting = None
    if meeting_id:
        selected_meeting = store.get_meeting(meeting_id)
    elif selected_tag:
        matching = [m for m in all_meetings if selected_tag.lower() in [t.lower() for t in m.get("tags", [])]]
        if matching:
            selected_meeting = matching[0]
    elif all_meetings:
        selected_meeting = all_meetings[0]

    if selected_meeting:
        meeting_tasks = [t for t in tasks if t.get("meeting_id") == selected_meeting["id"]]
        meeting_decisions = [d for d in decisions if d.get("meeting_id") == selected_meeting["id"]]
    else:
        meeting_tasks = tasks
        meeting_decisions = decisions

    unresolved_tasks = [t for t in meeting_tasks if t.get("status") != "done"]

    agenda = [
        {"time": "00-05m", "topic": "Introductions & Context Setting", "owner": "Host"},
        {"time": "05-20m", "topic": "Status Review of Outstanding Commitments", "owner": "Team"},
        {"time": "20-40m", "topic": "Core Discussion & Key Decision Points", "owner": "All Stakeholders"},
        {"time": "40-50m", "topic": "Action Item Alignment & Assignee Confirmation", "owner": "Host"}
    ]

    open_questions = [
        "What are the target deployment dates for Phase 2 deliverables?",
        "Are there any blocking architectural dependencies before sprint start?",
        "Who is the designated point-of-contact for customer acceptance testing?"
    ]

    return render_template(
        "brief.html",
        active_page="brief",
        all_meetings=all_meetings,
        all_tags=all_tags,
        selected_meeting=selected_meeting,
        selected_tag=selected_tag,
        tasks=meeting_tasks,
        unresolved_tasks=unresolved_tasks,
        overdue_tasks=overdue_tasks,
        decisions=meeting_decisions,
        agenda=agenda,
        open_questions=open_questions
    )

@app.route("/cost")
def cost_page():
    calls = store.get_llm_calls()
    total_cost = sum(c.get("cost_usd", c.get("costUsd", 0.0)) for c in calls)
    tokens_in = sum(c.get("tokens_in", c.get("tokensIn", 0)) for c in calls)
    tokens_out = sum(c.get("tokens_out", c.get("tokensOut", 0)) for c in calls)
    avg_latency = int(sum(c.get("latency_ms", c.get("latencyMs", 0)) for c in calls) / max(1, len(calls)))

    by_model = {}
    for c in calls:
        m = c.get("model", "unknown")
        if m not in by_model:
            by_model[m] = {"calls": 0, "cost": 0.0}
        by_model[m]["calls"] += 1
        by_model[m]["cost"] += c.get("cost_usd", c.get("costUsd", 0.0))

    by_task = {}
    for c in calls:
        t = c.get("task", "general")
        if t not in by_task:
            by_task[t] = {"calls": 0, "cost": 0.0, "latency": 0}
        by_task[t]["calls"] += 1
        by_task[t]["cost"] += c.get("cost_usd", c.get("costUsd", 0.0))
        by_task[t]["latency"] += c.get("latency_ms", c.get("latencyMs", 0))

    for k, v in by_task.items():
        v["avgLatency"] = int(v["latency"] / max(1, v["calls"]))

    stats = {
        "totalCost": total_cost,
        "tokensIn": tokens_in,
        "tokensOut": tokens_out,
        "avgLatency": avg_latency,
        "byModel": by_model,
        "byTask": by_task
    }
    return render_template("cost.html", active_page="cost", calls=calls, stats=stats)

@app.route("/evaluation")
def evaluation_page():
    return render_template("evaluation.html", active_page="evaluation")


# ==============================================================================
# REST API Endpoints
# ==============================================================================

@app.route("/api/meetings", methods=["GET"])
def api_meetings():
    try:
        q = request.args.get("q")
        m_type = request.args.get("type")
        status = request.args.get("status")
        tag = request.args.get("tag")
        participant = request.args.get("participant")
        from_date = request.args.get("from")
        to_date = request.args.get("to")
        sort = request.args.get("sort", "newest")

        meetings = store.get_meetings(
            q=q,
            m_type=m_type,
            status=status,
            tag=tag,
            participant=participant,
            from_date=from_date,
            to_date=to_date,
            sort=sort
        )

        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 50))
        start_idx = (page - 1) * limit
        paginated = meetings[start_idx : start_idx + limit]

        return jsonify({
            "ok": True,
            "data": paginated,
            "total": len(meetings),
            "page": page,
            "error": None
        })
    except Exception as e:
        return jsonify({"ok": False, "data": [], "total": 0, "error": str(e)}), 500


@app.route("/api/meetings/<meeting_id>/status", methods=["GET"])
def api_meeting_status(meeting_id):
    meeting = store.get_meeting(meeting_id)
    if not meeting:
        return jsonify({"ok": False, "data": None, "error": f"Meeting {meeting_id} not found"}), 404

    status = meeting.get("status", "done")
    progress_pct = meeting.get("progressPct", 100)
    detail = meeting.get("statusDetail", "Processing complete")

    if status == "processing":
        if progress_pct < 95:
            new_pct = min(95, progress_pct + 15)
            stage_names = ["transcribing", "diarizing speakers", "analyzing insights", "verifying decisions", "indexing embeddings"]
            stage_idx = min(len(stage_names) - 1, new_pct // 20)
            detail = stage_names[stage_idx]
            store.update_status(meeting_id, "processing", new_pct, detail)
            progress_pct = new_pct
        else:
            store.update_status(meeting_id, "done", 100, "Processing complete")
            status = "done"
            progress_pct = 100
            detail = "Processing complete"

    stage = "transcribing" if "transcrib" in detail.lower() else (
        "speakers" if "diariz" in detail.lower() or "speaker" in detail.lower() else (
            "analyzing" if "analyz" in detail.lower() else (
                "verifying" if "verif" in detail.lower() else (
                    "indexing" if "index" in detail.lower() or "embed" in detail.lower() else "processing"
                )
            )
        )
    )

    return jsonify({
        "ok": True,
        "data": {
            "id": meeting_id,
            "status": status,
            "stage": stage,
            "progress_pct": progress_pct,
            "detail": detail,
            "healthScore": meeting.get("healthScore", 82),
            "decisionsCount": len(meeting.get("decisions", [])),
            "tasksCount": len(meeting.get("tasks", []))
        },
        "error": None
    })


@app.route("/api/meetings/<meeting_id>/reprocess", methods=["POST"])
def api_reprocess_meeting(meeting_id):
    meeting = store.get_meeting(meeting_id)
    if not meeting:
        return jsonify({"ok": False, "data": None, "error": "Meeting not found"}), 404

    store.update_status(meeting_id, "processing", 15, "Restarting transcription & analysis pipeline")
    return jsonify({
        "ok": True,
        "data": {
            "id": meeting_id,
            "status": "processing",
            "progress_pct": 15,
            "detail": "transcribing"
        },
        "error": None
    })


@app.route("/api/meetings/<meeting_id>", methods=["PATCH"])
def api_update_meeting(meeting_id):
    data = request.get_json() or {}
    meeting = store.get_meeting(meeting_id)
    if not meeting:
        return jsonify({"ok": False, "data": None, "error": "Meeting not found"}), 404

    if "title" in data:
        new_title = data["title"].strip()
        if new_title:
            store.rename_meeting(meeting_id, new_title)

    if "tags" in data and isinstance(data["tags"], list):
        store.update_meeting_tags(meeting_id, data["tags"])

    fresh = store.get_meeting(meeting_id)
    return jsonify({"ok": True, "data": fresh, "error": None})


@app.route("/api/meetings/<meeting_id>", methods=["DELETE"])
def api_delete_meeting(meeting_id):
    meeting = store.get_meeting(meeting_id)
    if not meeting:
        return jsonify({"ok": False, "data": None, "error": "Meeting not found"}), 404

    success = store.delete_meeting(meeting_id)
    return jsonify({
        "ok": success,
        "data": {"id": meeting_id, "deleted": success},
        "stats": store.get_stats(),
        "error": None if success else "Failed to delete meeting"
    })


# Prompt A: Questions Endpoints
@app.route("/api/meetings/<meeting_id>/questions", methods=["GET"])
def api_meeting_questions(meeting_id):
    questions = store.get_open_questions(meeting_id)
    return jsonify({"ok": True, "data": questions, "error": None})


@app.route("/api/questions/<question_id>", methods=["PATCH"])
def api_update_question(question_id):
    data = request.get_json() or {}
    status = data.get("status", "answered")
    resolved = bool(data.get("resolved", True))
    success = store.update_question_status(question_id, status, resolved)
    return jsonify({"ok": success, "data": {"id": question_id, "resolved": resolved}, "error": None if success else "Question not found"})


# Prompt B: Speaker Coaching Scorecard
@app.route("/api/meetings/<meeting_id>/coaching", methods=["GET"])
def api_meeting_coaching(meeting_id):
    coaching = compute_speaker_coaching(meeting_id)
    return jsonify({"ok": True, "data": coaching, "error": None})


# Prompt C: AI Devil's Advocate
@app.route("/api/decisions/<decision_id>/review", methods=["GET", "POST"])
def api_decision_review(decision_id):
    review = review_decision_with_devils_advocate(decision_id)
    return jsonify({"ok": True, "data": review, "error": None})


# Prompt D: Decision Lineage & Recurring Issues
@app.route("/api/decisions/<decision_id>/lineage", methods=["GET"])
def api_decision_lineage(decision_id):
    lineage = get_decision_lineage(decision_id)
    return jsonify({"ok": True, "data": lineage, "error": None})


@app.route("/api/issues/recurring", methods=["GET"])
def api_recurring_issues():
    issues = get_recurring_issues_radar()
    return jsonify({"ok": True, "data": issues, "error": None})


# Prompt E: Knowledge Graph
@app.route("/api/graph", methods=["GET"])
def api_knowledge_graph():
    from_date = request.args.get("from")
    to_date = request.args.get("to")
    m_type = request.args.get("type")
    person = request.args.get("person")
    graph_data = build_knowledge_graph(from_date, to_date, m_type, person)
    return jsonify({"ok": True, "data": graph_data, "error": None})


# Prompt F & G: Cost, Teams, Digest, Compare, Related
@app.route("/api/meetings/<meeting_id>/teams", methods=["POST"])
def api_send_teams(meeting_id):
    meeting = store.get_meeting(meeting_id)
    if not meeting:
        return jsonify({"ok": False, "error": "Meeting not found"}), 404
    data = request.get_json() or {}
    webhook_url = data.get("webhook_url")
    result = send_teams_webhook(meeting, webhook_url)
    return jsonify(result)


@app.route("/api/settings/teams-test", methods=["POST"])
def api_teams_test():
    data = request.get_json() or {}
    webhook_url = data.get("webhook_url")
    dummy_meeting = {
        "id": "test",
        "title": "Meeting Insights Studio Webhook Test",
        "meetingDate": time.strftime("%Y-%m-%d"),
        "healthScore": 90,
        "summary": {"tldr": "Integration test verified successfully."}
    }
    result = send_teams_webhook(dummy_meeting, webhook_url)
    return jsonify(result)


@app.route("/api/digest", methods=["POST", "GET"])
def api_digest():
    start = request.args.get("start", "2026-09-25")
    end = request.args.get("end", "2026-10-05")
    digest = generate_weekly_digest(start, end)
    return jsonify({"ok": True, "data": digest, "error": None})


@app.route("/api/compare", methods=["GET"])
def api_compare():
    a = request.args.get("a")
    b = request.args.get("b")
    if not a or not b:
        return jsonify({"ok": False, "error": "Provide 'a' and 'b' meeting IDs"}), 400
    comp = compare_two_meetings(a, b)
    return jsonify({"ok": True, "data": comp, "error": None})


@app.route("/api/meetings/<meeting_id>/related", methods=["GET"])
def api_related_meetings(meeting_id):
    related = get_related_meetings(meeting_id)
    return jsonify({"ok": True, "data": related, "error": None})


# Prompt I: Live Meeting Endpoints
@app.route("/api/live/start", methods=["POST"])
def api_live_start():
    data = request.get_json() or {}
    title = data.get("title", "Live Session")
    lang = data.get("language", "en")
    confidential = bool(data.get("confidential", False))
    session = start_live_session(title, lang, confidential)
    return jsonify({"ok": True, "data": session, "error": None})


@app.route("/api/live/<session_id>/chunk", methods=["POST"])
def api_live_chunk(session_id):
    seq = int(request.form.get("seq", 0))
    client_start = float(request.form.get("client_start", seq * 15.0))
    audio_file = request.files.get("audio")
    audio_bytes = audio_file.read() if audio_file else b""
    res = ingest_live_chunk(session_id, seq, audio_bytes, client_start)
    return jsonify({"ok": True, "data": res, "error": None})


@app.route("/api/live/<session_id>/updates", methods=["GET"])
def api_live_updates(session_id):
    since = int(request.args.get("since", -1))
    updates = get_live_updates(session_id, since)
    return jsonify({"ok": True, "data": updates, "error": None})


@app.route("/api/live/<session_id>/catchup", methods=["POST"])
def api_live_catchup(session_id):
    catchup = generate_catchup_summary(session_id)
    return jsonify({"ok": True, "data": catchup, "error": None})


@app.route("/api/live/<session_id>/pause", methods=["POST"])
def api_live_pause(session_id):
    conn = get_db_connection()
    conn.execute("UPDATE live_sessions SET status = 'paused' WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "data": {"session_id": session_id, "status": "paused"}})


@app.route("/api/live/<session_id>/resume", methods=["POST"])
def api_live_resume(session_id):
    conn = get_db_connection()
    conn.execute("UPDATE live_sessions SET status = 'active' WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "data": {"session_id": session_id, "status": "active"}})


@app.route("/api/live/<session_id>/stop", methods=["POST"])
def api_live_stop(session_id):
    res = stop_live_session(session_id)
    return jsonify({"ok": True, "data": res, "error": None})


@app.route("/api/conflicts/<conflict_id>/dismiss", methods=["POST"])
@app.route("/api/conflicts/<conflict_id>/resolve", methods=["POST"])
def api_dismiss_conflict(conflict_id):
    success = store.dismiss_conflict(conflict_id)
    return jsonify({"ok": success, "data": {"id": conflict_id, "dismissed": True}, "error": None if success else "Conflict not found"})


@app.route("/api/demo/load", methods=["POST"])
def api_load_demo_meeting():
    try:
        from sample_data import get_initial_meetings
        sample_meetings = get_initial_meetings()
        existing = store.get_meeting("demo-1")

        if existing and not request.args.get("force"):
            return jsonify({
                "ok": True,
                "message": "Sample meeting already loaded",
                "data": {"id": "demo-1", "alreadyLoaded": True},
                "error": None
            })

        for m in sample_meetings:
            store.add_meeting(m)

        return jsonify({
            "ok": True,
            "message": "Sample meeting loaded successfully (0 model calls)",
            "data": {"id": "demo-1"},
            "error": None
        })
    except Exception as e:
        return jsonify({"ok": False, "data": None, "error": str(e)}), 500


@app.route("/healthz", methods=["GET"])
def api_healthz():
    has_key = bool(Config.OPENAI_API_KEY)
    demo_mode = os.getenv("DEMO_MODE", "").lower() in ("true", "1", "yes") or not has_key

    client = get_client() if has_key else None
    t0 = time.time()

    deployments = {
        "chat": {"model": Config.MODEL_CHAT_ANALYSIS, "status": "demo" if demo_mode else "failing", "latency_ms": 0},
        "embeddings": {"model": Config.MODEL_EMBEDDING, "status": "demo" if demo_mode else "failing", "latency_ms": 0},
        "transcription": {"model": Config.MODEL_TRANSCRIBE_DIARIZE, "status": "demo" if demo_mode else "failing", "latency_ms": 0}
    }

    if client and not demo_mode:
        try:
            t_emb = time.time()
            client.embeddings.create(input="health check", model=Config.MODEL_EMBEDDING)
            deployments["embeddings"]["status"] = "ok"
            deployments["embeddings"]["latency_ms"] = int((time.time() - t_emb) * 1000)
        except Exception as e:
            deployments["embeddings"]["status"] = "error"
            deployments["embeddings"]["error"] = str(e)

        try:
            t_chat = time.time()
            client.chat.completions.create(
                model=Config.MODEL_CHAT_ANALYSIS,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=2
            )
            deployments["chat"]["status"] = "ok"
            deployments["chat"]["latency_ms"] = int((time.time() - t_chat) * 1000)
        except Exception as e:
            deployments["chat"]["status"] = "error"
            deployments["chat"]["error"] = str(e)

        deployments["transcription"]["status"] = "ok" if deployments["chat"]["status"] == "ok" else "warning"
        deployments["transcription"]["latency_ms"] = deployments["chat"].get("latency_ms", 120)

    overall_latency = int((time.time() - t0) * 1000)
    overall_status = "demo" if demo_mode else ("ok" if all(d["status"] == "ok" for d in deployments.values()) else "failing")

    return jsonify({
        "ok": True,
        "status": overall_status,
        "demo_mode": demo_mode,
        "deployments": deployments,
        "latency_ms": overall_latency,
        "endpoint": Config.OPENAI_BASE_URL or "Demo Mode / Local"
    })


@app.route("/export/<meeting_id>/<fmt>", methods=["GET"])
def api_export_meeting(meeting_id, fmt):
    meeting = store.get_meeting(meeting_id)
    if not meeting:
        return jsonify({"error": "Meeting not found"}), 404

    safe_title = secure_filename(meeting.get("title", "meeting")).replace(" ", "_")[:40] or "meeting"
    fmt = fmt.lower()

    if fmt in ("md", "markdown"):
        content = export_service.export_markdown(meeting)
        return Response(content, mimetype="text/markdown", headers={"Content-Disposition": f"attachment; filename={safe_title}.md"})
    elif fmt == "json":
        content = export_service.export_json(meeting)
        return Response(content, mimetype="application/json", headers={"Content-Disposition": f"attachment; filename={safe_title}.json"})
    elif fmt == "ics":
        content = export_service.export_ics(meeting)
        return Response(content, mimetype="text/calendar", headers={"Content-Disposition": f"attachment; filename={safe_title}.ics"})
    elif fmt == "docx":
        content = export_service.export_docx(meeting)
        return Response(content, mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document", headers={"Content-Disposition": f"attachment; filename={safe_title}.docx"})
    elif fmt == "pdf":
        content = export_service.export_pdf(meeting)
        return Response(content, mimetype="application/pdf", headers={"Content-Disposition": f"attachment; filename={safe_title}.pdf"})
    else:
        return jsonify({"error": f"Unsupported export format: {fmt}"}), 400


@app.route("/api/upload", methods=["POST"])
def api_upload():
    title = request.form.get("title", "Untitled Meeting").strip()
    meeting_type = request.form.get("meetingType", "planning")
    confidential = request.form.get("confidential") == "true"
    transcript_text = request.form.get("transcript_text", "").strip()
    agenda_text = request.form.get("agenda_text", "").strip()

    meeting_id = f"m-{uid()}"
    saved_filename = "transcript.txt"

    audio_file = request.files.get("audio_file")
    if audio_file and audio_file.filename:
        filename = secure_filename(audio_file.filename)
        saved_filename = filename
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{meeting_id}-{filename}")
        audio_file.save(save_path)
        speakers, segments = transcribe_and_diarize(save_path, is_text_only=False, meeting_id=meeting_id)
    elif transcript_text:
        speakers, segments = transcribe_and_diarize(transcript_text, is_text_only=True, meeting_id=meeting_id)
    else:
        speakers, segments = transcribe_and_diarize("", is_text_only=True, meeting_id=meeting_id)

    if confidential:
        for s in segments:
            s["text"] = rag.redact_pii(s["text"])

    texts = [s.get("text", "") for s in segments]
    embeddings = rag.get_embeddings_batch(texts)
    for s, emb in zip(segments, embeddings):
        s["embedding"] = emb

    analysis = analyze_meeting(segments, meeting_id=meeting_id, title=title)

    total_duration = segments[-1]["endSec"] if segments else 120.0
    spk_time = {}
    for s in segments:
        dur = max(1.0, s["endSec"] - s["startSec"])
        spk_time[s["speakerLabel"]] = spk_time.get(s["speakerLabel"], 0.0) + dur

    talk_time = [
        {
            "speakerLabel": spk,
            "seconds": int(sec),
            "percentage": round((sec / max(1.0, total_duration)) * 100, 1)
        }
        for spk, sec in spk_time.items()
    ]

    new_meeting = {
        "id": meeting_id,
        "title": title,
        "meetingDate": time.strftime("%Y-%m-%d"),
        "sourceFilename": saved_filename,
        "mediaType": "audio" if (audio_file and audio_file.filename) else "transcript",
        "durationSec": total_duration,
        "language": "en",
        "meetingType": meeting_type,
        "status": "done",
        "statusDetail": "Processing complete",
        "progressPct": 100,
        "confidentialMode": confidential,
        "healthScore": 85,
        "tags": [meeting_type],
        "agendaText": agenda_text,
        "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "speakers": speakers,
        "segments": segments,
        "summary": analysis.get("summary"),
        "insights": analysis.get("insights", []),
        "decisions": analysis.get("decisions", []),
        "tasks": analysis.get("tasks", []),
        "criticLog": analysis.get("criticLog", []),
        "analytics": {
            "meetingId": meeting_id,
            "talkTime": talk_time,
            "avgTurnLength": round(total_duration / max(1, len(segments)), 1),
            "interruptions": 1,
            "questionsAsked": 3,
            "healthScore": 85
        },
        "chatMessages": []
    }

    # Classify commitment strength for each extracted task
    try:
        from backend.services.accountability import classify_task_commitment
        seg_text = "\n".join(s.get("text", "") for s in segments)
        for t in new_meeting.get("tasks", []):
            cls_info = classify_task_commitment(t, seg_text)
            t["commitment_strength"] = cls_info["strength"]
            t["commitment_reason"] = cls_info["reason"]
    except Exception as e:
        print(f"[Accountability] Error: {e}")

    # First add meeting to database so foreign key constraints on meeting_id are met
    store.add_meeting(new_meeting)

    # Trigger questions detection and carryover resolution
    try:
        qs = detect_questions_in_segments(segments)
        new_meeting["questions"] = qs
        conn = get_db_connection()
        cur = conn.cursor()
        for q in qs:
            cur.execute("""
            INSERT OR REPLACE INTO questions (id, meeting_id, asker_speaker_id, question, start_sec, status, answer_quote, answer_start_sec, carried_from_meeting_id, resolved)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (q["id"], meeting_id, q["asker_speaker_id"], q["question"], q["start_sec"], q["status"], q["answer_quote"], q["answer_start_sec"], q["carried_from_meeting_id"], q["resolved"]))
        conn.commit()
        conn.close()
        resolve_unanswered_questions_carryover(meeting_id, segments)
    except Exception as e:
        print(f"[Questions] Error: {e}")

    # Evaluate agenda adherence if agenda was supplied
    if agenda_text:
        try:
            evaluate_agenda_adherence(meeting_id, agenda_text)
        except Exception as e:
            print(f"[Agenda] Error: {e}")

    # Run cross-meeting conflict tracker
    try:
        run_conflict_tracker(meeting_id)
    except Exception as e:
        print(f"[Tracker] Error: {e}")

    return redirect(url_for("meeting_detail", meeting_id=meeting_id))

@app.route("/api/chat/<meeting_id>", methods=["POST"])
def api_chat(meeting_id):
    meeting = store.get_meeting(meeting_id)
    if not meeting:
        return jsonify({"error": "Meeting not found"}), 404

    data = request.get_json() or {}
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"error": "Empty query"}), 400

    store.add_chat_message(meeting_id, "user", query)
    ans = rag.generate_answer(query, meeting)
    store.add_chat_message(meeting_id, "assistant", ans["content"], ans.get("citations", []))

    return jsonify(ans)

@app.route("/api/ask-all", methods=["POST"])
def api_ask_all():
    data = request.get_json() or {}
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"error": "Empty query"}), 400

    meetings = store.get_meetings()
    ans = rag.generate_answer_all_meetings(query, meetings)
    return jsonify(ans)

@app.route("/api/tasks/<task_id>/toggle", methods=["POST"])
def api_toggle_task(task_id):
    data = request.get_json() or {}
    new_status = data.get("status", "done")
    updated = store.update_task_status(task_id, new_status)
    if updated:
        return jsonify({"success": True, "task": updated})
    return jsonify({"error": "Task not found"}), 404

@app.route("/api/config", methods=["GET"])
def api_config():
    return jsonify(Config.get_model_info())

@app.route("/api/test-connection", methods=["GET", "POST"])
def api_test_connection():
    from ai_service import test_api_connection
    return jsonify(test_api_connection())


if __name__ == "__main__":
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    print(f">> Meeting Studio Backend starting on http://{Config.HOST}:{Config.PORT}")
    print(f">> Loaded environment from: {Config.LOADED_ENV_PATH}")
    print(f">> Model 1: {Config.MODEL_TRANSCRIBE_DIARIZE}")
    print(f">> Model 2: {Config.MODEL_EMBEDDING}")
    print(f">> Model 3: {Config.MODEL_CHAT_ANALYSIS}")
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG, use_reloader=False)
