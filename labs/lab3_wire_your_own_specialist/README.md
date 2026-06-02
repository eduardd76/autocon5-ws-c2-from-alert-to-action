# Lab 3 — Wire Your Own Specialist Agent

## The idea — read this first (2 min)

In Labs 1 & 2 you *watched* the AI team diagnose faults. In Lab 3 **you add your own member to that team** — and you discover the trick: an "AI specialist" here is really just **two small functions** you write. Everything else (the messaging between agents, the AI model, the dashboard, the approval card) is plumbing that already exists and that you never touch.

**A NOC analogy:** the system is an on-call team. The *Team Leader* is the dispatcher; each *specialist agent* is an on-call engineer for one domain (routing, security, …). Right now nobody covers **QoS**. In this lab you "onboard" a QoS engineer by writing down just two things:

- **`classify()`** — *"Is this ticket mine?"* → yes / no
- **`diagnose()`** — *"Here's the root cause, the fix, and how confident I am."*

From then on, the dispatcher automatically routes QoS incidents to your new specialist. You didn't rewire anything — you just added a job description.

**What you'll do:** write those two functions until 4 tests go from red ❌ to green ✅; then (optional) plug your specialist into the live system and watch *your own code* produce a real approval card.

**What you'll walk away with:** a working specialist you built — and the realisation that extending this system to a whole new class of fault means *writing two functions*. That's the entire point: it is not a black box.

> **New to AI agents?** You need zero AI background for this. If you can read and edit a Python function, you can do this lab. The networking judgement is the hard part — and you already have that.

> **Read a stricter definition of "agent" (e.g. "Agents for Network Engineers")?** You're right that an *agent* is the whole while-loop + tools + memory + planning + guardrails. That full apparatus is *already built here* — the runner loop, the A2A messaging, the deterministic catalogue-confirm, the per-action approval gate. What you write in this lab is the one piece that book calls genuinely new: **the decision the loop delegates** (`classify` + `diagnose`). You're writing the brain; the bounded system around it — where the safety lives — is provided. This lab *is* that thesis, hands-on.

---

**Time:** 75 minutes, self-paced.
**Goal:** Implement a brand-new specialist agent — `QoSSpecialist` — that diagnoses QoS misconfiguration. Pass 4 TDD tests. Optionally hook it into the running stack and watch the UI route real incidents to it.

This is the lab you came for. It's the abstract's commitment: "participants extend the system by wiring a custom specialist agent using provided scaffolding."

---

## What you'll build

A new agent class with two methods:

```python
class QoSSpecialist:
    def classify(self, incident: dict) -> bool:
        """Return True if this is a QoS incident we should handle."""
        ...

    async def diagnose(self, incident: dict) -> dict:
        """Return root cause + proposed fix for the QoS incident."""
        ...
```

A scenario YAML that describes the new "QoS interface congested" fault. Four unit tests that are red until your implementation is correct.

---

## Setup (1 min, do this first)

```bash
cd labs/lab3_wire_your_own_specialist
python3 -m venv .venv
source .venv/bin/activate          # macOS / linux
# source .venv/Scripts/activate     # windows
pip install -q pytest pyyaml
```

If you don't have python3 on the host:

```bash
# fallback: run pytest in a throwaway container (slower)
docker run --rm -it -v "$PWD:/work" -w /work python:3.11-slim \
  sh -c "pip install -q pytest pyyaml && python -m pytest starter/test_my_specialist.py -v"
```

---

## Step 1 — Run the tests. Watch them fail.

```bash
python -m pytest starter/test_my_specialist.py -v
```

Expected: **4 tests, 4 failures.** This is TDD red. Your job is to make them green.

```
FAILED test_classify_recognizes_qos_keywords
FAILED test_classify_rejects_non_qos
FAILED test_diagnose_returns_expected_shape
FAILED test_diagnose_for_known_scenario_returns_high_confidence
```

---

## Step 2 — Open the scaffolding

```bash
$EDITOR starter/agent_yourname.py
```

Find the two `# TODO:` markers in `QoSSpecialist`. Read the docstrings — they tell you the exact contract the tests expect.

Hints (don't peek unless stuck):

<details>
<summary>Hint for classify()</summary>

The test passes incidents whose `raw_message` contains "qos", "policy-map", "shaping", or "congestion". Lowercase + substring match is enough.

</details>

<details>
<summary>Hint for diagnose()</summary>

Return a dict with these keys: `root_cause` (str), `evidence` (list of str), `proposed_fix` (dict with `commands` + `rollback` lists of str), `risk_assessment` (one of "low"/"medium"/"high"), `confidence` (float 0..1).

For the `qos_interface_congested` scenario, return something believable about a policy-map drop rate. The test only checks shape + that confidence > 0.7 for known scenarios.

</details>

---

## Step 3 — Iterate red -> green

Rerun the tests after each edit:

```bash
python -m pytest starter/test_my_specialist.py -v
```

Aim for all 4 passing. Typical solve time: 15–25 minutes if you're new, 5–10 minutes if you've done TDD before.

When you see:

```
4 passed in 0.04s
```

**Take a screenshot. Show your neighbor.** This is the moment.

---

## Step 4 (optional, ~15 min) — Wire your specialist into the running stack

So far your specialist exists only as a class with passing tests. To actually let the Team Leader
delegate live incidents to it — and watch the approval card come from **your** `diagnose()` — follow
the step-by-step **[`WIRING_GUIDE.md`](./WIRING_GUIDE.md)**.

It ships a ready runner (`wiring/`) that wraps your two methods in the A2A loop, plus the exact 5
edits and a diagram of where your agent slots in. All of it uses the role already in the enum —
`AgentRole.YOUR_SPECIALIST` (`"your_specialist"`); the inbox `a2a_your_specialist_inbox` is derived
from that name automatically.

The TL;DR of the 5 edits:
1. `cp -r wiring services/your-agent` and paste your two methods into `main.py`.
2. (`AgentRole.YOUR_SPECIALIST` already exists — no edit.)
3. Add a QoS keyword branch to Team Leader's `classify()` → `AgentRole.YOUR_SPECIALIST`.
4. Add a `your-agent` service to `docker-compose.yml` (copy the `stability-agent` block).
5. Add a `qos_interface_congested` trigger (UI button + one `_scenario_to_syslog` line).

Then `docker compose up -d --build` and click the new button. Or watch the presenter show this on
screen during the wrap-up.

---

## Step 5 (bonus, ~10 min) — Add a scenario to the catalogue

Edit `starter/scenario.yaml`. Add a second QoS scenario (e.g. `qos_class_starvation`). Add a matching canned response to `CANNED` in `services/shared/stub_llm_client.py`. Add a 5th test that exercises it. Make it pass.

This is the pattern by which the production system grows from 3 scenarios to 100+: scenario YAML + canned LLM response + matching test.

---

## What you've learned

- The specialist contract is two methods: `classify` + `diagnose`. Everything else is plumbing.
- TDD on agents is the same as TDD on functions — the agent loop is just a `while True: await receive()` wrapper around your two methods.
- Adding a new specialist to the production system follows the exact pattern you just did. The repo `agentic-netops-mvp/agents/<new>/agent_a2a.py` follows the same shape (more bells and whistles: KG queries, DT validation, verifiability chain emission — none of which are *required* to ship a working specialist).

---

## If you're stuck

Hand-raise + flag your laptop with the red sticky note. Or post in `#autocon5-ws-c2` on NAF Slack.

If you only have 5 min left: copy `solution/agent_qos.py` over your `starter/agent_yourname.py`, run the tests, see them pass, and read the diff to understand what you would have written.
