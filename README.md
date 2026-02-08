# BAMSec Transcript Downloader

A simple web app that downloads the most recent earnings call transcripts from your BAMSec account as PDFs. Enter a stock ticker, click download, and get a ZIP file of transcripts.

## What You Need

- A computer with **Python 3** installed ([download here](https://www.python.org/downloads/) — make sure to check "Add Python to PATH" during install)
- A **paid BAMSec subscription** (free trials have limited transcript access)

## First-Time Setup (do this once)

1. Open **PowerShell** (Windows) or **Terminal** (Mac)
2. Navigate to this folder (replace the path with wherever you put it):
   ```
   cd "C:\Users\YourName\Desktop\PublicAnalysis"
   ```
3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
4. Install the browser used for automation:
   ```
   python -m playwright install chromium
   ```

## How to Use

1. In PowerShell/Terminal, navigate to this folder and run:
   ```
   python app.py
   ```
2. Open your web browser and go to: **http://localhost:5000**
3. Enter your BAMSec email and password
4. Enter a stock ticker (e.g. RH, AAPL, MSFT)
5. Click **Download Transcripts**
6. Wait 1-2 minutes — a ZIP file with the PDFs will download automatically

## Troubleshooting

- **"pip is not recognized"** — Python isn't installed, or "Add to PATH" wasn't checked during install. Reinstall Python and check that box.
- **"Login failed"** — Double-check your BAMSec email and password
- **"No transcripts found"** — The ticker might not have transcripts on BAMSec, or the site layout may have changed
- **Page won't load** — Make sure `python app.py` is still running in your terminal
