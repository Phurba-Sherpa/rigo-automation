# RigoHR Attendance Automation

Automatically logs in, clocks you **in** when your laptop boots, and clocks you **out** when you shut it down — by driving a headless browser against RigoHR.

> ⚠️ This automates real "Clock In" / "Clock Out" actions on your behalf. Use responsibly — it reflects when your machine is on, not necessarily when you're actually working.
>
> ⚠️ **This stores your actual Microsoft/RigoHR password on disk** (`credentials.json`) so it can refresh its login session automatically. Treat this repo and folder as sensitive.

---

## Current scope

1. **Automatic login, check-in, and check-out** — triggered on boot and shutdown, no daily interaction needed.
2. **Manual trigger of any individual step** (login, check-in, or check-out) — for testing or one-off use outside the normal boot/shutdown flow.

---

## How it works

- RigoHR login goes through Microsoft SSO, so a real (headless) browser drives the login — not a simple API call.
- A **login** step runs first to get a fresh session, since RigoHR sessions are short-lived.
- **Check-in** then clicks "Clock In" and confirms it.
- **Check-out** clicks "Clock Out" and confirms it — and if the session has already expired by the time you shut down, it logs in again automatically before retrying.
- On **boot**: login runs first, and check-in only runs if login succeeded.
- On **shutdown**: check-out runs automatically (with its own session-refresh built in).

---

## 1. Setup

1. Clone this repo and install dependencies:
   ```bash
   git clone <this-repo-url> rigo-automation
   cd rigo-automation
   uv sync
   uv run playwright install chromium
   sudo .venv/bin/playwright install-deps chromium
   ```
2. Set up your credentials:
   ```bash
   cp credentials.example.json credentials.json
   chmod 600 credentials.json
   ```
   Edit `credentials.json` and fill in your real email and password.
3. Verify `credentials.json` and `session.json` are excluded from git (already handled by `.gitignore`, but double-check with `git status` before pushing anything).

---

## 2. Enable automatic login, check-in, and check-out

Three `systemd` services handle this:

| Service | Trigger | Depends on |
|---|---|---|
| `attendance-login` | On boot | — |
| `attendance-checkin` | On boot | Only runs if `attendance-login` succeeds |
| `attendance-checkout` | On shutdown | Refreshes its own session if needed |

Setup steps:
1. Copy the three `.service` files (included in this repo under `systemd/`) into `/etc/systemd/system/`, updating the username and path inside each to match your machine.
2. Reload and enable:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable attendance-login.service
   sudo systemctl enable attendance-checkin.service
   sudo systemctl enable attendance-checkout.service
   ```
3. Reboot once to confirm login + check-in fire correctly, then do a real `sudo shutdown -h now` and boot back up to confirm check-out fired on the previous session.

Once enabled, no daily interaction is needed — everything runs automatically on boot and shutdown.

---

## 3. Running things manually

Useful for testing, or if you ever need to trigger something outside the normal boot/shutdown flow:

```bash
uv run python daily_login.py     # refresh the login session
uv run python checkin.py         # clock in
uv run python checkout.py        # clock out
```

> **Always run `daily_login.py` first before a manual `checkin.py` or `checkout.py`.** RigoHR sessions are short-lived, so a session saved earlier in the day may already be dead by the time you manually trigger a check-in/out later — logging in fresh right beforehand avoids a failed run.

Logs for each are written to `login.log`, `checkin.log`, and `checkout.log` in this folder — check these first if something doesn't seem to have registered on RigoHR.

---

## Security

- `credentials.json` and `session.json` hold real login secrets — never commit them, never share them, never copy them off this machine.
- `chmod 600 credentials.json` restricts it to your user only — this is already set up as part of the setup steps above.
- Each person running this needs their **own** `credentials.json` and `session.json`, tied to their own account.
- Storing a real password on disk is a real security trade-off — if this laptop is ever compromised, this file is a direct credential leak. Weigh that against the convenience for your own situation.
- Avoid running the login step repeatedly in quick succession while testing — enterprise Microsoft accounts can flag rapid automated sign-ins as suspicious.

---

## Planned improvements (not yet implemented)

1. **Restrict auto check-in/check-out to the internal office network (`techkraft.net`)** — add a guard that only allows the automatic trigger to proceed if the office network is reachable, preventing accidental clock in/out from home or elsewhere.
2. **Time-of-day guard** — detect whether it's morning or evening and skip the irrelevant action, so a random reboot mid-day doesn't accidentally re-trigger check-in or check-out.
3. **A "remote" vs "physical" mode setting** — since RigoHR itself is a public site and can't tell where you actually are, this would layer on top of the network guard above: when set to "physical," the automation would additionally require that the internal network is reachable (proof you're actually in the office) before allowing check-in/check-out — the internal network being unreachable from home makes this a reliable signal that automatic triggering shouldn't fire from anywhere unless you're intentionally targeting office presence.

---

## Found a bug?

If check-in/check-out fails, doesn't register on RigoHR, or you hit anything unexpected, please open an issue in this repo (or reach out directly) with:
- Which step failed (login / check-in / check-out)
- The relevant log file contents (`login.log` / `checkin.log` / `checkout.log`)
- Roughly what time it happened

That makes it much faster to track down than a "it didn't work" report alone.
