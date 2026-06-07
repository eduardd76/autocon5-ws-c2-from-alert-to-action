# Lab 3 — Author Your Own Scenario (teach the system YOUR 2 a.m. fault)

## The idea — read this first (2 min)
In Labs 1 & 2 you *watched* the AI team work. Now **you add knowledge to it** — and you'll
see the trick: a "scenario" is just **one YAML file**. When you load it, that single file
drives **detection → routing → the agent's diagnosis → the approval card**. Nothing else
changes. That is the whole thesis, in your hands:

> **The catalogue is the brain. The agents are the runtime. Add a fault = add a file.**
> This is *Institutional Memory as Code* — your 2 a.m. know-how, written down once, attributable, and run 24/7.

**You need zero coding.** If you can write a syslog pattern and a fix, you can do this — and
that judgement is the hard part, which you already have.

> **Honest note:** on your laptop the LLM is a *stub*, so in this lab **you also write the
> expected diagnosis** (root cause + fix) in the YAML. In production the fine-tuned model
> writes that diagnosis — *grounded by this same catalogue entry*. Either way, the catalogue
> is what's in control.

**Time:** ~25 min (a 12-min express path exists below).

---

## Step 1 — Copy the template (30s)
```bash
cp lab_scenarios/_TEMPLATE.yaml lab_scenarios/mine/$(whoami).yaml
```
Open `lab_scenarios/mine/<you>.yaml` in the editor (browser code-editor on the pod, or any text editor).

## Step 2 — Fill it in (10 min) — a fault from YOUR ops life
Fill every line marked `<-- FILL`. The big ones:
- `scenario_id` — unique, `lower_snake_case` (e.g. `vrrp_master_flap`)
- `trigger.syslog_pattern` — the facility that fires it (e.g. `%VRRP-6-STATECHANGE`)
- `trigger.example_message` — the exact log line (use `{device}` where the hostname goes)
- `root_cause` — one clear sentence
- `proposed_fix.commands` / `rollback` — the fix, and how to undo it
- `provenance.author` — **your work email** (your name on the brain)

Keep `owner_specialist: stability_specialist` (the only specialist running on the laptop).
See **AUTHORING_GUIDE.md** for a field-by-field walkthrough + a worked example.

## Step 3 — Validate (30s) — the validator babysits you
```bash
make validate-mine F=lab_scenarios/mine/<you>.yaml
```
It tells you in plain English exactly what to fix until you see **🎉 VALID**.

## Step 4 — Fire it and watch YOUR scenario drive the team (2 min)
The catalogue **hot-reloads** — no restart. Fire it:
- **In the UI** (easiest): sidebar → *Lab 3: Fire YOUR scenario* → pick your `scenario_id` → **🔥 Fire**.
- **Or CLI:** `make fire-mine SCN=<your_scenario_id>`

Then open **Pending approvals**: there's a card with **YOUR root cause, YOUR fix, and `Authored by: <your email> 🧠`**. You taught the system a fault — and it ran your knowledge end-to-end.

## Step 5 (stretch, 5 min) — open a Pull Request
Commit your scenario and open a PR against the repo — that's exactly how knowledge enters the
production catalogue: authored, peer-reviewed, version-controlled, run forever.
```bash
git checkout -b scenario/<your_scenario_id>
git add lab_scenarios/mine/<you>.yaml && git commit -m "scenario: <your_scenario_id>"
# push to your fork and open a PR
```

---

## ⏱ Express path (12 min, for a slow laptop / short on time)
```bash
cp lab_scenarios/examples/bgp_flap_after_maintenance.yaml lab_scenarios/mine/$(whoami).yaml
# change just: scenario_id, provenance.author, and one word of root_cause
make validate-mine F=lab_scenarios/mine/$(whoami).yaml
make fire-mine SCN=<your new scenario_id>
```

## Want to go deeper? (take-home)
`labs/lab3_wire_your_own_specialist/` is the **advanced** track: write the specialist's
`classify()` + `diagnose()` in Python and pass 4 TDD tests. Same thesis, code-level. Do it on
the plane home.
