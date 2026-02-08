"""
BAMSec Transcript Downloader — Web App

A simple web interface for downloading earnings transcripts from BAMSec.
Run with: python app.py
Then open http://localhost:5000 in your browser.
"""

import io
import os
import shutil
import tempfile
import zipfile

from flask import Flask, jsonify, render_template, request, send_file
from playwright.sync_api import sync_playwright

from bamsec.auth import login
from bamsec.scraper import download_transcripts, go_to_transcripts, search_company

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/download", methods=["POST"])
def download():
    data = request.get_json()
    email = data.get("email", "").strip()
    password = data.get("password", "")
    ticker = data.get("ticker", "").strip().upper()
    count = data.get("count", 8)

    if not email or not password:
        return jsonify({"error": "Please enter your BAMSec email and password."}), 400
    if not ticker:
        return jsonify({"error": "Please enter a stock ticker."}), 400

    # Use a temporary directory for this download
    tmp_dir = tempfile.mkdtemp()

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(accept_downloads=True)
            page = context.new_page()

            try:
                login(page, email, password)
                search_company(page, ticker)
                go_to_transcripts(page)
                files = download_transcripts(page, ticker, tmp_dir, count)
            finally:
                browser.close()

        if not files:
            return jsonify({
                "error": f"No transcripts found for {ticker}. "
                         "The ticker may not have transcripts on BAMSec, "
                         "or the page layout may have changed."
            }), 404

        # Package all PDFs into a ZIP file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for filepath in files:
                filename = os.path.basename(filepath)
                zf.write(filepath, filename)
        zip_buffer.seek(0)

        return send_file(
            zip_buffer,
            mimetype="application/zip",
            as_attachment=True,
            download_name=f"{ticker}_transcripts.zip",
        )

    except Exception as e:
        error_msg = str(e)
        if "login" in error_msg.lower() or "password" in error_msg.lower():
            return jsonify({"error": "Login failed. Please check your BAMSec email and password."}), 401
        return jsonify({"error": f"Something went wrong: {error_msg}"}), 500

    finally:
        # Clean up temp files
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    print("=" * 50)
    print("BAMSec Transcript Downloader")
    print("Open this link in your browser: http://localhost:5000")
    print("=" * 50)
    app.run(debug=False, port=5000)
