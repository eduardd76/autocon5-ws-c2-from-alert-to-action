#!/usr/bin/env python3
"""Babysitting validator for a Lab-3 scenario YAML — friendly errors, never cryptic."""
import sys, re
try:
    import yaml
except ImportError:
    print("Need pyyaml:  pip3 install pyyaml"); sys.exit(2)
def err(m): print("  ❌ " + m)
def ok(m):  print("  ✅ " + m)
def main():
    if len(sys.argv) < 2:
        print("usage: python3 lab_scenarios/validate.py lab_scenarios/mine/<you>.yaml"); sys.exit(2)
    p = sys.argv[1]
    try:
        doc = yaml.safe_load(open(p, encoding="utf-8")) or {}
    except Exception as e:
        err(f"YAML won't parse: {e}"); sys.exit(1)
    print(f"Validating {p} ...")
    n = 0
    sid = doc.get("scenario_id") or doc.get("id")
    if not sid: err("missing scenario_id"); n += 1
    elif not re.fullmatch(r"[a-z0-9_]+", str(sid)): err(f"scenario_id '{sid}' must be lower_snake_case (a-z 0-9 _ only)"); n += 1
    elif sid == "my_fault_id": err("scenario_id is still the placeholder 'my_fault_id' — rename it"); n += 1
    else: ok(f"scenario_id = {sid}")
    for k in ("title", "root_cause"):
        if not str(doc.get(k, "")).strip(): err(f"missing/empty {k}"); n += 1
    trig = doc.get("trigger") or {}
    pat = trig.get("syslog_pattern")
    if not pat: err("trigger.syslog_pattern missing"); n += 1
    else:
        try: re.compile(pat); ok(f"syslog_pattern compiles: {pat}")
        except re.error as e: err(f"syslog_pattern is not valid regex: {e}"); n += 1
    if not trig.get("example_message"): err("trigger.example_message missing (the log line that fires it)"); n += 1
    fix = doc.get("proposed_fix") or {}
    if not fix.get("commands"): err("proposed_fix.commands is empty — what is the fix?"); n += 1
    else: ok(f"{len(fix['commands'])} fix command(s)")
    try:
        c = float(doc.get("confidence"))
        if not 0 <= c <= 1: err("confidence must be 0.0-1.0"); n += 1
        else: ok(f"confidence = {c}")
    except Exception: err("confidence must be a number 0.0-1.0"); n += 1
    auth = ((doc.get("provenance") or {}).get("author") or "")
    if not auth or "you@" in auth: print("  ⚠️  provenance.author not set to your email (optional — but it's your name on the brain)")
    else: ok(f"author = {auth}")
    print()
    if n == 0:
        print(f"\U0001f389 VALID.  Now load + fire it:\n   make fire-mine SCN={sid}"); sys.exit(0)
    print(f"Found {n} thing(s) to fix above. Edit the file and run me again."); sys.exit(1)
if __name__ == "__main__": main()
