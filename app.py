"""
app.py
------
Flask backend for the AI Interview Trainer Agent.

Routes:
  GET  /                     — Home page
  POST /upload_resume        — Extract resume text + parse with Granite
  POST /generate_questions   — Generate HR / Technical / Behavioral questions
  POST /upload_kb            — Ingest a knowledge-base PDF/TXT into ChromaDB
  GET  /kb_status            — Return knowledge-base chunk count
  POST /clear_kb             — Wipe the knowledge base
  GET  /health               — Simple health-check endpoint
"""

import os
import json
import logging
import re
import uuid
from pathlib import Path

from flask import (Flask, render_template, request,
                   jsonify, session, redirect, url_for)
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

import watsonx_client as wx
import rag_utils
import agent_instructions as AI

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# ── Flask app setup ───────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")
app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_UPLOAD_MB", 16)) * 1024 * 1024

UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def _allowed(filename: str, allowed: set) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


def _safe_json_parse(raw: str) -> dict | list | None:
    """
    Strip markdown fences and extract the first valid JSON object or array
    from the model output. Tries progressively larger substrings on failure
    so that truncated or padded responses still parse.
    """
    if not raw:
        return None

    # 1. Remove ```json ... ``` or ``` ... ``` fences
    cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()

    # 2. Try the full cleaned string first
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # 3. Walk through looking for the first { or [ and try to parse from there
    for start_char in ("[", "{"):
        idx = cleaned.find(start_char)
        if idx == -1:
            continue
        # Try slicing from first bracket to end
        candidate = cleaned[idx:]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass
        # Try finding the last matching closing bracket and slicing to that
        end_char = "]" if start_char == "[" else "}"
        last_idx = candidate.rfind(end_char)
        if last_idx != -1:
            try:
                return json.loads(candidate[:last_idx + 1])
            except json.JSONDecodeError:
                pass

    return None


def _build_resume_summary(parsed: dict) -> str:
    """
    Build a rich plain-text resume summary for prompt injection.
    Includes every section so Granite has full context when generating questions.
    """
    lines = []
    if parsed.get("name"):
        lines.append(f"Name: {parsed['name']}")
    if parsed.get("location"):
        lines.append(f"Location: {parsed['location']}")
    if parsed.get("summary"):
        lines.append(f"Summary: {parsed['summary']}")

    # Skills — all of them
    if parsed.get("skills"):
        lines.append("Skills: " + ", ".join(parsed["skills"]))

    # Education — all entries
    for edu in parsed.get("education", []):
        gpa = f", GPA {edu['gpa']}" if edu.get("gpa") else ""
        lines.append(f"Education: {edu.get('degree','')} from {edu.get('institution','')} ({edu.get('year','')}){gpa}")

    # Work experience — all entries, all responsibilities
    for exp in parsed.get("experience", []):
        resp = "; ".join(exp.get("responsibilities", [])[:4])
        lines.append(f"Experience: {exp.get('title','')} at {exp.get('company','')} ({exp.get('duration','')}) — {resp}")

    # Internships
    for intern in parsed.get("internships", []):
        resp = "; ".join(intern.get("responsibilities", [])[:2])
        lines.append(f"Internship: {intern.get('title','')} at {intern.get('company','')} ({intern.get('duration','')}) — {resp}")

    # Projects — all entries
    for proj in parsed.get("projects", []):
        techs = ", ".join(proj.get("technologies", []))
        lines.append(f"Project: {proj.get('name','')} — {proj.get('description','')} [Technologies: {techs}]")

    # Certifications
    if parsed.get("certifications"):
        lines.append("Certifications: " + " | ".join(parsed["certifications"]))

    # Achievements
    if parsed.get("achievements"):
        lines.append("Achievements: " + " | ".join(parsed["achievements"]))

    # Languages
    if parsed.get("languages"):
        lines.append("Languages: " + ", ".join(parsed["languages"]))

    return "\n".join(lines)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health")
def health():
    import watsonx_client as wx
    return jsonify({
        "status": "ok",
        "configured_model": os.getenv("GRANITE_MODEL_ID", "ibm/granite-3-3-8b-instruct"),
        "active_model": wx.get_active_model_id() or "not yet initialised",
    })


