import os
import re
import time

from playwright.sync_api import Page


def search_company(page: Page, ticker: str) -> None:
    """Search for a company by ticker on BAMSec and navigate to its page."""
    print(f"Searching for ticker: {ticker}...")

    # The homepage/nav bar has a search input with placeholder "Ticker or company name"
    search_input = page.locator('input[placeholder*="Ticker"], input[placeholder*="company"]').first
    search_input.wait_for(state="visible", timeout=15000)
    search_input.click()
    search_input.fill(ticker)

    # Wait for the autocomplete dropdown to appear
    # The dropdown shows results like:  RH  |  NYSE: RH
    time.sleep(3)

    # Click the first matching result in the dropdown
    # The first result should be an exact ticker match
    try:
        # Look for dropdown items — they appear as a list below the search
        first_result = page.locator(f'a:has-text("NYSE: {ticker.upper()}")').first
        first_result.wait_for(state="visible", timeout=5000)
        first_result.click()
    except Exception:
        try:
            # Try broader match — just the ticker text as a bold/link in dropdown
            first_result = page.locator(f'a:has-text("{ticker.upper()}")').first
            first_result.wait_for(state="visible", timeout=3000)
            first_result.click()
        except Exception:
            # Last resort: press Enter
            search_input.press("Enter")

    page.wait_for_load_state("networkidle")
    time.sleep(2)
    print(f"Navigated to company page for: {ticker}")


def go_to_transcripts(page: Page) -> None:
    """Click on the Transcripts link in the left sidebar of a company page."""
    print("Looking for Transcripts section...")

    # The left sidebar has navigation links: Categorized, Chronological, ..., Transcripts
    transcripts_link = page.locator('a:has-text("Transcripts")').first
    transcripts_link.wait_for(state="visible", timeout=10000)
    transcripts_link.click()
    page.wait_for_load_state("networkidle")
    time.sleep(2)
    print("Opened Transcripts page.")


def download_transcripts(page: Page, ticker: str, download_dir: str, count: int = 8) -> list[str]:
    """Download the most recent earnings transcripts as PDFs.

    The transcripts page shows rows grouped by year (CY 2025, CY 2024, etc.).
    Each row looks like:
        Earnings | RH, Q3 2026 Earnings Call, Dec 11, 2025

    Clicking a row opens the full transcript with a "PDF" link in the sidebar.
    """
    ticker_dir = os.path.join(download_dir, ticker.upper())
    os.makedirs(ticker_dir, exist_ok=True)

    print(f"Looking for the {count} most recent earnings transcripts...")

    # Collect all links that contain "Earnings Call" in their text
    # These are the clickable transcript rows
    all_links = page.locator("a").all()

    transcript_entries = []
    for link in all_links:
        try:
            text = (link.text_content(timeout=2000) or "").strip()
            href = link.get_attribute("href") or ""
            if "Earnings Call" in text and href:
                transcript_entries.append({"text": text, "href": href})
        except Exception:
            continue

    # Also try: rows where "Earnings" appears as a label in a table
    if not transcript_entries:
        rows = page.locator("tr").all()
        for row in rows:
            try:
                text = (row.text_content(timeout=2000) or "").strip()
                if "Earnings" in text:
                    link = row.locator("a").first
                    href = link.get_attribute("href") or ""
                    if href:
                        transcript_entries.append({"text": text, "href": href})
            except Exception:
                continue

    transcript_entries = transcript_entries[:count]

    if not transcript_entries:
        print("No transcripts found on this page.")
        debug_path = os.path.join(ticker_dir, "debug_transcripts.png")
        try:
            page.screenshot(path=debug_path)
            print(f"  DEBUG: Screenshot saved to {debug_path}")
        except Exception:
            pass
        return []

    print(f"Found {len(transcript_entries)} transcripts. Starting downloads...")

    downloaded_files = []
    for i, item in enumerate(transcript_entries, 1):
        # Create a clean filename from the transcript description
        # e.g. "Earnings  RH, Q3 2026 Earnings Call, Dec 11, 2025"
        raw_name = item["text"].replace("\n", " ").strip()
        # Extract the meaningful part: "RH, Q3 2026 Earnings Call, Dec 11, 2025"
        match = re.search(r'(\w+,\s*Q\d\s+\d{4}\s+Earnings Call[^"]*\d{4})', raw_name)
        if match:
            clean_name = match.group(1)
        else:
            clean_name = raw_name
        clean_name = re.sub(r'[<>:"/\\|?*]', '_', clean_name)[:100]
        filename = f"{i:02d}_{clean_name}.pdf"
        filepath = os.path.join(ticker_dir, filename)

        print(f"  [{i}/{len(transcript_entries)}] {clean_name}...")

        try:
            # Navigate to the transcript page
            href = item["href"]
            if not href.startswith("http"):
                href = "https://www.bamsec.com" + href
            page.goto(href)
            page.wait_for_load_state("networkidle")
            time.sleep(2)

            # The transcript page has a left sidebar with "Share", "Print", "PDF"
            # Click the "PDF" link to download
            pdf_link = page.locator('a:has-text("PDF")').first
            pdf_link.wait_for(state="visible", timeout=10000)

            with page.expect_download(timeout=60000) as download_info:
                pdf_link.click()
            download = download_info.value
            download.save_as(filepath)

            downloaded_files.append(filepath)
            print(f"    Saved: {filename}")

        except Exception as e:
            print(f"    Failed: {e}")
            try:
                debug_path = os.path.join(ticker_dir, f"debug_{i}.png")
                page.screenshot(path=debug_path)
            except Exception:
                pass

        # Small delay between downloads
        time.sleep(1)

    return downloaded_files
