# Lab 3 · Fire your specialist & see YOUR card

You wrote `classify()` and `diagnose()`. The 4 tests are green.
Now watch your code run *inside the live 5-layer pipeline* and produce a real
approval card — a card a human signs off, with **your name on it**.

> **Why this lab exists.** Labs 1–2 you *watched* the system solve a fault.
> Here you *teach it a new one*. A QoS congestion fault that the shipped system
> never knew about now flows end-to-end: syslog → Team Leader → **your agent** →
> MCP evidence → **your diagnosis** → human gate. That is the whole thesis of the
> workshop in 10 minutes: **expertise becomes an executable, reviewable asset.**
> The model proposes; the catalogue and a human dispose.

---

## Step 1 — prove your code in isolation (TDD gate)

```bash
cd labs/lab3_wire_your_own_specialist
python3 -m pytest test_my_specialist.py -q
```
Expected: `4 passed`.
- `classify()` says **yes** to QoS (by keyword *and* by scenario_id), **no** to unrelated faults.
- `diagnose()` returns a complete, confident card for `qos_interface_congested`.

*What you learned:* the tests ARE the spec. You didn't guess "done" — red→green told you.

---

## Step 2 — wire your agent into the pod

Your specialist runs as the 6th container (`ws-c2-your-agent`). Rebuild it with
your code, then bring the pod up:

```bash
cd ../..                       # back to repo root
docker compose up -d --build your-agent
docker compose ps              # ws-c2-your-agent -> Up
```

*What you learned:* an "agent" here is just a small service that (1) registers a
role, (2) listens on the A2A bus, (3) reads MCP tools, (4) returns a diagnosis.
No framework magic — you can read every line.

---

## Step 3 — open two watch windows

```bash
# TERMINAL A — the Team Leader's routing decision + your agent's reasoning
docker compose logs -f team-leader your-agent

# TERMINAL B — the approval queue filling up
watch -n1 'curl -s localhost:8002/acp/queues'
```

---

## Step 4 — fire YOUR fault

```bash
curl -s -X POST localhost:8001/incident/trigger \
  -H "X-MCP-API-Key: dev-key-123" -H "Content-Type: application/json" \
  -d '{"scenario_id":"qos_interface_congested","device_id":"router-1"}' ; echo
```

In **TERMINAL A** you should see the fault route to *your* specialist, not stability:
```
[team-leader] -> delegating to your_specialist as task-xxxxxxxx
[A2A] team_leader -> your_specialist: task_delegation
[your-agent] ===== delegation task-xxxxxxxx =====
[your-agent] step 1/2: reading qos_parser MCP evidence for router-1
[your-agent] step 2/2: running YOUR diagnose()
[your-agent] responded task-xxxxxxxx (confidence=0.88)
```

*What you learned:* the **catalogue** routed this — `owner_specialist: qos_specialist`
in `lab_scenarios/qos_interface_congested.yaml` is why the Team Leader picked your
agent. Change that line, change the routing. Code didn't decide; the YAML did.

---

## Step 5 — see YOUR card (the payoff)

```bash
curl -s localhost:8002/acp/approvals | python3 -m json.tool
```
You should see a card whose `specialist` is `your_specialist`, with:
- **root_cause** — the voice-priority queue oversubscription you wrote
- **evidence[0]** — `qos_parser(live): voice-priority NNNN drops/60s ...` (the MCP read your agent did *before* diagnosing — grounding, not guessing)
- **proposed_fix** — your remediation commands
- **confidence** — `0.88`

Same card is in the UI at **http://localhost:8501** under *Pending approvals*.

Approve it (you are the L5 human gate):
```bash
TASK=$(curl -s localhost:8002/acp/approvals | python3 -c 'import sys,json;print(json.load(sys.stdin)[0]["task_id"])')
curl -s -X POST localhost:8002/acp/approval \
  -H "Content-Type: application/json" \
  -d "{\"action\":\"approve\",\"task_id\":\"$TASK\",\"decision_rationale\":\"verified by me\"}" ; echo
```

---

## What you just proved
1. **You extended an agentic system with new domain knowledge** — a QoS specialist —
   without touching the Team Leader, the MCP server, or the UI.
2. **Your agent grounds before it speaks**: it reads `qos_parser` (live device facts)
   and puts that evidence on the card. The LLM step is one gated proposal, not the decision-maker.
3. **A human still signs.** The system never auto-applied your fix — it queued it for approval.

That is the safe, reviewable shape of agentic NetOps: *model proposes, catalogue routes,
evidence grounds, human disposes.*

---

## If something's off
| Symptom | Fix |
|---|---|
| Routed to `stability_specialist` | Check `owner_specialist: qos_specialist` in `lab_scenarios/qos_interface_congested.yaml`, then `docker compose restart team-leader` |
| `your-agent` not in `docker compose ps` | `docker compose up -d --build your-agent` and read its logs: `docker compose logs your-agent` |
| Card confidence not 0.88 / fields missing | Re-run `pytest` — your `diagnose()` dict is incomplete; the test will tell you which key |
| Empty `acp/approvals` | Queues drain fast; the card stays pending until approved. Re-fire and `curl` within a second or two |
