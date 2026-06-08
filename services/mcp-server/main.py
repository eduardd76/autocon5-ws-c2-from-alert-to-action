"""
MCP Server — stripped attendee version.

Production version (mcp-server/main.py) has 13 tools + idempotency-via-redis
+ SSH tunnel + Scrapli + adapter selection + NetBox integration. This is
the laptop-lab version: 3 tools, in-memory idempotency, mock devices only.

Tools exposed:
  POST /tools/ospf_parser
  POST /tools/interface_parser
  POST /tools/bgp_summary
  POST /incident/trigger          (creates a fake syslog event)
  GET  /health
"""
from __future__ import annotations

import asyncio
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any

import redis.asyncio as redis
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field


API_KEY = os.getenv("MCP_API_KEY", "dev-key-123")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

# --- in-memory device "state" --------------------------------------------
# Production reads real CLI via scrapli. Here we hard-code three routers
# in three scenario states. Each scenario_id triggers a different state set.

MOCK_DEVICE_STATE = {
    "router-1": {
        "vendor": "cisco-ios",
        "qos": {"interface": "GigabitEthernet0/1", "policy_map": "child-policy",
                "classes": [{"name": "voice-priority", "shape_kbps": 1000, "offered_kbps": 1700,
                             "drops_60s": 4521, "wred": True}],
                "egress_congested": True},
        "ospf_neighbors": [
            {"router_id": "10.0.0.2", "interface": "GigabitEthernet0/1",
             "state": "INIT", "uptime": "00:04:23", "dead_timer": "00:00:39"},
        ],
        "interfaces": {
            "GigabitEthernet0/1": {"status": "up", "protocol": "up",
                                   "input_errors": 0, "output_errors": 0,
                                   "hello_interval": 10, "dead_interval": 40},
        },
        "bgp_neighbors": [
            {"neighbor": "10.0.0.2", "remote_as": 65001, "state": "Idle",
             "msg_rcvd": 0, "msg_sent": 0, "uptime": "00:12:00"},
        ],
    },
    "router-2": {
        "vendor": "arista-eos",
        "ospf_neighbors": [
            {"router_id": "10.0.0.1", "interface": "Ethernet1",
             "state": "FULL", "uptime": "1d 02:14:55", "dead_timer": "00:00:35"},
        ],
        "interfaces": {
            "Ethernet1": {"status": "up", "protocol": "up",
                          "input_errors": 0, "output_errors": 0,
                          "hello_interval": 30, "dead_interval": 120},
        },
        "bgp_neighbors": [
            {"neighbor": "10.0.0.1", "remote_as": 65000, "state": "Established",
             "msg_rcvd": 8412, "msg_sent": 8401, "uptime": "1d 02:14:55"},
        ],
    },
    "leaf-1": {
        "vendor": "arista-eos",
        "evpn_routes": [
            {"route_type": 2, "mac": "aa:bb:cc:dd:ee:ff", "vni": 10100,
             "next_hop": "192.168.1.10", "rt": "65000:100"},
        ],
        "vrf_imports": ["65000:100"],
    },
}


# --- pydantic schemas ----------------------------------------------------

class ToolRequest(BaseModel):
    device_id: str
    idempotency_key: str = Field(default_factory=lambda: str(uuid.uuid4()))


class ToolResponse(BaseModel):
    device_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    data: dict[str, Any]


class IncidentTrigger(BaseModel):
    scenario_id: str = "bgp_session_idle"
    device_id: str = "router-1"


# --- app ----------------------------------------------------------------

app = FastAPI(title="MCP Server (workshop)", version="0.1.0")
_redis: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = await redis.from_url(REDIS_URL, decode_responses=True)
    return _redis


async def verify_api_key(x_mcp_api_key: str = Header(...)):
    if x_mcp_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="invalid api key")


async def check_and_cache(operation: str, key: str, fn) -> dict[str, Any]:
    """Idempotency: cache result for 60s. Production uses 24h."""
    r = await get_redis()
    cache_key = f"idem:{operation}:{key}"
    cached = await r.get(cache_key)
    if cached:
        return json.loads(cached)
    result = await fn()
    await r.setex(cache_key, 60, json.dumps(result))
    return result


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "mcp-server",
            "ts": datetime.now(timezone.utc).isoformat()}


