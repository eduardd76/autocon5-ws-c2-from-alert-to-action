# Lab 3 — Reference Solution

This is what `starter/agent_yourname.py` should look like when all 4 tests pass. Don't open this until you've spent at least 15 min trying.

The file `agent_qos.py` here is a drop-in replacement: copy it over `starter/agent_yourname.py` (and rename the file/class accordingly) and the tests pass.

The presenter will walk through this code in the last 10 min of the workshop.

## What the solution shows

1. **`classify()` as a 6-line function.** Keyword match + scenario set. That's it. The production version (~30 lines) adds catalogue lookup + KG-aided routing, but the core pattern is the same.

2. **`diagnose()` as a dict lookup with a graceful fallback.** Production replaces the dict with an LLM call to a fine-tuned 7B model, but the shape of the returned envelope is identical to what you wrote — every specialist in the production stack returns these 5 keys (`root_cause`, `evidence`, `proposed_fix`, `risk_assessment`, `confidence`).

3. **No protocol code, no Redis code, no MCP code in the specialist.** All of that lives outside the specialist class (in the agent runner). Your specialist is testable in isolation with pure unit tests. That's why the tests don't need Docker.

## Wiring it into the running stack (optional Step 4)

To make your specialist actually receive live Team Leader delegations — and run **your**
`diagnose()` on a real triggered incident — follow **[`../WIRING_GUIDE.md`](../WIRING_GUIDE.md)**.

That guide is the single source of truth: it ships a ready runner (`../wiring/`) that wraps your
two methods in the A2A loop, plus the exact 5 edits (route in the Team Leader, add the container,
add a trigger). Everything uses the role that already exists in the enum —
**`AgentRole.YOUR_SPECIALIST` (`"your_specialist"`)**. The inbox (`a2a_your_specialist_inbox`) is
derived from that role name automatically, so keep it consistent on both sides.

> Note: an earlier version of this file said to rename the role to `QOS_SPECIALIST` and to add a
> *canned stub-LLM response*. Both are superseded by the guide — you keep `YOUR_SPECIALIST`, and the
> runner calls **your** `diagnose()` directly (no stub), so the card you see is genuinely your code.

It's the same 5-step shape that adds any new specialist to the production stack.
