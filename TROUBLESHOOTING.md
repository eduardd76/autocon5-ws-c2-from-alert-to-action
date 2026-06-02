# Troubleshooting — The Top 10 Things That Will Bite You

If your lab is broken, find the symptom below and run the fix verbatim. **Do not improvise.** The labs are timeboxed.

---

## 1. `docker compose up` exits immediately with `port is already allocated`

**Symptom:**
```
Error response from daemon: Ports are not available: 0.0.0.0:8501 ...
```

**Fix:**
```bash
docker compose down
lsof -i :8501 -i :8002 -i :8001 -i :6379
# kill the offending PID, OR change the port in docker-compose.yml
docker compose up -d
```

Most common cause on macOS: a previous Streamlit dev server you forgot about, or AirPlay Receiver on port 5000 (not our port, but check anyway).

---

## 2. UI loads but says "cannot reach Team Leader"

**Symptom:** UI at `http://localhost:8501` renders but the agent status panel shows red dots.

**Fix:**
```bash
docker compose logs team-leader | tail -30
# if you see "ConnectionRefusedError: Redis", restart Redis first:
docker compose restart redis
sleep 5
docker compose restart team-leader
```

---

## 3. `preflight_check.sh: Permission denied`

**Symptom:**
```
zsh: permission denied: ./scripts/preflight_check.sh
```

**Fix:**
```bash
chmod +x scripts/*.sh
./scripts/preflight_check.sh
```

---

## 4. Docker says "Cannot connect to the Docker daemon"

**Symptom:**
```
Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?
```

**Fix (macOS / Windows):** Open Docker Desktop application from Applications / Start Menu. Wait 30s for the whale to settle.

**Fix (Linux):**
```bash
sudo systemctl start docker
sudo usermod -aG docker $USER
# log out and back in
```

---

## 5. Container exits with `exec format error`

**Symptom:** A container immediately dies. `docker compose logs <svc>` shows `exec format error`.

**Cause:** You're on Apple Silicon (M1/M2/M3) and pulled an x86_64-only image.

**Fix:**
```bash
docker compose down
docker pull --platform=linux/arm64 redis:7-alpine
docker pull --platform=linux/arm64 python:3.11-slim
docker compose up -d
```

All our app images build on top of `python:3.11-slim` which is multi-arch, so this should only hit you if your Docker is misconfigured.

---

## 6. `incident_queue` empty even after I clicked "Trigger"

**Symptom:** UI says incident triggered but no agent activity in the dashboard.

**Fix — verify Redis has the event:**
```bash
docker compose exec redis redis-cli
> LLEN incident_queue
> KEYS *
> exit
```

If `LLEN` is 0: the syslog injector didn't fire. Re-trigger from the UI button, or via curl:
```bash
curl -X POST http://localhost:8001/incident/trigger \
  -H "X-MCP-API-Key: dev-key-123"
```

---

## 7. "Lab 3 tests fail with `ModuleNotFoundError: starter`"

**Symptom:**
```
ModuleNotFoundError: No module named 'starter'
```

**Fix:** You're running pytest from the wrong directory.
```bash
cd labs/lab3_wire_your_own_specialist
python -m pytest starter/test_my_specialist.py -v
```

Always `cd` into the lab dir first. The `python -m pytest` form (not just `pytest`) fixes the import path.

---

## 8. `docker compose up` hangs forever on "Pulling redis"

**Symptom:** First-time pull stuck for >5 min.

**Fix:** Conference wifi is bad. Use your phone hotspot. If you pre-pulled with `pull_all_images.sh` at home, you should not see this — start there.

If pre-pulled and still hanging:
```bash
docker compose down
docker images | grep -E "redis|python"   # confirm images are cached
docker compose up --no-pull -d            # skip the pull step entirely
```

---

## 9. Agent logs spam `LLM_PROVIDER=stub: scenario unknown`

**Symptom:** Every incident triggers but the agent always returns the same generic response.

**Cause:** The stub LLM only knows about the scenarios in `services/shared/stub_llm_client.py`. If you triggered a scenario name it doesn't recognize, it falls back to a generic response.

**Fix:** Only trigger the scenarios listed in the lab READMEs (`bgp_session_idle`, `evpn_route_missing`). For Lab 3, your custom scenario must be registered in `lab3/starter/scenario.yaml` AND mapped in your specialist's `classify()` method.

---

## 10. Streamlit UI shows `WebSocketError` and won't refresh

**Symptom:** UI loads once but the SSE event stream dies.

**Fix:** Hard refresh the browser (`Cmd+Shift+R` on mac, `Ctrl+Shift+R` on linux). If still dead:
```bash
docker compose restart ui
sleep 8
# refresh browser
```

If you're using Safari and seeing weird SSE behavior, use Chrome or Firefox for the workshop — Safari's EventSource handling has quirks.

---

## "I tried everything, my lab is dead"

1. Nuclear option (preserves nothing):
   ```bash
   docker compose down -v
   docker system prune -af --volumes
   docker compose up --build -d
   ```
2. Still broken? Post in `#autocon5-ws-c2` on NAF Slack with:
   - Your OS + Docker version (`docker version | head -10`)
   - The last 20 lines of `docker compose logs --tail=20`
   - What you were trying to do
3. Worst-case fallback during the workshop: follow along on the projector — every lab has a screenshot output in its README so you can see what success looks like even without your own stack running.
