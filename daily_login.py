from playwright.sync_api import sync_playwright
from datetime import datetime
import json
import sys
import time

with open("credentials.json") as f:
    creds = json.load(f)

LOGIN_URL = "https://app.rigohr.com/login"
MAX_RETRIES = 3

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    try:
        # Step 1-3: email + continue, with retry on transient network error
        for attempt in range(1, MAX_RETRIES + 1):
            page.goto(LOGIN_URL)
            page.fill("#email-input", creds["email"])
            page.click("#sign-btn")
            page.wait_for_timeout(3000)

            error_visible = page.get_by_text("Network error", exact=False).is_visible()
            if error_visible:
                print(f"[{datetime.now()}] Attempt {attempt}: 'Network error' after email submit.")
                if attempt == MAX_RETRIES:
                    raise Exception("Repeated 'Network error' after email submit — giving up.")
                time.sleep(10 * attempt)  # 10s, 20s backoff
                continue
            break  # no error, proceed

        # Step 4: Click the "Microsoft" SSO button
        try:
            page.get_by_role("button", name="Microsoft").click(timeout=15000)
        except Exception:
            page.screenshot(path="debug_after_email.png", full_page=True)
            raise Exception(f"Microsoft button not found. URL: {page.url}")

        # Step 5-6: Might land straight in, or hit a Microsoft password page
        password_field = page.locator("#i0118")
        try:
            password_field.wait_for(timeout=10000)
            password_field.fill(creds["password"])
            page.click("#idSIButton9")  # "Sign in"

            # Optional "Stay signed in?" prompt reuses the same button id
            stay_signed_in = page.locator("#idSIButton9")
            try:
                stay_signed_in.wait_for(timeout=8000)
                stay_signed_in.click()  # "Yes"
            except Exception:
                pass  # prompt didn't appear, that's fine
        except Exception:
            print(f"[{datetime.now()}] No password prompt — already trusted/logged in.")

        # Confirm we actually landed on RigoHR (not stuck mid-auth)
        page.wait_for_timeout(2000)
        try:
            page.wait_for_url("https://app.rigohr.com/**", timeout=15000)
        except Exception:
            page.screenshot(path="debug_login.png", full_page=True)
            raise Exception(f"Never reached app.rigohr.com, final URL: {page.url}")

        context.storage_state(path="session.json")
        print(f"[{datetime.now()}] Daily login successful. Session refreshed.")

    except Exception as e:
        print(f"[{datetime.now()}] Daily login failed: {e}", file=sys.stderr)
        sys.exit(1)

    browser.close()