# ── Resume Upload & Parsing ────────────────────────────────────────────────────
@app.route("/upload_resume", methods=["POST"])
def upload_resume():
    if "resume" not in request.files:
        return jsonify({"error": "No file provided."}), 400

    file = request.files["resume"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    if not _allowed(file.filename, AI.ALLOWED_RESUME_EXTENSIONS):
        return jsonify({"error": "Only PDF files are accepted for resumes."}), 400

    filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    try:
        # Extract raw text
        raw_text = rag_utils.extract_text_from_file(filepath)
        if not raw_text.strip():
            return jsonify({"error": "Could not extract text from the PDF. Is it a scanned image?"}), 422

        # Build extraction prompt — use up to 8000 chars to capture all sections
        prompt = AI.RESUME_EXTRACTION_PROMPT.format(
            persona=AI.AGENT_PERSONA,
            resume_text=raw_text[:8000],
        )

        raw_response = wx.generate(prompt)
        parsed = _safe_json_parse(raw_response)

        if parsed is None or not isinstance(parsed, dict):
            logger.warning("JSON parse failed — falling back to raw text for session summary")
            parsed = {"parse_error": True, "raw": raw_response}
            # IMPORTANT: always store a usable plain-text summary so that
            # /generate_questions never sees an empty session["resume_summary"]
            session["resume_summary"] = raw_text[:3000]
        else:
            session["resume_summary"] = _build_resume_summary(parsed) or raw_text[:3000]

        session["resume_parsed"] = parsed

        return jsonify({"success": True, "data": parsed})

    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 500
    except Exception as exc:
        logger.error("Unexpected error in upload_resume: %s", exc, exc_info=True)
        return jsonify({"error": "An unexpected error occurred."}), 500
    finally:
        # Clean up uploaded file
        try:
            os.remove(filepath)
        except OSError:
            pass


# ── Question Generation ────────────────────────────────────────────────────────
@app.route("/generate_questions", methods=["POST"])
def generate_questions():
    body = request.get_json(silent=True) or {}
    job_role = body.get("job_role", "").strip()
    categories = body.get("categories", list(AI.QUESTION_CATEGORIES.keys()))

    if not job_role:
        return jsonify({"error": "Please enter a job role."}), 400

    resume_summary = session.get("resume_summary", "")
    if not resume_summary:
        return jsonify({"error": "Please upload your resume first."}), 400

    # RAG context
    rag_raw = rag_utils.retrieve_context(f"{job_role} interview questions")
    rag_context = (
        AI.RAG_CONTEXT_TEMPLATE.format(context=rag_raw)
        if rag_raw else AI.RAG_CONTEXT_EMPTY
    )

    results = {}

    for cat_key in categories:
        cat = AI.QUESTION_CATEGORIES.get(cat_key)
        if cat is None:
            continue

        prompt = cat["prompt_template"].format(
            persona=AI.AGENT_PERSONA,
            job_role=job_role,
            resume_text=resume_summary,
            rag_context=rag_context,
        )

        try:
            raw = wx.generate(prompt)
            parsed = _safe_json_parse(raw)
            results[cat_key] = {
                "label": cat["label"],
                "questions": parsed if isinstance(parsed, list) else [],
                "raw": raw if parsed is None else None,
            }
        except RuntimeError as exc:
            results[cat_key] = {"label": cat["label"], "questions": [], "error": str(exc)}

    return jsonify({"success": True, "job_role": job_role, "results": results})


# ── Preparation Tips ───────────────────────────────────────────────────────────
@app.route("/generate_tips", methods=["POST"])
def generate_tips():
    body = request.get_json(silent=True) or {}
    job_role = body.get("job_role", "").strip()

    if not job_role:
        return jsonify({"error": "Please enter a job role."}), 400

    resume_summary = session.get("resume_summary", "")
    if not resume_summary:
        return jsonify({"error": "Please upload your resume first."}), 400

    rag_raw = rag_utils.retrieve_context(f"{job_role} interview preparation tips")
    rag_context = (
        AI.RAG_CONTEXT_TEMPLATE.format(context=rag_raw)
        if rag_raw else AI.RAG_CONTEXT_EMPTY
    )

    prompt = AI.PREPARATION_TIPS_PROMPT.format(
        persona=AI.AGENT_PERSONA,
        job_role=job_role,
        resume_text=resume_summary,
        rag_context=rag_context,
    )

    try:
        raw = wx.generate(prompt)
        parsed = _safe_json_parse(raw)

        # If JSON parse failed, build a minimal tips dict from the raw prose
        # so the frontend always gets something useful to display.
        if not isinstance(parsed, dict):
            logger.warning("Tips JSON parse failed — wrapping raw text as prose_tips")
            parsed = {"prose_tips": raw}

        return jsonify({"success": True, "tips": parsed})
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 500


# ── Knowledge Base ─────────────────────────────────────────────────────────────
@app.route("/upload_kb", methods=["POST"])
def upload_kb():
    if "kb_file" not in request.files:
        return jsonify({"error": "No file provided."}), 400

    file = request.files["kb_file"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    if not _allowed(file.filename, AI.ALLOWED_KB_EXTENSIONS):
        return jsonify({"error": "Only PDF and TXT files are accepted for the knowledge base."}), 400

    filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    try:
        doc_id = Path(file.filename).stem[:50]
        chunks_added = rag_utils.ingest_document(filepath, doc_id=doc_id)
        stats = rag_utils.get_kb_stats()
        return jsonify({
            "success": True,
            "chunks_added": chunks_added,
            "total_chunks": stats["total_chunks"],
            "filename": file.filename,
        })
    except Exception as exc:
        logger.error("KB ingest error: %s", exc, exc_info=True)
        return jsonify({"error": f"Failed to ingest document: {exc}"}), 500
    finally:
        try:
            os.remove(filepath)
        except OSError:
            pass


@app.route("/kb_status")
def kb_status():
    return jsonify(rag_utils.get_kb_stats())


@app.route("/clear_kb", methods=["POST"])
def clear_kb():
    rag_utils.clear_knowledge_base()
    return jsonify({"success": True, "message": "Knowledge base cleared."})


# ── Error handlers ─────────────────────────────────────────────────────────────
@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": f"File too large. Maximum size is {os.getenv('MAX_UPLOAD_MB', 16)} MB."}), 413


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error."}), 500


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    app.run(debug=debug, host="0.0.0.0", port=5000)
