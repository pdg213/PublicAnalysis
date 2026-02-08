from playwright.sync_api import Page


def login(page: Page, email: str, password: str) -> None:
    """Log into BAMSec using email and password."""
    print("Opening BAMSec login page...")
    page.goto("https://www.bamsec.com/login")
    page.wait_for_load_state("networkidle")

    # Fill in email
    email_input = page.locator('input[type="email"], input[name="email"], input[placeholder*="mail"]').first
    email_input.wait_for(state="visible", timeout=15000)
    email_input.fill(email)

    # Fill in password
    password_input = page.locator('input[type="password"]').first
    password_input.wait_for(state="visible", timeout=15000)
    password_input.fill(password)

    # Click submit
    submit_button = page.locator('button[type="submit"], input[type="submit"]').first
    submit_button.click()

    # Wait for login to complete — look for navigation away from login page
    print("Logging in...")
    page.wait_for_url(lambda url: "/login" not in url, timeout=30000)
    print("Logged in successfully!")
