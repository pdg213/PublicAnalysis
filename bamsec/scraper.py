import os
import re
import time

from playwright.sync_api import Page


def search_company(page: Page, ticker: str) -> None:
    """Search for a company by ticker on BAMSec and navigate to its page."""
    print(f"Searching for ticker: {ticker}...")
    page.goto("https://www.bamsec.com")
    page.wait_for_load_state("networkidle")

    # Use the search bar on the homepage
    search_input = page.locator(
        'input[placeholder*="earch"], input[placeholder*="icker"], '
        'input[placeholder*="ompany"], input[type="search"]'
    ).first
    search_input.wait_for(state="visible", timeout=15000)
    search_input.fill(ticker)

    # Wait for autocomplete/suggestions to appear and click the first match
    time.sleep(2)

    # Try clicking the first suggestion in a dropdown
    suggestion = page.locator(
        '[class*="suggestion"], [class*="result"], [class*="dropdown"] a, '
        '[class*="autocomplete"] a, [class*="search"] a, [role="option"]'
    ).first
    try:
        suggestion.wait_for(state="visible", timeout=5000)
        suggestion.click()
    except Exception:
        # If no dropdown, try pressing Enter
        search_input.press("Enter")

    page.wait_for_load_state("networkidle")
    print(f"Navigated to company page for: {ticker}")


def go_to_transcripts(page: Page) -> None:
    """Click on the Transcripts tab/link on a company page."""
    print("Looking for Transcripts section...")

    # Look for a Transcripts link in the sidebar or navigation
    transcripts_link = page.locator('a:has-text("Transcripts")').first
    try:
        transcripts_link.wait_for(state="visible", timeout=10000)
        transcripts_link.click()
        page.wait_for_load_state("networkidle")
        print("Opened Transcripts page.")
    except Exception:
        # Maybe we're already on a page that shows transcripts, or the URL has a pattern
        current_url = page.url
        if "/transcripts" not in current_url:
            # Try appending /transcripts to the current company URL
            page.goto(current_url.rstrip("/") + "/transcripts")
            page.wait_for_load_state("networkidle")
        print("On Transcripts page.")


def download_transcripts(page: Page, ticker: str, download_dir: str, count: int = 8) -> list[str]:
    """Download the most recent earnings transcripts as PDFs."""
    ticker_dir = os.path.join(download_dir, ticker.upper())
    os.makedirs(ticker_dir, exist_ok=True)

    print(f"Looking for the {count} most recent earnings transcripts...")

    # Find all transcript links on the page
    # BAMSec typically lists transcripts with links containing "Earnings" or "Quarter"
    all_links = page.locator("a").all()

    transcript_links = []
    for link in all_links:
        try:
            text = link.text_content(timeout=2000) or ""
            href = link.get_attribute("href") or ""
            # Look for earnings-related transcripts
            if re.search(r"(earning|quarter|Q[1-4]|annual)", text, re.IGNORECASE) and href:
                transcript_links.append({"text": text.strip(), "href": href})
        except Exception:
            continue

    # If we didn't find earnings-specific ones, grab all transcript-like links
    if len(transcript_links) < count:
        transcript_links = []
        for link in all_links:
            try:
                text = link.text_content(timeout=2000) or ""
                href = link.get_attribute("href") or ""
                # Look for any transcript/filing links (usually contain /view/ or /filing/)
                if href and re.search(r"(transcript|filing|/view/)", href, re.IGNORECASE):
                    if text.strip() and len(text.strip()) > 5:
                        transcript_links.append({"text": text.strip(), "href": href})
            except Exception:
                continue

    # Take only the requested count (most recent are typically listed first)
    transcript_links = transcript_links[:count]

    if not transcript_links:
        print("No transcripts found on this page. The page structure may have changed.")
        print("Current URL:", page.url)
        return []

    print(f"Found {len(transcript_links)} transcripts. Starting downloads...")

    downloaded_files = []
    for i, item in enumerate(transcript_links, 1):
        name = re.sub(r'[<>:"/\\|?*]', '_', item['text'])[:80]
        filename = f"{i:02d}_{name}.pdf"
        filepath = os.path.join(ticker_dir, filename)

        print(f"  [{i}/{len(transcript_links)}] Downloading: {item['text'][:60]}...")

        try:
            # Navigate to the transcript page
            href = item["href"]
            if not href.startswith("http"):
                href = "https://www.bamsec.com" + href
            page.goto(href)
            page.wait_for_load_state("networkidle")

            # Look for a PDF download button/link
            pdf_button = page.locator(
                'a:has-text("PDF"), a:has-text("Download"), '
                'button:has-text("PDF"), button:has-text("Download"), '
                '[class*="pdf"], [class*="download"]'
            ).first

            try:
                pdf_button.wait_for(state="visible", timeout=10000)
                # Use Playwright's download handler
                with page.expect_download(timeout=30000) as download_info:
                    pdf_button.click()
                download = download_info.value
                download.save_as(filepath)
            except Exception:
                # If no download button, try printing the page as PDF
                page.pdf(path=filepath)

            downloaded_files.append(filepath)
            print(f"    Saved: {filename}")

        except Exception as e:
            print(f"    Failed to download: {e}")

        # Small delay to be respectful
        time.sleep(1)

    return downloaded_files
