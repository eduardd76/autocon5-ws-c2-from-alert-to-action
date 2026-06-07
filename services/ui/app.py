"""
Streamlit UI — workshop attendee view.

Production UI (ui/app.py, ~1300 lines) has SSE streaming, KG graph viz, audit-chain
explorer, multi-tab approval workflow. This is the minimal version: one page,
auto-refresh every 3s, four panels:
  1. Queue depths (live)
  2. Trigger incident (3 buttons)
  3. Pending approvals
  4. History (approved / rejected)
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime

import httpx
import streamlit as st

TEAM_LEADER_URL = os.getenv("TEAM_LEADER_URL", "http://team-leader:8002").rstrip("/")
MCP_URL = os.getenv("MCP_URL", "http://mcp-server:8000").rstrip("/")
MCP_API_KEY = os.getenv("MCP_API_KEY", "dev-key-123")


st.set_page_config(
    page_title="AutoCon5 WS:C2 — From Alert to Action",
    page_icon="🌐",
    layout="wide",
)

st.title("AutoCon5 WS:C2 — From Alert to Action")
st.caption("5-agent NetOps dream team — laptop edition. Mock devices, canned LLM, "
           "everything else is the same protocol as production.")

# ---- Sidebar: trigger panel --------------------------------------------

st.sidebar.header("Lab 1: Trigger an incident")
scenarios = [
    ("ospf_neighbor_down", "router-1", "OSPF adjacency down (Cisco)"),
    ("bgp_session_idle",   "router-1", "BGP idle / ACL block (Cisco)"),
    ("evpn_route_missing", "leaf-1",   "EVPN Type-2 missing (Arista EOS)"),
]

with st.sidebar:
    for sid, dev, label in scenarios:
        if st.button(label, key=f"btn_{sid}", use_container_width=True):
            try:
                r = httpx.post(
                    f"{MCP_URL}/incident/trigger",
                    json={"scenario_id": sid, "device_id": dev},
                    headers={"X-MCP-API-Key": MCP_API_KEY},
                    timeout=5.0,
                )
                if r.status_code == 200:
                    st.success(f"triggered: {sid}")
                else:
                    st.error(f"trigger failed: {r.status_code} {r.text}")
            except Exception as e:
                st.error(f"trigger error: {e}")
            time.sleep(0.5)
            st.rerun()

    st.divider()
    st.subheader("Lab 3: Fire YOUR scenario")
    try:
        _sc = httpx.get(f"{MCP_URL}/scenarios", headers={"X-MCP-API-Key": MCP_API_KEY}, timeout=3.0).json().get("scenarios", [])
    except Exception:
        _sc = []
    _ids = [s2["scenario_id"] for s2 in _sc]
    if _ids:
        _pick = st.selectbox("scenario_id (live catalogue)", _ids, key="lab3pick")
        _dev = st.text_input("device_id", value="router-1", key="lab3dev")
        if st.button("🔥 Fire this scenario", key="lab3fire", use_container_width=True):
            try:
                _r = httpx.post(f"{MCP_URL}/incident/trigger", json={"scenario_id": _pick, "device_id": _dev}, headers={"X-MCP-API-Key": MCP_API_KEY}, timeout=5.0)
                st.success(f"fired: {_pick}") if _r.status_code == 200 else st.error(f"fail: {_r.text}")
            except Exception as _e:
                st.error(f"error: {_e}")
            time.sleep(0.5); st.rerun()
    else:
        st.caption("No scenarios loaded.")

    st.divider()
    st.caption("Health")
    try:
        h_mcp = httpx.get(f"{MCP_URL}/health", timeout=2.0).status_code == 200
    except Exception:
        h_mcp = False
    try:
        h_tl = httpx.get(f"{TEAM_LEADER_URL}/acp/health", timeout=2.0).status_code == 200
    except Exception:
        h_tl = False
    st.write(f"MCP server: {'✅' if h_mcp else '❌'}")
    st.write(f"Team Leader: {'✅' if h_tl else '❌'}")

    st.divider()
    auto = st.checkbox("Auto-refresh (3s)", value=True)


# ---- Main: queue depths -----------------------------------------------

try:
    q = httpx.get(f"{TEAM_LEADER_URL}/acp/queues", timeout=3.0).json()
except Exception as e:
    q = {}
    st.warning(f"team-leader unreachable: {e}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("incident_queue", q.get("incident_queue", "?"))
c2.metric("specialist inbox", q.get("a2a_stability_specialist_inbox", "?"))
c3.metric("pending approvals", q.get("approval_queue", "?"))
c4.metric("approved history", q.get("approved_history", "?"))


# ---- Pending approvals -----------------------------------------------

st.subheader("Pending approvals")
try:
    approvals = httpx.get(f"{TEAM_LEADER_URL}/acp/approvals", timeout=3.0).json()
except Exception as e:
    approvals = []
    st.error(f"failed to load approvals: {e}")

if not approvals:
    st.info("No pending approvals. Trigger an incident from the sidebar.")
else:
    for a in approvals:
        with st.expander(
            f"🟡 {a.get('scenario_id', '?')} on {a.get('device_id', '?')} — "
            f"confidence {int((a.get('confidence') or 0) * 100)}% — "
            f"task {a.get('task_id', '?')}",
            expanded=True,
        ):
            cc1, cc2 = st.columns([3, 1])
            with cc1:
                st.markdown(f"**Specialist:** `{a.get('specialist')}`")
                st.markdown(f"**Root cause:** {a.get('root_cause')}")
                if a.get("authored_by"):
                    st.markdown(f"**Authored by:** `{a.get('authored_by')}` 🧠 *(your scenario drove this)*")
                st.markdown(f"**Risk:** `{a.get('risk_assessment')}`")
                st.markdown("**Evidence:**")
                for e in a.get("evidence", []):
                    st.markdown(f"- {e}")
                pf = a.get("proposed_fix", {})
                if pf.get("commands"):
                    st.markdown("**Proposed fix:**")
                    st.code("\n".join(pf["commands"]), language="text")
                if pf.get("rollback"):
                    st.markdown("**Rollback:**")
                    st.code("\n".join(pf["rollback"]), language="text")
            with cc2:
                if st.button("✅ Approve", key=f"app_{a['task_id']}"):
                    httpx.post(
                        f"{TEAM_LEADER_URL}/acp/approval",
                        json={"action": "approve", "task_id": a["task_id"],
                              "decision_rationale": "workshop attendee approved"},
                        timeout=5.0,
                    )
                    st.rerun()
                if st.button("❌ Reject", key=f"rej_{a['task_id']}"):
                    httpx.post(
                        f"{TEAM_LEADER_URL}/acp/approval",
                        json={"action": "reject", "task_id": a["task_id"],
                              "decision_rationale": "workshop attendee rejected"},
                        timeout=5.0,
                    )
                    st.rerun()


# ---- History ----------------------------------------------------------

st.subheader("History")
try:
    hist = httpx.get(f"{TEAM_LEADER_URL}/acp/history", timeout=3.0).json()
except Exception:
    hist = {"approved": [], "rejected": []}

th1, th2 = st.columns(2)
with th1:
    st.markdown(f"**✅ Approved ({len(hist.get('approved', []))})**")
    for a in hist.get("approved", [])[:10]:
        st.caption(f"`{a.get('task_id')}` {a.get('scenario_id')} — {a.get('decided_at', '')[:19]}")
with th2:
    st.markdown(f"**❌ Rejected ({len(hist.get('rejected', []))})**")
    for a in hist.get("rejected", [])[:10]:
        st.caption(f"`{a.get('task_id')}` {a.get('scenario_id')} — {a.get('decided_at', '')[:19]}")

st.divider()
st.caption(f"Last refresh: {datetime.now().strftime('%H:%M:%S')}")

if auto:
    time.sleep(3)
    st.rerun()
