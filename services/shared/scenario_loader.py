"""Lab scenario catalogue loader — the Single Source of Truth (SSOT).

Reads every *.yaml in $SCENARIOS_DIR (default /app/lab_scenarios) and returns a
dict keyed by scenario_id. The stub LLM, the Team Leader router and the MCP
syslog generator ALL read THIS one place — change a YAML and every layer
updates. Hot-reload: re-reads automatically when any file's mtime changes
(no container restart needed). Files whose names start with '_' are skipped
(so _TEMPLATE.yaml is never loaded as a scenario).
"""
from __future__ import annotations
import glob, os
from typing import Any

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None

SCN_DIR = os.getenv("SCENARIOS_DIR", "/app/lab_scenarios")
_cache: dict[str, Any] = {"sig": None, "data": {}}

def _files() -> list[str]:
    pats = [os.path.join(SCN_DIR, "**", "*.yaml"), os.path.join(SCN_DIR, "**", "*.yml")]
    out: list[str] = []
    for p in pats:
        out += glob.glob(p, recursive=True)
    return [f for f in out if not os.path.basename(f).startswith("_")]

def _sig():
    try:
        return tuple(sorted((f, os.path.getmtime(f)) for f in _files()))
    except Exception:
        return None

def load_scenarios(force: bool = False) -> dict[str, dict]:
    if yaml is None:
        return {}
    sig = _sig()
    if force or sig != _cache["sig"]:
        data: dict[str, dict] = {}
        for f in _files():
            try:
                doc = yaml.safe_load(open(f, encoding="utf-8")) or {}
            except Exception as e:
                print(f"[scenario_loader] SKIP {f}: {e}")
                continue
            sid = doc.get("scenario_id") or doc.get("id")
            if sid:
                doc["_source_file"] = os.path.relpath(f, SCN_DIR)
                data[sid] = doc
        _cache["sig"] = sig
        _cache["data"] = data
        print(f"[scenario_loader] {len(data)} scenarios from {SCN_DIR}: {sorted(data)}")
    return _cache["data"]

def get_scenario(scenario_id: str | None) -> dict | None:
    if not scenario_id:
        return None
    return load_scenarios().get(scenario_id)
