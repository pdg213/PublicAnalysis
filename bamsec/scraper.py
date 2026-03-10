from __future__ import annotations

import os
import re
import time
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Page


def search_company(page: Page, ticker: str) -> str:
    """Search for a company by ticker on BAMSec and navigate to its page.
    Returns the company page URL so we can navigate back to it later."""
    print(f"Searching for ticker: {ticker}...")

    # Go to homepage first to ensure the search bar is available
    page.goto("https://www.bamsec.com")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # The homepage/nav bar has a search input with placeholder "Ticker or company name"
    search_input = page.locator('input[placeholder*="Ticker"], input[placeholder*="company"]').first
    search_input.wait_for(state="visible", timeout=15000)
    search_input.click()
    search_input.fill(ticker)

    # Wait for the autocomplete dropdown to appear
    time.sleep(3)

    # Click the first matching result in the dropdown
    try:
        first_result = page.locator(f'a:has-text("NYSE: {ticker.upper()}")').first
        first_result.wait_for(state="visible", timeout=5000)
        first_result.click()
    except Exception:
        try:
            first_result = page.locator(f'a:has-text("{ticker.upper()}")').first
            first_result.wait_for(state="visible", timeout=3000)
            first_result.click()
        except Exception:
            search_input.press("Enter")

    page.wait_for_load_state("networkidle")
    time.sleep(2)
    company_url = page.url
    print(f"Navigated to company page for: {ticker} ({company_url})")
    return company_url


def go_to_company_page(page: Page, company_url: str) -> None:
    """Navigate directly back to a company page by URL."""
    print(f"Returning to company page...")
    page.goto(company_url)
    page.wait_for_load_state("networkidle")
    time.sleep(2)


def go_to_transcripts(page: Page) -> None:
    """Click on the Transcripts link in the left sidebar of a company page."""
    print("Looking for Transcripts section...")
    transcripts_link = page.locator('a:has-text("Transcripts")').first
    transcripts_link.wait_for(state="visible", timeout=10000)
    transcripts_link.click()
    page.wait_for_load_state("networkidle")
    time.sleep(2)
    print("Opened Transcripts page.")


def go_to_categorized(page: Page) -> None:
    """Click on the Categorized link to see Financials on the company page."""
    print("Looking for Categorized/Financials section...")
    cat_link = page.locator('a:has-text("Categorized")').first
    cat_link.wait_for(state="visible", timeout=10000)
    cat_link.click()
    page.wait_for_load_state("networkidle")
    time.sleep(2)
    print("Opened Categorized page.")


def _parse_filing_date(text: str) -> datetime | None:
    """Try to extract a date from filing row text like 'ended 11/01/25  12/11/25'."""
    # Look for dates in MM/DD/YY format — the last one is typically the filing date
    dates = re.findall(r'(\d{2}/\d{2}/\d{2})', text)
    if dates:
        try:
            return datetime.strptime(dates[-1], "%m/%d/%y")
        except ValueError:
            pass
    return None


def _download_pdf(page: Page, href: str, filepath: str) -> bool:
    """Navigate to a document page and click the PDF link to download it."""
    if not href.startswith("http"):
        href = "https://www.bamsec.com" + href
    page.goto(href)
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    pdf_link = page.locator('a:has-text("PDF")').first
    pdf_link.wait_for(state="visible", timeout=10000)

    with page.expect_download(timeout=60000) as download_info:
        pdf_link.click()
    download = download_info.value
    download.save_as(filepath)
    return True


def download_transcripts(
    page: Page,
    ticker: str,
    download_dir: str,
    count: int = 8,
    progress_callback=None,
) -> list[str]:
    """Download the most recent earnings transcripts as PDFs."""
    ticker_dir = os.path.join(download_dir, ticker.upper(), "transcripts")
    os.makedirs(ticker_dir, exist_ok=True)

    if progress_callback:
        progress_callback(f"[{ticker}] Looking for earnings transcripts...")

    # Collect all links that contain "Earnings Call"
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

    # Fallback: rows with "Earnings" in a table
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
        if progress_callback:
            progress_callback(f"[{ticker}] No transcripts found.")
        return []

    if progress_callback:
        progress_callback(f"[{ticker}] Found {len(transcript_entries)} transcripts. Downloading...")

    downloaded_files = []
    for i, item in enumerate(transcript_entries, 1):
        raw_name = item["text"].replace("\n", " ").strip()
        match = re.search(r'(\w+,\s*Q\d\s+\d{4}\s+Earnings Call[^"]*\d{4})', raw_name)
        clean_name = match.group(1) if match else raw_name
        clean_name = re.sub(r'[<>:"/\\|?*]', '_', clean_name)[:100]
        filename = f"{ticker}_{clean_name}.pdf"
        filepath = os.path.join(ticker_dir, filename)

        if progress_callback:
            progress_callback(f"[{ticker}] Downloading transcript {i}/{len(transcript_entries)}: {clean_name}")

        try:
            _download_pdf(page, item["href"], filepath)
            downloaded_files.append(filepath)
        except Exception as e:
            if progress_callback:
                progress_callback(f"[{ticker}] Failed transcript {i}: {e}")

        time.sleep(1)

    return downloaded_files


