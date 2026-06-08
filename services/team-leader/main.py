"""
Team Leader Agent — stripped attendee version.

Production (~1000 lines, agents/team_leader/agent_acp_a2a.py) has full ACP
server + RAG over scenario catalogue + KG queries + ReAct loop. This is the
minimal version: poll incident_queue, classify, delegate to one specialist,
push the response to approval_queue.

Two HTTP endpoints:
  GET  /acp/health
  GET  /acp/queues          (returns Redis queue lengths for the UI)
  POST /acp/approval        (UI -> "approve" / "reject" a recommendation)
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import redis.asyncio as redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

sys.path.insert(0, "/app")  # so we can import shared.*
from shared.a2a_protocol import A2AChannel, AgentRole, MessageType  # noqa: E402


REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
INCIDENT_QUEUE = "incident_queue"
APPROVAL_QUEUE = "approval_queue"
HISTORY_QUEUE_APPROVED = "approved_history"
HISTORY_QUEUE_REJECTED = "rejected_history"

_redis: redis.Redis | None = None
_a2a: A2AChannel | None = None


async def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = await redis.from_url(REDIS_URL, decode_responses=True)
    return _redis


# --- triage logic --------------------------------------------------------

def classify(incident: dict) -> AgentRole:
    """Pick the right specialist for an incident.

    Production has scenario-catalogue lookup + Neo4j graph queries + an LLM
    triage step. Workshop version is a 6-line keyword router. Same idea,
    much smaller surface area.
    """
    sid = incident.get("scenario_id") or incident.get("incident_type")
    # SSOT: a catalogue scenario routes to its owner_specialist. In the laptop lab
    # only the stability specialist runs, so catalogue scenarios resolve to stability
    # (production has troubleshooting + security specialists for their own domains).
    try:
        from shared.scenario_loader import get_scenario
        _scn = get_scenario(sid)
    except Exception:
        _scn = None
    if _scn:
        _owner = str(_scn.get("owner_specialist") or "").lower()
        if "troubleshoot" in _owner:
            return AgentRole.TROUBLESHOOTING_SPECIALIST
        if "security" in _owner:
            return AgentRole.SECURITY_SPECIALIST
        if "qos" in _owner:
            return AgentRole.YOUR_SPECIALIST
        return AgentRole.STABILITY_SPECIALIST
    msg = (incident.get("raw_message") or "").lower()
    scenario = (incident.get("scenario_id") or incident.get("incident_type") or "").lower()
    if "ospf" in msg or "bgp" in msg or "evpn" in msg or "ospf" in scenario or "bgp" in scenario or "evpn" in scenario:
        return AgentRole.STABILITY_SPECIALIST
    if "interface" in msg or "ping" in msg:
        return AgentRole.TROUBLESHOOTING_SPECIALIST
    if "acl" in msg or "aaa" in msg or "login" in msg:
        return AgentRole.SECURITY_SPECIALIST
    if "qos" in msg or "policy-map" in msg or "shaping" in msg or "congestion" in msg or "qos" in scenario:
        return AgentRole.YOUR_SPECIALIST
    # Default: send unknown to stability (the only one running in the lab).
    return AgentRole.STABILITY_SPECIALIST


# --- incident loop -------------------------------------------------------

async def incident_loop():
    """Pop from incident_queue, classify, delegate via A2A, await response."""
    r = await get_redis()
    a2a = A2AChannel(r, AgentRole.TEAM_LEADER)
    print(f"[team-leader] listening on {INCIDENT_QUEUE}")

    while True:
        try:
            popped = await r.brpop(INCIDENT_QUEUE, timeout=5)
            if popped is None:
                continue
            _, raw = popped
            incident = json.loads(raw)
            print(f"[team-leader] received incident {incident.get('id')} scenario={incident.get('scenario_id')}")

            specialist = classify(incident)
            task_id = f"task-{uuid.uuid4().hex[:8]}"
            print(f"[team-leader] -> delegating to {specialist.value} as {task_id}")
            await a2a.send_delegation(
                to_agent=specialist,
                task_id=task_id,
                payload={"incident": incident, "incident_id": incident.get("id")},
            )

            # Now wait for the response on our own inbox.
            # In production this is non-blocking and uses correlation_id matching;
            # here we just wait up to 30s for the first response and assume it's ours.
            response = await a2a.receive(timeout=30)
            if response is None or response.message_type != MessageType.TASK_RESPONSE:
                print(f"[team-leader] ❌ no response from {specialist.value} for {task_id}")
                continue

            result = response.payload.get("result", {})
            approval = {
                "task_id": response.task_id,
                "incident_id": incident.get("id"),
                "scenario_id": incident.get("scenario_id"),
                "device_id": result.get("device_id"),
                "specialist": specialist.value,
                "root_cause": result.get("root_cause"),
                "evidence": result.get("evidence"),
                "proposed_fix": result.get("proposed_fix"),
                "risk_assessment": result.get("risk_assessment"),
                "confidence": result.get("confidence"),
                "authored_by": result.get("authored_by"),
                "title": result.get("title"),
                "received_at": datetime.now(timezone.utc).isoformat(),
                "status": "pending_approval",
            }
            await r.lpush(APPROVAL_QUEUE, json.dumps(approval))
            print(f"[team-leader] ✓ approval queued: {task_id} confidence={approval['confidence']}")

        except Exception as e:
            print(f"[team-leader] loop error: {e}")
            await asyncio.sleep(2)


# --- HTTP server (ACP) ---------------------------------------------------

class ApprovalDecision(BaseModel):
    action: str           # "approve" | "reject"
    task_id: str
    decision_rationale: str = ""


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start the incident_loop as a background task."""
    task = asyncio.create_task(incident_loop())
    print("[team-leader] incident_loop started")
    yield
    task.cancel()
    print("[team-leader] incident_loop stopped")