@app.post("/tools/ospf_parser", response_model=ToolResponse)
async def ospf_parser(req: ToolRequest, _=Depends(verify_api_key)):
    async def _do():
        dev = MOCK_DEVICE_STATE.get(req.device_id)
        if not dev:
            raise HTTPException(404, f"unknown device {req.device_id}")
        return {
            "device_id": req.device_id,
            "data": {
                "neighbors": dev.get("ospf_neighbors", []),
                "vendor": dev["vendor"],
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    return await check_and_cache("ospf_parser", req.idempotency_key, _do)


@app.post("/tools/interface_parser", response_model=ToolResponse)
async def interface_parser(req: ToolRequest, _=Depends(verify_api_key)):
    async def _do():
        dev = MOCK_DEVICE_STATE.get(req.device_id)
        if not dev:
            raise HTTPException(404, f"unknown device {req.device_id}")
        return {
            "device_id": req.device_id,
            "data": {
                "interfaces": dev.get("interfaces", {}),
                "vendor": dev["vendor"],
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    return await check_and_cache("interface_parser", req.idempotency_key, _do)


@app.post("/tools/bgp_summary", response_model=ToolResponse)
async def bgp_summary(req: ToolRequest, _=Depends(verify_api_key)):
    async def _do():
        dev = MOCK_DEVICE_STATE.get(req.device_id)
        if not dev:
            raise HTTPException(404, f"unknown device {req.device_id}")
        return {
            "device_id": req.device_id,
            "data": {
                "neighbors": dev.get("bgp_neighbors", []),
                "vendor": dev["vendor"],
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    return await check_and_cache("bgp_summary", req.idempotency_key, _do)


@app.get("/scenarios")
async def list_scenarios():
    """List every scenario in the YAML catalogue (the SSOT) — for the UI/CLI."""
    try:
        import sys
        sys.path.insert(0, "/app")
        from shared.scenario_loader import load_scenarios
        sc = load_scenarios(force=True)
        return {"scenarios": [
            {"scenario_id": k, "title": v.get("title"), "owner": v.get("owner_specialist"),
             "source": v.get("_source_file")} for k, v in sorted(sc.items())]}
    except Exception as e:
        return {"scenarios": [], "error": str(e)}


@app.post("/tools/qos_parser", response_model=ToolResponse)
async def qos_parser(req: ToolRequest, _=Depends(verify_api_key)):
    async def _do():
        dev = MOCK_DEVICE_STATE.get(req.device_id)
        if not dev:
            raise HTTPException(404, f"unknown device {req.device_id}")
        return {"device_id": req.device_id,
                "data": {"qos": dev.get("qos", {}), "vendor": dev["vendor"]},
                "timestamp": datetime.now(timezone.utc).isoformat()}
    return await check_and_cache("qos_parser", req.idempotency_key, _do)


@app.post("/incident/trigger")
async def trigger_incident(trig: IncidentTrigger, _=Depends(verify_api_key)):
    """Push a fake syslog incident onto the incident_queue.

    Team Leader is listening on incident_queue and will pick this up,
    classify it, and delegate to the right specialist.
    """
    r = await get_redis()
    incident = {
        "id": f"syslog-{uuid.uuid4().hex[:8]}",
        "scenario_id": trig.scenario_id,
        "incident_type": trig.scenario_id,
        "device_id": trig.device_id,
        "severity": "warning",
        "raw_message": _scenario_to_syslog(trig.scenario_id, trig.device_id),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await r.lpush("incident_queue", json.dumps(incident))
    print(f"[INCIDENT] triggered scenario={trig.scenario_id} device={trig.device_id} id={incident['id']}")
    return {"status": "queued", "incident": incident}


def _scenario_to_syslog(sid: str, dev: str) -> str:
    try:
        import sys
        sys.path.insert(0, "/app")
        from shared.scenario_loader import get_scenario
        _scn = get_scenario(sid)
        if _scn and (_scn.get("trigger") or {}).get("example_message"):
            return str(_scn["trigger"]["example_message"]).replace("{device}", dev)
    except Exception:
        pass
    table = {
        "qos_interface_congested": "%QOS-4-CONGESTION: GigabitEthernet0/1 policy-map child-policy class voice-priority tail-drops 4521 pkts/60s (shape 1000kbps < offered 1700kbps)",
        "bgp_session_idle": f"%BGP-3-NOTIFICATION: sent to neighbor 10.0.0.2 4/0 (hold time expired) 0 bytes",
        "evpn_route_missing": f"%EVPN-4-ROUTE_MISSING: VNI 10100 expected MAC aa:bb:cc:dd:ee:ff not in BGP EVPN table",
    }
    return f"{dev}: {table.get(sid, 'unknown scenario')}"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
