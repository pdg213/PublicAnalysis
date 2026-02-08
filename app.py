"""
BAMSec Document Downloader — Web App

A web interface for downloading earnings transcripts and financial filings
from BAMSec. Supports multiple tickers, filing type filters, date ranges,
live progress updates, credential caching, and download history.

Run with: python app.py
Then open http://localhost:5000 in your browser.
"""

import io
import json
import os
import queue
import shutil
import tempfile
import threading
import time
import uuid
import zipfile
from datetime import datetime, timedelta

from flask import Flask, Response, jsonify, render_template, request, send_file

from bamsec.auth import login
from bamsec.scraper import (
    download_financials,
    download_transcripts,
    go_to_categorized,
    go_to_company_page,
    go_to_transcripts,
    search_company,
)

app = Flask(__name__)

# --- Credential caching (server-side, 6-hour expiry) ---
_credential_cache = {}  # token -> {email, password, expires}
CREDENTIAL_TTL_HOURS = 6

# --- Job tracking for progress updates ---
_jobs = {}  # job_id -> {queue, status, files, error}

# --- Download history ---
HISTORY_FILE = os.path.join(os.path.dirname(__file__), "download_history.json")


def _load_history() -> list[dict]:
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE) as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _save_history(entry: dict) -> None:
    history = _load_history()
    history.insert(0, entry)
    # Keep last 50 entries
    history = history[:50]
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def _cache_credentials(email: str, password: str) -> str:
    """Store credentials and return a token."""
    token = str(uuid.uuid4())
    _credential_cache[token] = {
        "email": email,
        "password": password,
        "expires": datetime.now() + timedelta(hours=CREDENTIAL_TTL_HOURS),
    }
    # Clean up expired tokens
    now = datetime.now()
    expired = [k for k, v in _credential_cache.items() if v["expires"] < now]
    for k in expired:
        del _credential_cache[k]
    return token


def _get_cached_credentials(token: str) -> tuple[str, str] | None:
    """Retrieve credentials by token if not expired."""
    if token in _credential_cache:
        entry = _credential_cache[token]
        if entry["expires"] > datetime.now():
            return entry["email"], entry["password"]
        else:
            del _credential_cache[token]
    return None


def _run_download_job(job_id: str, email: str, password: str, config: dict) -> None:
    """Background worker that runs the scraping job and sends progress via queue."""
    job = _jobs[job_id]
    q = job["queue"]

    tickers = config["tickers"]
    download_transcripts_flag = config.get("transcripts", False)
    download_financials_flag = config.get("financials", False)
    transcript_count = config.get("transcript_count", 8)
    financial_count = config.get("financial_count", 8)
    filing_types = config.get("filing_types", ["10-Q", "10-K"])
    date_from = config.get("date_from") or None
    date_to = config.get("date_to") or None

    tmp_dir = tempfile.mkdtemp()
    all_files = []

    def progress(msg):
        q.put({"type": "progress", "message": msg})

    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(accept_downloads=True)
            page = context.new_page()

            try:
                progress("Logging into BAMSec...")
                login(page, email, password)
                progress("Logged in successfully!")

                for ticker_idx, ticker in enumerate(tickers):
                    ticker = ticker.strip().upper()
                    if not ticker:
                        continue

                    progress(f"[{ticker}] Searching for company ({ticker_idx + 1}/{len(tickers)})...")
                    company_url = search_company(page, ticker)

                    if download_transcripts_flag:
                        go_to_transcripts(page)
                        files = download_transcripts(
                            page, ticker, tmp_dir, transcript_count,
                            progress_callback=progress,
                        )
                        all_files.extend(files)

                        # Navigate directly back to company page for financials
                        if download_financials_flag:
                            go_to_company_page(page, company_url)

                    if download_financials_flag:
                        go_to_categorized(page)
                        files = download_financials(
                            page, ticker, tmp_dir, financial_count,
                            filing_types=filing_types,
                            date_from=date_from,
                            date_to=date_to,
                            progress_callback=progress,
                        )
                        all_files.extend(files)

            finally:
                browser.close()

        if not all_files:
            q.put({"type": "error", "message": "No documents found for the given tickers/options."})
            job["status"] = "error"
            return

        # Package into ZIP
        progress("Packaging files into ZIP...")
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for filepath in all_files:
                # Preserve folder structure: TICKER/transcripts/file.pdf
                rel_path = os.path.relpath(filepath, tmp_dir)
                zf.write(filepath, rel_path)
        zip_buffer.seek(0)

        # Determine ZIP filename
        if len(tickers) == 1:
            zip_name = f"{tickers[0].upper()}_bamsec.zip"
        else:
            zip_name = "bamsec_downloads.zip"

        job["zip_data"] = zip_buffer.getvalue()
        job["zip_name"] = zip_name
        job["file_count"] = len(all_files)
        job["status"] = "done"

        # Save to history
        _save_history({
            "timestamp": datetime.now().isoformat(),
            "tickers": [t.upper() for t in tickers],
            "transcripts": download_transcripts_flag,
            "financials": download_financials_flag,
            "file_count": len(all_files),
            "transcript_count": transcript_count if download_transcripts_flag else 0,
            "financial_count": financial_count if download_financials_flag else 0,
        })

        progress(f"Done! {len(all_files)} files ready for download.")

    except Exception as e:
        error_msg = str(e)
        if "login" in error_msg.lower() or "password" in error_msg.lower():
            q.put({"type": "error", "message": "Login failed. Check your email and password."})
        else:
            q.put({"type": "error", "message": f"Something went wrong: {error_msg}"})
        job["status"] = "error"

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        q.put({"type": "done"})


