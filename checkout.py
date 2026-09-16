# checkout.py
from playwright.sync_api import sync_playwright
from datetime import datetime
import json
import sys

with open("credentials.json") as f:
    creds = json.load(f)


def do_login(page):
    """Full login flow, reused as a fallback when session has expired."""
    page.goto("https://app.rigohr.com/login")
    page.fill("#email-input", creds["email"])
    page.click("#sign-btn")
    page.get_by_role("button", name="Microsoft").click(timeout=15000)

    password_field = page.locator("#i0118")
    try:
        password_field.wait_for(timeout=10000)
        password_field.fill(creds["password"])
        page.click("#idSIButton9")
        stay_signed_in = page.locator("#idSIButton9")
        try:
            stay_signed_in.wait_for(timeout=8000)
            stay_signed_in.click()
        except Exception:
            pass
    except Exception:
        print(f"[{datetime.now()}] No password prompt — already trusted/logged in.")

    page.wait_for_url("https://app.rigohr.com/**", timeout=15000)


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(storage_state="session.json")
    page = context.new_page()

    api_success = {"done": False}

    def check_response(response):
        if "clock" in response.url.lower() and response.request.method == "POST":
            print(f"[{datetime.now()}] Clock-out API response: {response.status} {response.url}")
            if response.status < 400:
                api_success["done"] = True

    page.on("response", check_response)

    try:
        page.goto("https://app.rigohr.com/hr/clock/out")
        page.wait_for_timeout(2000)

        # Session-expiry check: if we're not actually on the clock page, re-login
        if "login" in page.url or "microsoftonline" in page.url:
            print(f"[{datetime.now()}] Session expired, logging in before checkout...")
            do_login(page)
            context.storage_state(path="session.json")  # save fresh session immediately
            page.goto("https://app.rigohr.com/hr/clock/out")
            page.wait_for_timeout(2000)

        button = page.get_by_role("button").filter(has_text="Clock Out")
        button.wait_for(timeout=15000)
        button.click()

        submit_button = page.locator('button[aria-label="CheckOut Submit Button"]')
        submit_button.wait_for(state="visible", timeout=10000)
        submit_button.click(timeout=10000)

        page.wait_for_timeout(3000)

        if api_success["done"]:
            print(f"[{datetime.now()}] Checked out — confirmed via API response.")
        else:
            page.screenshot(path="debug_checkout_unconfirmed.png", full_page=True)
            print(f"[{datetime.now()}] WARNING: clicked through, but no successful clock API response seen.")

    except Exception as e:
        page.screenshot(path="debug_checkout_failure.png", full_page=True)
        print(f"[{datetime.now()}] Check-out failed: {e}", file=sys.stderr)
        sys.exit(1)

    context.storage_state(path="session.json")
    browser.close()
