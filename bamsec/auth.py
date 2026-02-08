import os
import time

from playwright.sync_api import Page


def login(page: Page, email: str, password: str) -> None:
    """Log into BAMSec using email and password."""
    print("Opening BAMSec login page...")
    page.goto("https://www.bamsec.com/login")
    page.wait_for_load_state("networkidle")

    # Wait a bit for any JS rendering
    time.sleep(3)

    # Try to find the email input using many possible selectors
    email_selectors = [
        'input[type="email"]',
        'input[name="email"]',
        'input[placeholder*="mail"]',
        'input[placeholder*="Mail"]',
        'input[autocomplete="email"]',
        'input[autocomplete="username"]',
        'input[name="username"]',
        'input[name="login"]',
        'input[type="text"]',
    ]

    email_input = None
    for selector in email_selectors:
        try:
            el = page.locator(selector).first
            if el.is_visible(timeout=2000):
                email_input = el
                print(f"  Found email field: {selector}")
                break
        except Exception:
            continue

    if not email_input:
        # Take a screenshot for debugging
        debug_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "debug_login.png")
        page.screenshot(path=debug_path)
        print(f"  DEBUG: Screenshot saved to {debug_path}")
        print(f"  DEBUG: Current URL is {page.url}")
        print(f"  DEBUG: Page title is {page.title()}")
        raise Exception(
            "Could not find the email/username field on the BAMSec login page. "
            "A screenshot has been saved to debug_login.png — please share it so we can fix this."
        )

    email_input.fill(email)

    # Find the password input
    password_input = page.locator('input[type="password"]').first
    try:
        password_input.wait_for(state="visible", timeout=10000)
    except Exception:
        # Some sites show password on a second step
        # Try clicking next/continue first
        for btn_text in ["Next", "Continue", "Submit"]:
            try:
                btn = page.locator(f'button:has-text("{btn_text}")').first
                if btn.is_visible(timeout=1000):
                    btn.click()
                    time.sleep(2)
                    break
            except Exception:
                continue
        password_input = page.locator('input[type="password"]').first
        password_input.wait_for(state="visible", timeout=10000)

    password_input.fill(password)

    # Click the sign in / submit button
    submit_selectors = [
        'button:has-text("Sign In")',
        'button:has-text("Log In")',
        'button:has-text("Login")',
        'button:has-text("Sign in")',
        'button:has-text("Log in")',
        'button[type="submit"]',
        'input[type="submit"]',
    ]

    for selector in submit_selectors:
        try:
            btn = page.locator(selector).first
            if btn.is_visible(timeout=2000):
                btn.click()
                print(f"  Clicked: {selector}")
                break
        except Exception:
            continue

    # Wait for login to complete
    print("Logging in...")
    try:
        page.wait_for_url(lambda url: "/login" not in url, timeout=30000)
        print("Logged in successfully!")
    except Exception:
        # Take a screenshot to see what happened
        debug_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "debug_after_login.png")
        page.screenshot(path=debug_path)
        print(f"  DEBUG: Screenshot saved to {debug_path}")
        raise Exception(
            "Login didn't complete — the page stayed on the login screen. "
            "This might mean wrong credentials, or the site needs extra steps (like 2FA). "
            "A screenshot has been saved to debug_after_login.png."
        )
