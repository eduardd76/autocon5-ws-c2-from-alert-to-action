# Lab 1 — Trigger Your First Incident

## The idea — read this first (1 min)

This is your first look at the whole machine working. You fire one fake alert (a BGP session problem) and watch the AI team handle it end to end: the **Team Leader** receives it and decides which specialist it belongs to; that **specialist** gathers evidence and writes a diagnosis; and you get an **approval card** — root cause, proposed fix, confidence score — waiting for *your* click.

Watch the two things that matter:
- **The decision is delegated, but bounded.** A deterministic step routes the alert (no guessing about *who* handles it), and **nothing changes on any device** — the system stops and asks you to approve.
- **You are the gate.** The agent proposes; you dispose. That's the whole safety model: the brakes live in the system around the AI, not in the AI.

**NOC analogy:** a ticket comes in → the dispatcher routes it to the right on-call engineer → they diagnose and write up a fix → you sign off before anything is touched.

---

**Time:** 30 minutes, self-paced.
**Goal:** Push a fake BGP alert into the system and watch the 5-agent reasoning chain in real time.

---

## Before you start

You should have already run `./scripts/preflight_check.sh` and seen `✅ READY`. If not, do that first.

---

## Step 1 — Bring the stack up

From the repo root:

```bash
docker compose up -d
```

Wait ~15 seconds for all 5 containers to settle. Verify:

```bash
docker compose ps
```

Expected: 5 containers all `running` and `healthy` (or `started` for stability-agent + team-leader).

```
NAME                 STATUS              PORTS
ws-c2-mcp            Up (healthy)        0.0.0.0:8001->8000/tcp
ws-c2-redis          Up (healthy)        0.0.0.0:6379->6379/tcp
ws-c2-stability      Up                  
ws-c2-team-leader    Up                  0.0.0.0:8002->8002/tcp
ws-c2-ui             Up                  0.0.0.0:8501->8501/tcp
```

If any are `Restarting` or `Exited`, see `TROUBLESHOOTING.md`.

---

## Step 2 — Open the UI

```bash
open http://localhost:8501          # mac
xdg-open http://localhost:8501      # linux
# or just paste into your browser
```

You should see the **AutoCon5 WS:C2 — From Alert to Action** dashboard. The sidebar on the left has 2 trigger buttons. The main area shows queue depths + (empty) approvals + (empty) history.

The sidebar `Health` block should show two ✅. If you see ❌, run `docker compose logs <svc>` for the failing service.

---

## Step 3 — Trigger a BGP incident

Click **"BGP idle / ACL block (Cisco)"** in the sidebar.

Within 3 seconds you should see:

1. `incident_queue` briefly increment to 1 and back to 0 (Team Leader consumed it)
2. `specialist inbox` briefly increment (Team Leader delegated to Stability)
3. `pending approvals` increment to 1
4. The approval panel expands with the recommendation

---

## Step 4 — Read what the agents decided

The approval card shows:

- **Root cause:** BGP peer 10.0.0.2 stuck in Idle — an ACL on Gi0/0 is dropping inbound TCP/179
- **Evidence:** 3 facts from the MCP tool calls
- **Proposed fix:** 3 CLI commands
- **Rollback:** 3 CLI commands to undo
- **Risk:** `medium`
- **Confidence:** 87%

This is the full chain:

```
[you] click button
   -> MCP server emits a fake syslog onto incident_queue
   -> Team Leader pops it, classifies as "stability fault"
   -> A2A delegation to Stability Specialist via Redis queue
   -> Stability Specialist:
        - calls MCP ospf_parser  (gathers evidence)
        - calls MCP interface_parser
        - calls MCP bgp_summary
        - asks the LLM for a diagnosis
   -> A2A response back to Team Leader
   -> Team Leader pushes to approval_queue
   -> UI renders the card
[you] approve or reject
```

In the production system the LLM is a fine-tuned Qwen2.5-7B on a dedicated GPU. Here it's a stub that returns canned responses keyed off the scenario_id. Everything else is identical to production code paths.

---

## Step 5 — Approve the recommendation

Click **"✅ Approve"** on the card. It disappears from "Pending" and shows up under **"Approved history"** on the right.

---

## Step 6 — Watch the agents at work in the logs

In a new terminal:

```bash
docker compose logs -f team-leader stability-agent mcp-server
```

Click another trigger button in the UI and watch the log lines fly past. You'll see the 3-step Stability Agent flow clearly labelled:

```
[stability-agent-ws-c2] step 1/3: gathering MCP evidence for router-1
[stability-agent-ws-c2] step 2/3: LLM diagnosis for scenario=bgp_session_idle
[stability-agent-ws-c2] step 3/3: sending response to team_leader (confidence=0.87, duration=0.18s)
```

Press `Ctrl+C` to stop tailing logs.

---

## Step 7 — Try EVPN (preview of Lab 2)

Click **"EVPN Type-2 missing (Arista EOS)"**. Same flow, different scenario and a different vendor:

- The device is now `leaf-1`, vendor `arista-eos` (not Cisco)
- Root cause is an EVPN Type-2 route missing due to an RT import mismatch
- Confidence is 94%, risk `low`

Lab 2 goes deep on this multi-vendor case — this is just a taste.

---

## Step 8 — Look at what the MCP tools returned

Open a terminal and curl one of the MCP tools directly (this is exactly what the Stability Agent did):

```bash
curl -s -X POST http://localhost:8001/tools/bgp_summary \
  -H "X-MCP-API-Key: dev-key-123" \
  -H "Content-Type: application/json" \
  -d '{"device_id":"router-1"}' | python3 -m json.tool
```

You should see the structured BGP neighbor data the agent reasoned over — note the peer `10.0.0.2` in state `Idle`.

---

## Bonus (5 min, optional)

- Trigger the same scenario twice in a row. The MCP idempotency cache (60s TTL in the workshop, 24h in production) means the second call returns the cached parse instead of re-executing — check the second response is identical to the first.
- Look at `services/team-leader/main.py` `classify()` function — it's a 6-line keyword router. The production version uses scenario catalogue lookup + KG queries + LLM triage. Same idea, much smaller surface.

---

## Done

You triggered an incident, watched 4 services coordinate via 3 protocols (HTTP/ACP, Redis-list/A2A, HTTP/MCP), and approved a fix.

Move to **Lab 2** when ready.
