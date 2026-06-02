# Lab 2 — Multi-Vendor EVPN Audit

## The idea — read this first (1 min)

Lab 1 used a Cisco fault. This lab fires the *same kind* of incident on an **Arista** switch — different vendor, different CLI, different syntax — and the **agent code does not change at all**. That's the whole point.

Why it works: the agent never reads raw vendor CLI. The **tool layer** (the MCP server) translates each vendor's output into one *neutral* picture, and the agent reasons over that neutral picture. Swap the vendor, swap the translator — the brain stays the same.

Watch for:
- **The adapter is the only vendor-aware part.** Everything above it (the agent, the loop, the diagnosis) is vendor-agnostic — which is how you cover Cisco + Arista with one set of agents.
- **Tools are where the loop touches the world** — and each tool here is narrow and read-only, so the blast radius is "read some state," nothing more.

**NOC analogy:** your on-call engineer doesn't memorise every vendor's CLI — they read a normalised report. A per-vendor "translator" speaks each dialect so the engineer doesn't have to.

---

**Time:** 30 minutes, self-paced.
**Goal:** See the same agent pattern handle an Arista EOS EVPN fault that looks nothing like Cisco IOS — without changing any agent code.

---

## What this lab demonstrates

In Lab 1 you watched the Stability Specialist diagnose a Cisco BGP fault. The same specialist now handles an **EVPN Type-2 route missing** on an Arista EOS leaf switch. Different vendor, different syntax, different CLI — but the agent + protocol layer doesn't care, because the **vendor-specific knowledge lives in the MCP server's adapter** (Layer 4), not in the agent.

This is the "vendor abstraction" idea from the workshop slides: agents reason over **neutral schema**, adapters translate vendor CLI to/from that schema.

---

## Step 1 — Verify the stack is up

```bash
docker compose ps         # all 5 should be Up
```

If you tore down at end of Lab 1:

```bash
docker compose up -d
sleep 15
```

---

## Step 2 — Trigger the EVPN scenario

In the UI sidebar, click **"EVPN Type-2 missing (Arista EOS)"**.

You should see (~3 seconds later) a new approval card. The vendor changes — `leaf-1` is `arista-eos`, not `cisco-ios`.

Examine the card:
- **Root cause:** EVPN Type-2 route for MAC `aa:bb:cc:dd:ee:ff` missing on Arista leaf-1 — RT import mismatch
- **Evidence:** 3 facts including the asymmetric import (VRF tenant-a imports `65000:200`, peer advertises `65000:100`)
- **Proposed fix:** Arista EOS-style EVPN CLI:
  ```
  router bgp 65000
  vrf tenant-a
  route-target import evpn 65000:100
  ```
- **Confidence:** 94%

---

## Step 3 — Inspect the MCP response

Same MCP tool name (`ospf_parser`), different vendor:

```bash
curl -s -X POST http://localhost:8001/tools/ospf_parser \
  -H "X-MCP-API-Key: dev-key-123" \
  -H "Content-Type: application/json" \
  -d '{"device_id":"leaf-1"}' | python3 -m json.tool
```

Notice the `vendor: arista-eos` field. In production this is what selects the right CLI-to-neutral-schema adapter. The agent never knows what raw CLI looked like — it just gets the structured `neighbors` list.

---

## Step 4 — Look at the agent code paths

Open `services/stability-agent/main.py`. The `process()` method is **vendor-agnostic**:

```python
evidence["ospf"] = (await self.mcp.ospf_parser(device_id)).get("data", {})
```

It doesn't ask "is this Cisco or Arista?" — it just calls the tool by name. The MCP server (Layer 4) routes to the right adapter based on the device's `vendor` field. This is the production pattern, identical here.

In the production repo (`agentic-netops-mvp/mcp-server/adapters/`) you'll find:
- `cisco_nxos_adapter.py` — NX-OS CLI -> neutral schema
- `arista_eos_adapter.py` — Arista EOS CLI -> neutral schema
- `n9kv_adapter.py` — Nexus 9000v -> neutral schema

For the laptop lab we use a single in-memory mock state per device, but the principle is the same.

---

## Step 5 — Try the Fabric Architect simulation

In the production stack, the "Fabric Architect" agent runs **proactive audits** across all leaves in a DC fabric — it doesn't wait for a syslog. For the workshop we approximate this with a one-shot script.

```bash
# from the repo root
curl -s -X POST http://localhost:8001/incident/trigger \
  -H "X-MCP-API-Key: dev-key-123" \
  -H "Content-Type: application/json" \
  -d '{"scenario_id":"evpn_route_missing","device_id":"leaf-1"}'
```

Refresh the UI — you'll see the same approval card appear. This is the curl equivalent of the sidebar button (production also exposes this for CI/CD pipelines).

---

## Discuss with your neighbor (2 min)

Two questions to chew on:

1. **What would change** in the system if you added a 4th vendor (say, Juniper)? Hint: which layer?
2. **What stays the same?** Hint: the Streamlit UI? The Team Leader's classify()? The A2A protocol?

The answer matters because it's the whole reason for the 5-layer architecture: the parts most likely to change (vendor CLI quirks) are isolated to one place, and the parts most likely to be reused (agent reasoning) are vendor-agnostic.

---

## Bonus (5 min, optional)

Open `services/mcp-server/main.py` and look at `MOCK_DEVICE_STATE`. Add a new device `leaf-3` with `vendor: juniper-junos` and a different EVPN route set. Restart the MCP server:

```bash
docker compose restart mcp-server
```

Then trigger an incident against it:

```bash
curl -X POST http://localhost:8001/incident/trigger \
  -H "X-MCP-API-Key: dev-key-123" \
  -d '{"scenario_id":"evpn_route_missing","device_id":"leaf-3"}'
```

You've simulated adding a vendor without touching agent code. That's the point.

---

## Done

You've seen the same agent pattern handle 3 vendors via the MCP adapter abstraction. Move to **Lab 3** when ready.
