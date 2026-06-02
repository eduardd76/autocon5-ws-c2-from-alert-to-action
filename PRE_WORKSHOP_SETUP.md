# Pre-Workshop Setup — Do This 24 Hours Before Munich

If you do these 5 steps at home with a stable wifi connection, you will start the workshop in a working state. **Do not wait until the venue.** Conference wifi will not be your friend when 250 people try to pull container images at once.

Estimated time: **15 minutes**.

---

## Step 1 — Install Docker (skip if already installed)

**macOS:** Download Docker Desktop from <https://docs.docker.com/desktop/install/mac-install/> and run the installer. Open Docker Desktop once, accept the EULA, wait for the whale icon in your menu bar.

**Ubuntu / Linux:**
```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
# log out and back in for the group change to take effect
```

**Windows:** Install WSL2 first (<https://learn.microsoft.com/windows/wsl/install>), then Docker Desktop with the WSL2 backend. Run all the lab commands inside your WSL2 Ubuntu prompt, not PowerShell.

Verify:
```bash
docker --version          # expect >= 24
docker compose version    # expect v2.x
```

---

## Step 2 — Give Docker enough RAM

The stack needs **8 GB RAM allocated to Docker**. Default on macOS is 4 GB.

**Docker Desktop (mac/win):** Settings → Resources → Memory → drag to 8 GB → Apply & Restart.

**Linux:** No action needed (Docker uses the host's RAM directly).

---

## Step 3 — Clone the repo and run preflight

```bash
git clone https://github.com/eduardd76/autocon5-ws-c2-from-alert-to-action.git
cd autocon5-ws-c2-from-alert-to-action
cp .env.sample .env
./scripts/preflight_check.sh
```

Expected output ends with:
```
✅ READY — your laptop is set up for AutoCon5 WS:C2
```

If you see `❌ FIX:`, follow the printed instruction. If still stuck, jump to `TROUBLESHOOTING.md` or post in `#autocon5-ws-c2` on NAF Slack.

---

## Step 4 — Pre-pull all images (wifi-failure insurance)

```bash
./scripts/pull_all_images.sh
```

This pulls `redis:7-alpine` and `python:3.11-slim` into your local Docker cache. About 200 MB. Once cached, you can run the labs even if the conference wifi melts.

---

## Step 5 — Smoke test the stack

```bash
docker compose up -d
sleep 20
curl -s http://localhost:8001/health | grep -q healthy && echo "MCP OK"
curl -s http://localhost:8002/acp/health | grep -q ok && echo "TL OK"
curl -sI http://localhost:8501 | grep -q 200 && echo "UI OK"
docker compose down
```

You should see three `OK` lines. If yes, you're done — see you in Munich.

---

## Optional: bring a hotspot

Conference wifi at AutoCon4 buckled when ~250 engineers downloaded container images simultaneously. If you can, bring a phone with mobile hotspot capability. Tethering as a fallback turned a 3-hour workshop drama into a non-event for previous attendees.

---

## What to bring on the day

- Laptop (charged + charger)
- Power strip if you have one (your neighbor will love you)
- USB-C ↔ USB-A adapter if you have one (the room only has 2 USB-A ports per row)
- Notebook + pen — there's a worksheet at your seat for Lab 3 design
- Your favorite hot drink in a sealed cup

See you at the Westin Grand, Tuesday morning, room TBD on the NAF AC5 site.