# --- Routes ---

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def start_download():
    """Start a download job and return a job ID for progress tracking."""
    data = request.get_json()

    email = data.get("email", "").strip()
    password = data.get("password", "")
    cred_token = data.get("cred_token", "")

    # Try cached credentials first
    if cred_token:
        cached = _get_cached_credentials(cred_token)
        if cached:
            email, password = cached

    if not email or not password:
        return jsonify({"error": "Please enter your BAMSec email and password."}), 400

    # Parse tickers (comma-separated)
    tickers_raw = data.get("tickers", "").strip()
    if not tickers_raw:
        return jsonify({"error": "Please enter at least one stock ticker."}), 400
    tickers = [t.strip().upper() for t in tickers_raw.split(",") if t.strip()]

    if not data.get("transcripts") and not data.get("financials"):
        return jsonify({"error": "Please select at least one document type (Transcripts or Financials)."}), 400

    # Cache credentials
    new_token = _cache_credentials(email, password)

    # Create job
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "queue": queue.Queue(),
        "status": "running",
        "zip_data": None,
        "zip_name": None,
        "file_count": 0,
    }

    config = {
        "tickers": tickers,
        "transcripts": data.get("transcripts", False),
        "financials": data.get("financials", False),
        "transcript_count": data.get("transcript_count", 8),
        "financial_count": data.get("financial_count", 8),
        "filing_types": data.get("filing_types", ["10-Q", "10-K"]),
        "date_from": data.get("date_from", ""),
        "date_to": data.get("date_to", ""),
    }

    thread = threading.Thread(target=_run_download_job, args=(job_id, email, password, config))
    thread.daemon = True
    thread.start()

    return jsonify({"job_id": job_id, "cred_token": new_token})


@app.route("/progress/<job_id>")
def progress_stream(job_id):
    """Server-Sent Events stream for live progress updates."""
    if job_id not in _jobs:
        return jsonify({"error": "Job not found"}), 404

    def generate():
        job = _jobs[job_id]
        q = job["queue"]
        while True:
            try:
                msg = q.get(timeout=60)
                yield f"data: {json.dumps(msg)}\n\n"
                if msg.get("type") == "done":
                    break
            except queue.Empty:
                # Send keepalive
                yield f"data: {json.dumps({'type': 'keepalive'})}\n\n"

    return Response(generate(), mimetype="text/event-stream")


@app.route("/download/<job_id>")
def download_result(job_id):
    """Download the ZIP file for a completed job."""
    if job_id not in _jobs:
        return jsonify({"error": "Job not found"}), 404

    job = _jobs[job_id]
    if job["status"] != "done" or not job["zip_data"]:
        return jsonify({"error": "Download not ready"}), 400

    return send_file(
        io.BytesIO(job["zip_data"]),
        mimetype="application/zip",
        as_attachment=True,
        download_name=job["zip_name"],
    )


@app.route("/history")
def get_history():
    """Return download history."""
    return jsonify(_load_history())


@app.route("/check-credentials", methods=["POST"])
def check_credentials():
    """Check if a credential token is still valid."""
    data = request.get_json()
    token = data.get("cred_token", "")
    cached = _get_cached_credentials(token)
    if cached:
        # Return masked email
        email = cached[0]
        masked = email[:3] + "***" + email[email.index("@"):]
        return jsonify({"valid": True, "email": masked})
    return jsonify({"valid": False})


if __name__ == "__main__":
    print("=" * 50)
    print("BAMSec Document Downloader")
    print("Open this link in your browser: http://localhost:5000")
    print("=" * 50)
    app.run(debug=False, port=5000)