def download_financials(
    page: Page,
    ticker: str,
    download_dir: str,
    count: int = 8,
    filing_types: list[str] | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    progress_callback=None,
) -> list[str]:
    """Download the most recent financial filings (10-Q, 10-K) as PDFs.

    The Financials section on the Categorized page shows rows like:
        10-Q | Q3 | ended 11/01/25 | 12/11/25
        10-K | FY 2024 | ended 02/01/25 | 04/02/25

    Each row links to the filing, which has a "PDF" link in the sidebar.
    """
    ticker_dir = os.path.join(download_dir, ticker.upper(), "financials")
    os.makedirs(ticker_dir, exist_ok=True)

    if progress_callback:
        progress_callback(f"[{ticker}] Looking for financial filings...")

    # Parse date filters
    date_from_dt = None
    date_to_dt = None
    if date_from:
        try:
            date_from_dt = datetime.strptime(date_from, "%Y-%m-%d")
        except ValueError:
            pass
    if date_to:
        try:
            date_to_dt = datetime.strptime(date_to, "%Y-%m-%d")
        except ValueError:
            pass

    # Default to both 10-Q and 10-K
    if not filing_types:
        filing_types = ["10-Q", "10-K"]

    # Find all rows in the Financials section
    # The rows contain links with text like "10-Q" or "10-K"
    all_links = page.locator("a").all()

    filing_entries = []
    for link in all_links:
        try:
            text = (link.text_content(timeout=2000) or "").strip()
            href = link.get_attribute("href") or ""
            if not href:
                continue

            # Check if this is a financial filing link
            is_filing = False
            filing_type = ""
            for ft in filing_types:
                if ft in text:
                    is_filing = True
                    filing_type = ft
                    break

            if not is_filing:
                continue

            # Get the full row text for date/period info
            parent = link.locator("xpath=ancestor::tr").first
            try:
                row_text = (parent.text_content(timeout=2000) or "").strip()
            except Exception:
                row_text = text

            # Apply date filter if specified
            if date_from_dt or date_to_dt:
                filing_date = _parse_filing_date(row_text)
                if filing_date:
                    if date_from_dt and filing_date < date_from_dt:
                        continue
                    if date_to_dt and filing_date > date_to_dt:
                        continue

            # Extract period info (Q1, Q2, Q3, FY 2024, etc.)
            period = ""
            period_match = re.search(r'(Q\d|FY\s*\d{4})', row_text)
            if period_match:
                period = period_match.group(1)

            # Extract the "ended" date for naming
            ended_match = re.search(r'ended\s+(\d{2}/\d{2}/\d{2})', row_text)
            ended = ended_match.group(1) if ended_match else ""

            filing_entries.append({
                "text": row_text,
                "href": href,
                "type": filing_type,
                "period": period,
                "ended": ended,
            })
        except Exception:
            continue

    # Also try table rows directly if the above didn't find enough
    if not filing_entries:
        rows = page.locator("tr").all()
        for row in rows:
            try:
                text = (row.text_content(timeout=2000) or "").strip()
                has_type = any(ft in text for ft in filing_types)
                if not has_type:
                    continue

                link = row.locator("a").first
                href = link.get_attribute("href") or ""
                if not href:
                    continue

                filing_type = ""
                for ft in filing_types:
                    if ft in text:
                        filing_type = ft
                        break

                if date_from_dt or date_to_dt:
                    filing_date = _parse_filing_date(text)
                    if filing_date:
                        if date_from_dt and filing_date < date_from_dt:
                            continue
                        if date_to_dt and filing_date > date_to_dt:
                            continue

                period_match = re.search(r'(Q\d|FY\s*\d{4})', text)
                period = period_match.group(1) if period_match else ""
                ended_match = re.search(r'ended\s+(\d{2}/\d{2}/\d{2})', text)
                ended = ended_match.group(1) if ended_match else ""

                filing_entries.append({
                    "text": text,
                    "href": href,
                    "type": filing_type,
                    "period": period,
                    "ended": ended,
                })
            except Exception:
                continue

    filing_entries = filing_entries[:count]

    if not filing_entries:
        if progress_callback:
            progress_callback(f"[{ticker}] No financial filings found.")
        return []

    if progress_callback:
        progress_callback(f"[{ticker}] Found {len(filing_entries)} filings. Downloading...")

    downloaded_files = []
    for i, item in enumerate(filing_entries, 1):
        # Clean filename like: RH_10-K_FY2024.pdf or RH_10-Q_Q3_ended_110125.pdf
        parts = [ticker.upper(), item["type"]]
        if item["period"]:
            parts.append(item["period"].replace(" ", ""))
        if item["ended"]:
            parts.append("ended_" + item["ended"].replace("/", ""))
        filename = "_".join(parts) + ".pdf"
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filepath = os.path.join(ticker_dir, filename)

        if progress_callback:
            progress_callback(
                f"[{ticker}] Downloading filing {i}/{len(filing_entries)}: "
                f"{item['type']} {item['period']}"
            )

        try:
            _download_pdf(page, item["href"], filepath)
            downloaded_files.append(filepath)
        except Exception as e:
            if progress_callback:
                progress_callback(f"[{ticker}] Failed filing {i}: {e}")

        time.sleep(1)

    return downloaded_files