app = FastAPI(title="Team Leader ACP", version="0.1.0", lifespan=lifespan)


@app.get("/acp/health")
async def health():
    return {"status": "ok", "service": "team-leader",
            "ts": datetime.now(timezone.utc).isoformat()}


@app.get("/acp/queues")
async def queues():
    r = await get_redis()
    return {
        "incident_queue": await r.llen(INCIDENT_QUEUE),
        "approval_queue": await r.llen(APPROVAL_QUEUE),
        "approved_history": await r.llen(HISTORY_QUEUE_APPROVED),
        "rejected_history": await r.llen(HISTORY_QUEUE_REJECTED),
        "a2a_stability_specialist_inbox": await r.llen("a2a_stability_specialist_inbox"),
        "a2a_team_leader_inbox": await r.llen("a2a_team_leader_inbox"),
    }


@app.get("/acp/approvals")
async def list_approvals():
    """Read-only view of the approval queue, newest first."""
    r = await get_redis()
    items = await r.lrange(APPROVAL_QUEUE, 0, 50)
    return [json.loads(i) for i in items]


@app.get("/acp/history")
async def list_history():
    r = await get_redis()
    approved = [json.loads(i) for i in await r.lrange(HISTORY_QUEUE_APPROVED, 0, 50)]
    rejected = [json.loads(i) for i in await r.lrange(HISTORY_QUEUE_REJECTED, 0, 50)]
    return {"approved": approved, "rejected": rejected}


@app.post("/acp/approval")
async def post_approval(d: ApprovalDecision):
    """Approve or reject a pending recommendation by task_id."""
    if d.action not in ("approve", "reject"):
        raise HTTPException(400, "action must be 'approve' or 'reject'")
    r = await get_redis()
    items = await r.lrange(APPROVAL_QUEUE, 0, -1)
    for idx, raw in enumerate(items):
        rec = json.loads(raw)
        if rec.get("task_id") == d.task_id:
            await r.lrem(APPROVAL_QUEUE, 1, raw)
            rec["decision_rationale"] = d.decision_rationale
            rec["decided_at"] = datetime.now(timezone.utc).isoformat()
            rec["status"] = d.action + "d"
            target = HISTORY_QUEUE_APPROVED if d.action == "approve" else HISTORY_QUEUE_REJECTED
            await r.lpush(target, json.dumps(rec))
            print(f"[team-leader] {d.action.upper()} {d.task_id}")
            return {"status": "ok", "task_id": d.task_id, "moved_to": target}
    raise HTTPException(404, f"no pending approval with task_id={d.task_id}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
