#!/usr/bin/env python3
"""Secured quiz server for antiviral drug question bank — Chapter 44 Pharmacology.

Questions live ONLY in server memory. The API serves one question at a time.
No bulk-export endpoint exists. Rate-limited to deter scraping.

Run locally:   python app.py
Deploy to web: Render / Railway / PythonAnywhere (Procfile + requirements.txt ready)
"""

import csv
import io
import os
import secrets
from pathlib import Path

from flask import Flask, jsonify, render_template, request, abort
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["300 per hour", "30 per minute"],
    storage_uri=os.environ.get("RATELIMIT_STORAGE", "memory://"),
)

# ---------------------------------------------------------------------------
# Load question bank into server memory — CSV file is NEVER served to clients
# ---------------------------------------------------------------------------
CSV_PATH = Path(__file__).parent / "antiviral.csv"

def load_questions() -> list[dict]:
    text = CSV_PATH.read_text(encoding="utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    questions = []
    for row in reader:
        questions.append({
            "id": int(row["id"]),
            "question": row["question"].strip(),
            "options": [
                row["option_a"].strip(),
                row["option_b"].strip(),
                row["option_c"].strip(),
                row["option_d"].strip(),
                row["option_e"].strip(),
            ],
            "correct": row["correct"].strip().upper(),
            "explanation": row["explanation"].strip(),
            "category": row.get("category", "").strip(),
        })
    return questions

QUESTIONS: list[dict] = load_questions()
CATEGORIES: list[str] = sorted({q["category"] for q in QUESTIONS if q["category"]})

print(f"[server] Loaded {len(QUESTIONS)} questions across {len(CATEGORIES)} categories.")

# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/mobile")
def mobile():
    """Serve the self-contained WeChat-compatible mobile app."""
    return app.send_static_file("antiviral_app.html")

# ---------------------------------------------------------------------------
# API — metadata
# ---------------------------------------------------------------------------
@app.route("/api/info")
@limiter.limit("10 per second")
def api_info():
    return jsonify({
        "total": len(QUESTIONS),
        "categories": CATEGORIES,
    })

# ---------------------------------------------------------------------------
# API — get ONE question (no correct answer included)
# ---------------------------------------------------------------------------
@app.route("/api/question/<int:idx>")
@limiter.limit("5 per second")
def api_question(idx: int):
    if idx < 0 or idx >= len(QUESTIONS):
        abort(404, description=f"Index {idx} out of range (0-{len(QUESTIONS)-1})")

    q = QUESTIONS[idx]
    return jsonify({
        "id": q["id"],
        "index": idx,
        "total": len(QUESTIONS),
        "question": q["question"],
        "options": q["options"],
        "category": q["category"],
    })

# ---------------------------------------------------------------------------
# API — check answer
# ---------------------------------------------------------------------------
@app.route("/api/check", methods=["POST"])
@limiter.limit("5 per second")
def api_check():
    data = request.get_json(silent=True)
    if not data:
        abort(400, description="JSON body required")

    qid = data.get("id")
    answer = str(data.get("answer", "")).strip().upper()

    if not qid or answer not in "ABCDE":
        abort(400, description="id (int) and answer (A-E) required")

    q = next((q for q in QUESTIONS if q["id"] == int(qid)), None)
    if not q:
        abort(404, description="Question not found")

    return jsonify({
        "correct": answer == q["correct"],
        "correct_answer": q["correct"],
        "explanation": q["explanation"],
    })

# ---------------------------------------------------------------------------
# API — reveal answer (no student answer required)
# ---------------------------------------------------------------------------
@app.route("/api/reveal/<int:idx>")
@limiter.limit("3 per second")
def api_reveal(idx: int):
    if idx < 0 or idx >= len(QUESTIONS):
        abort(404)
    q = QUESTIONS[idx]
    return jsonify({
        "correct_answer": q["correct"],
        "explanation": q["explanation"],
    })

# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------
@app.errorhandler(404)
def not_found(e):
    return jsonify(error="Not found", detail=str(e.description)), 404

@app.errorhandler(429)
def ratelimited(e):
    return jsonify(error="Too many requests",
                   detail="请求过于频繁，请稍后再试 / Please slow down"), 429

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    print(f"[server] Listening on 0.0.0.0:{port}  (debug={debug})")
    app.run(host="0.0.0.0", port=port, debug=debug)
