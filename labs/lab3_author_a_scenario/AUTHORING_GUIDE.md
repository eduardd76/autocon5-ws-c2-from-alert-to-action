# Authoring Guide — field by field

A scenario YAML has two halves: **the trigger** (how the fault is detected + routed) and
**the diagnosis** (what the agent presents). Here's every field.

| Field | What it is | Example |
|---|---|---|
| `scenario_id` | unique id, `lower_snake_case` | `vrrp_master_flap` |
| `title` | one human-readable line | `"VRRP master flapping"` |
| `owner_specialist` | who handles it (keep `stability_specialist` on the laptop) | `stability_specialist` |
| `severity` | `info` / `warning` / `critical` | `warning` |
| `trigger.syslog_pattern` | the Cisco/Arista facility that fires it (a regex) | `'%VRRP-6-STATECHANGE'` |
| `trigger.example_message` | the exact log line; `{device}` = hostname | `"%VRRP-6-STATECHANGE: Vl10 Grp 1 Master->Backup on {device}"` |
| `root_cause` | ONE clear sentence: what's actually wrong | `"VRRP priority tie + preempt → master flaps"` |
| `evidence` | 2–3 show-command findings that prove it | `["show vrrp brief: prio 100 both", ...]` |
| `proposed_fix.commands` | the fix, in order | `["interface Vlan10", "vrrp 1 priority 120"]` |
| `proposed_fix.rollback` | how to undo it | `["interface Vlan10", "no vrrp 1 priority"]` |
| `risk_assessment` | `low` / `medium` / `high` | `low` |
| `confidence` | 0.0–1.0, how sure the diagnosis is | `0.9` |
| `provenance.author` | **your work email** | `you@yourcompany.com` |

### Worked example
See `lab_scenarios/examples/bgp_flap_after_maintenance.yaml` — a complete, valid scenario you
can copy and tweak.

### Common validator messages (and the fix)
- *"scenario_id must be lower_snake_case"* → no spaces/caps; use `_`.
- *"syslog_pattern is not valid regex"* → escape special chars, or keep it simple (`%FAC-5-MNEMONIC`).
- *"proposed_fix.commands is empty"* → add at least one fix command.
- *"still the placeholder 'my_fault_id'"* → rename `scenario_id`.

### Why this is the whole product
In production the same YAML lives in a `git` catalogue (≈76 today). A senior writes it once;
CI validates it; a peer reviews the PR; the agents hot-load it. The fine-tuned model produces
the diagnosis at runtime — but **grounded by your entry**, so it can't wander. You just did
the core motion of extending the system: *no code, just knowledge.*
