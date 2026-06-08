# Lab 3 — Build your own specialist (QoS)

## The idea (1 min)
In Labs 1 & 2 you *watched* the AI team. Here you **add a new member**. The trick: a
"specialist" is really just **two small functions** — everything else (messaging, the
model, the dashboard, the approval card) already exists and you never touch it.

**NOC analogy:** the system is an on-call team. The Team Leader is the dispatcher; each
specialist is the on-call engineer for one domain. Nobody covers **QoS** yet. You
"onboard" a QoS engineer by writing two things:
- **`classify()`** — *"Is this ticket mine?"* → yes / no
- **`diagnose()`** — *"Root cause, the fix, how confident I am."*

From then on the dispatcher routes QoS incidents to your specialist automatically.

> Zero AI background needed. If you can read a Python function, you can do this. The
> networking judgement is the hard part — and you already have that.

You're on your pod, in the repo root: `cd ~/autocon5-ws-c2-from-alert-to-action`

---

## Step 1 — See the failing tests (your "definition of done")
```
make lab3-test
```
Expect **`4 failed`** — clean and short (no scary traceback). Those 4 tests are the spec
for your QoS agent. Your job: turn `4 failed` → `4 passed`.

*(That's Test-Driven Development: like deciding "ping works · BGP Established · 0 drops"
**before** a change. RED = not there yet; GREEN = proven.)*

---

## Step 2 — Make them green

### ✅ Reliable path (recommended) — copy the reference, then read it
```
make lab3-solve
```
This copies the reference specialist into the **exact** file the tests load
(`starter/agent_yourname.py`) and re-runs them → **`4 passed`**. Then open it and read the
two functions you just "wrote":
```
cat labs/lab3_wire_your_own_specialist/solution/agent_qos.py
```
- `classify()` → True if the syslog contains `qos / policy-map / shaping / congestion`,
  or the `scenario_id` is one you own. Else False. *(the routing decision)*
- `diagnose()` → returns `root_cause`, `evidence`, `proposed_fix` (commands + rollback),
  `risk_assessment`, `confidence`. *(this is the LLM's seat — on the pod you hand-write it)*

### ✍️ Optional challenge — write them yourself
Edit `labs/lab3_wire_your_own_specialist/starter/agent_yourname.py`, fill the two
`# TODO:` methods, and run `make lab3-test` until green. The docstrings tell you the exact
contract. *(Tip: the filename must stay `agent_yourname.py` — that's what the tests load.)*

---

## Step 3 — Wire it in & see YOUR card
Your specialist runs as the 6th container (`ws-c2-your-agent`). Put your fingerprint on it
and rebuild — full steps in **[`VERIFY_FIRE_AND_CARD.md`](./VERIFY_FIRE_AND_CARD.md)**. The short version:
```
cd ~/autocon5-ws-c2-from-alert-to-action
sed -i 's/Voice-priority child-policy/[diagnosed by YOUR-NAME] Voice-priority child-policy/' services/your-agent/main.py
docker compose up -d --build your-agent
curl -s -X POST localhost:8001/incident/trigger -H 'X-MCP-API-Key: dev-key-123' -H 'Content-Type: application/json' -d '{"scenario_id":"qos_interface_congested","device_id":"router-1"}'
curl -s localhost:8002/acp/approvals | python3 -m json.tool
```
The card's `specialist` is `your_specialist`, with your fingerprint in the root cause.

---

## What you learned
- A specialist is **two functions**: `classify` (routing) + `diagnose` (reasoning).
  Everything around them — the agent loop, A2A messaging, the approval gate — is provided.
- TDD on agents = TDD on functions: the loop is just `while True: await receive()` around
  your two methods.
- Extending this system to a whole new class of fault = writing two functions. It is not a
  black box.
