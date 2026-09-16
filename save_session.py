# save_session.py — run this once manually (not via systemd)
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # visible so you can log in
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://app.rigohr.com/login")
    print("Log in manually (Microsoft SSO, MFA, etc). Press Enter here when you land on the dashboard.")
    input()
    context.storage_state(path="session.json")
    browser.close()
