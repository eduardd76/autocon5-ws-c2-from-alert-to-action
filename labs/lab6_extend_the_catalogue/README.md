# Lab 6 — Extend the brain (the catalogue)

**The brain is the catalogue, not a model.** On your pod there is *no live LLM* — the
agent's diagnosis comes from a YAML file in `lab_scenarios/`. Each file is one fault,
and it drives **everything**: the syslog that fires it → which specialist owns it →
the root cause + fix on the card → the author's name. **Add a fault = add a file.**

> That's *Institutional Memory as Code*: your 2 a.m. expertise, written down once as
> peer-reviewed YAML, then run 24/7 by the agents — with your name on it.

You're SSH'd into your pod, in the repo root:
```
cd ~/autocon5-ws-c2-from-alert-to-action
```

---

## Step 1 — See the brain that's been running the whole time
```
ls lab_scenarios/
cat lab_scenarios/bgp_session_idle.yaml
```
Notice: `owner_specialist` (routing), `trigger.example_message` (detection),
`root_cause` / `proposed_fix` (the card), `provenance.author`. One file, every layer.

## Step 2 — Add YOUR entry (copy a real one, make it yours)
No editor needed — copy an example and change the key fields with `sed`:
```
cp lab_scenarios/examples/bgp_flap_after_maintenance.yaml lab_scenarios/mine/my_first_fault.yaml

sed -i 's/^scenario_id:.*/scenario_id: my_first_fault/'                 lab_scenarios/mine/my_first_fault.yaml
sed -i 's/^title:.*/title: "My first catalogue entry"/'                 lab_scenarios/mine/my_first_fault.yaml
sed -i 's|author:.*|author: you@yourcompany.com|'                       lab_scenarios/mine/my_first_fault.yaml
```
*(Want it to be truly your fault? Also `sed` the `root_cause:` line — one sentence in
your words. Or `cat lab_scenarios/_TEMPLATE.yaml` to author one from scratch.)*

Check what you wrote:
```
cat lab_scenarios/mine/my_first_fault.yaml
```

## Step 3 — Validate it (the babysitting validator)
```
python3 lab_scenarios/validate.py lab_scenarios/mine/my_first_fault.yaml
```
It tells you exactly what's wrong if a field is missing or the regex won't compile —
nobody gets stuck.

## Step 4 — Watch it appear in the brain (no restart — hot reload)
```
curl -s localhost:8001/scenarios | python3 -m json.tool
```
Your `my_first_fault` is now in the catalogue. You didn't restart anything — the loader
re-read the folder the moment you saved the file.

## Step 5 — Fire YOUR fault
```
curl -s -X POST localhost:8001/incident/trigger -H 'X-MCP-API-Key: dev-key-123' -H 'Content-Type: application/json' -d '{"scenario_id":"my_first_fault","device_id":"router-1"}'
```

## Step 6 — See your card (your knowledge, your name)
```
curl -s localhost:8002/acp/approvals | python3 -m json.tool
```
…or open the UI. The card's `root_cause`/fix is what **you** wrote, and
`authored_by` is **your email**. The Team Leader routed it, the agent presented it —
but the knowledge is yours.

---

## What just happened (the whole thesis)
- The "AI" decided nothing — **your YAML did.** The LLM on the pod is a stub; the
  catalogue is the brain.
- One file changed detection, routing, diagnosis, and the card — **the Single Source
  of Truth.**
- It's reviewable (it's just YAML in git), versioned, and attributable to you.

**That is how tribal knowledge becomes an executable, peer-reviewed asset.** Stretch:
open a PR with your scenario to share it with the room.
