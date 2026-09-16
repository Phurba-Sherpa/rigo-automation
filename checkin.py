# checkin.py
from playwright.sync_api import sync_playwright
from datetime import datetime
import sys

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(storage_state="session.json")
    page = context.new_page()

    api_success = {"done": False}

    def check_response(response):
        if "clock" in response.url.lower() and response.request.method == "POST":
            print(f"[{datetime.now()}] Clock-in API response: {response.status} {response.url}")
            if response.status < 400:
                api_success["done"] = True

    page.on("response", check_response)

    page.goto("https://app.rigohr.com/hr/clock/in")
    page.wait_for_timeout(2000)

    try:
        button = page.get_by_role("button").filter(has_text="Clock In")
        button.wait_for(timeout=15000)
        button.click()

        submit_button = page.locator('button[aria-label="CheckIn Submit Button"]')
        submit_button.wait_for(state="visible", timeout=10000)

        # Diagnostic: confirm it's actually enabled/clickable before we try
        is_enabled = submit_button.is_enabled()
        print(f"[{datetime.now()}] Submit button visible. Enabled: {is_enabled}")

        submit_button.click(timeout=10000, force=False)  # force=False will error loudly if truly not clickable

        page.wait_for_timeout(3000)

        if api_success["done"]:
            print(f"[{datetime.now()}] Checked in — confirmed via API response.")
        else:
            page.screenshot(path="debug_checkin_unconfirmed.png", full_page=True)
            print(f"[{datetime.now()}] WARNING: clicked through, but no successful clock API response seen.")

    except Exception as e:
        page.screenshot(path="debug_checkin_failure.png", full_page=True)
        print(f"[{datetime.now()}] Check-in failed: {e}", file=sys.stderr)
        sys.exit(1)

    context.storage_state(path="session.json")
    browser.close()
