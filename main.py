"""
BAMSec Transcript Downloader

Downloads the most recent earnings call transcripts for a given stock ticker
from BAMSec. Requires a paid BAMSec subscription.

Usage:
    python main.py TICKER
    python main.py RH
    python main.py AAPL --count 4
"""

import argparse
import sys

from playwright.sync_api import sync_playwright

from bamsec.auth import login
from bamsec.config import BAMSEC_EMAIL, BAMSEC_PASSWORD, DOWNLOAD_DIR
from bamsec.scraper import download_transcripts, go_to_transcripts, search_company


def main():
    parser = argparse.ArgumentParser(
        description="Download earnings transcripts from BAMSec"
    )
    parser.add_argument("ticker", help="Stock ticker symbol (e.g. RH, AAPL)")
    parser.add_argument(
        "--count", type=int, default=8,
        help="Number of transcripts to download (default: 8)"
    )
    parser.add_argument(
        "--headed", action="store_true", default=True,
        help="Show the browser window (default: yes)"
    )
    parser.add_argument(
        "--headless", action="store_true",
        help="Run without showing the browser window"
    )
    args = parser.parse_args()

    # Validate credentials
    if not BAMSEC_EMAIL or not BAMSEC_PASSWORD:
        print("ERROR: BAMSec credentials not found!")
        print()
        print("Please create a file called '.env' in this folder with your login info:")
        print()
        print("  BAMSEC_EMAIL=your_email@example.com")
        print("  BAMSEC_PASSWORD=your_password")
        print()
        print("(You can copy .env.example and fill in your details)")
        sys.exit(1)

    headless = args.headless

    print(f"BAMSec Transcript Downloader")
    print(f"Ticker: {args.ticker.upper()}")
    print(f"Downloading: {args.count} most recent transcripts")
    print(f"Save folder: downloads/{args.ticker.upper()}/")
    print("-" * 40)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        try:
            # Step 1: Log in
            login(page, BAMSEC_EMAIL, BAMSEC_PASSWORD)

            # Step 2: Search for the company
            search_company(page, args.ticker)

            # Step 3: Go to Transcripts section
            go_to_transcripts(page)

            # Step 4: Download transcripts
            files = download_transcripts(page, args.ticker, DOWNLOAD_DIR, args.count)

            # Summary
            print("-" * 40)
            if files:
                print(f"Done! Downloaded {len(files)} transcripts to: downloads/{args.ticker.upper()}/")
            else:
                print("No transcripts were downloaded.")
                print("This might mean:")
                print("  - The ticker wasn't found on BAMSec")
                print("  - The page layout has changed")
                print("  - There are no transcripts available for this company")
                print()
                print("Try running with --headed to watch what's happening in the browser.")

        except Exception as e:
            print(f"Something went wrong: {e}")
            print()
            print("If this keeps happening, the BAMSec website may have changed.")
            print("Try running with --headed to see what the browser is doing.")
            sys.exit(1)

        finally:
            browser.close()


if __name__ == "__main__":
    main()
