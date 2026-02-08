# BAMSec Document Downloader

A web app that downloads earnings call transcripts and financial filings (10-Q, 10-K) from your BAMSec account as PDFs.

## Features

- **Earnings transcripts** and **financial filings** (10-Q, 10-K)
- **Multiple tickers at once** — type "RH, AAPL, MSFT" to download from all three
- **Live progress updates** — see exactly what's happening as it downloads
- **Credential caching** — enter your BAMSec login once, stays saved for 6 hours
- **Filing type filter** — download only 10-Qs, only 10-Ks, or both
- **Date range filter** — only download filings from a specific time period
- **Custom counts** — choose how many transcripts/filings to download per ticker
- **Download history** — see a log of your previous downloads
- **Clean file names** — PDFs are named like `RH_10-K_FY2024.pdf`

## What You Need

- **Python 3** installed ([download here](https://www.python.org/downloads/) — check "Add Python to PATH" during install)
- A **paid BAMSec subscription**

## First-Time Setup (do this once)

1. Open **PowerShell** (Windows) or **Terminal** (Mac)
2. Go to this folder:
   ```
   cd path\to\PublicAnalysis
   ```
3. Install packages:
   ```
   python -m pip install -r requirements.txt
   ```
4. Install the browser:
   ```
   python -m playwright install chromium
   ```

## How to Use

1. Start the app:
   ```
   python app.py
   ```
2. Open **http://localhost:5000** in your browser
3. Enter your BAMSec email and password (only needed the first time — it remembers for 6 hours)
4. Enter one or more stock tickers
5. Check off what you want: Transcripts, Financials, or both
6. Click **Download** and watch the progress
7. When done, click **Save ZIP File** to get your PDFs

## Troubleshooting

- **"pip is not recognized"** — Use `python -m pip install` instead of `pip install`
- **"Login failed"** — Double-check your BAMSec email and password
- **"No documents found"** — The ticker may not have transcripts/filings on BAMSec
- **Page won't load** — Make sure `python app.py` is still running in your terminal
