import os
import time

from playwright.sync_api import Page


def login(page: Page, email: str, password: str) -> None:
    """Log into BAMSec using email and password."""
    print("Opening BAMSec login page...")
    page.goto("https://www.bamsec.com/login")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # The login page has labeled fields: "Email *" and "Password *"
    # Fill email — try label first, then fall back to input type
    try:
        page.get_by_label("Email").fill(email)
        print("  Filled email field.")
    except Exception:
        page.locator('input[type="email"], input[type="text"]').first.fill(email)
        print("  Filled email field (fallback).")

    # Fill password
    try:
        page.get_by_label("Password").fill(password)
        print("  Filled password field.")
    except Exception:
        page.locator('input[type="password"]').first.fill(password)
        print("  Filled password field (fallback).")

    # Click "Sign In" button
    try:
        page.get_by_role("button", name="Sign In").click()
        print("  Clicked Sign In.")
    except Exception:
        page.locator('button:has-text("Sign In")').first.click()
        print("  Clicked Sign In (fallback).")

    # Wait for login to complete — page should navigate away from /login
    print("Logging in...")
    try:
        page.wait_for_url(lambda url: "/login" not in url, timeout=30000)
        print("Logged in successfully!")
    except Exception:
        debug_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "debug_after_login.png")
        page.screenshot(path=debug_path)
        raise Exception(
            "Login didn't complete. Possible causes: wrong email/password, "
            "two-factor authentication, or CAPTCHA. "
            f"A screenshot was saved to {debug_path}"
        )
