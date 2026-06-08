"""
Lab 3 — runner for the attendee's specialist (the 6th container on the pod).

It wraps the QoSSpecialist's classify()/diagnose() in the A2A loop so the Team
Leader can delegate live incidents to it. It reads the qos_parser MCP tool FIRST
(like the real specialists gather evidence), then runs YOUR diagnose(). When you
fire a QoS fault, the approval card is produced by the code YOU wrote.

ATTENDEE: paste your classify() + diagnose() into the YourSpecialist class below,
then `docker compose up -d --build your-agent`. (Default below = the QoS reference
solution, so the pod works out-of-the-box for the day-1 demo.)
"""
from __future__ import annotations
import asyncio, os, sys
from typing import Any
import redis.asyncio as redis
from redis.exceptions import TimeoutError as RedisTimeoutError

sys.path.insert(0, "/app")
from shared.a2a_protocol import A2AChannel, AgentRole, MessageType  # noqa: E402
from shared.mcp_client import MCPClient  # noqa: E402

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

# =====================================================================
# YOUR SPECIALIST — paste your classify() + diagnose() here
# (default = the QoS reference solution so the wire-in runs as-is)
# =====================================================================
class YourSpecialist:
    KEYWORDS = ("qos", "policy-map", "shaping", "congestion")
    def __init__(self):
        self.agent_id = "qos-specialist-ws-c2"
        self.known_scenarios = {"qos_interface_congested"}
    def classify(self, incident: dict[str, Any]) -> bool:
        text = (incident.get("raw_message") or "").lower()
        if any(k in text for k in self.KEYWORDS):
            return True
        return incident.get("scenario_id") in self.known_scenarios
    async def diagnose(self, incident: dict[str, Any]) -> dict[str, Any]:
        if incident.get("scenario_id") in self.known_scenarios:
            return {
                "root_cause": "Voice-priority child-policy on Gi0/1 is over-subscribed — shaper 1 Mbps, 60s burst 1.7 Mbps; WRED tail-dropping EF",
                "evidence": [
                    "show policy-map interface Gi0/1: 4521 drops on class voice-priority in 60s",
                    "shape average 1 Mbps < offered 1.7 Mbps; parent interface not congested",
                ],
                "proposed_fix": {
                    "commands": ["policy-map child-policy", " class voice-priority", "  priority 2000"],
                    "rollback": ["policy-map child-policy", " class voice-priority", "  priority 1000"],
                },
                "risk_assessment": "low",
                "confidence": 0.88,
            }
        return {"root_cause": "Unrecognized QoS pattern — manual review needed",
                "evidence": [], "proposed_fix": {"commands": [], "rollback": []},
                "risk_assessment": "unknown", "confidence": 0.2}
# =====================================================================

class SpecialistRunner:
    def __init__(self):
        self.role = AgentRole.YOUR_SPECIALIST
        self.specialist = YourSpecialist()
        self.mcp = MCPClient()
        self.r: redis.Redis | None = None
        self.a2a: A2AChannel | None = None
    async def init(self):
        self.r = await redis.from_url(REDIS_URL, decode_responses=True)
        self.a2a = A2AChannel(self.r, self.role)
        print(f"[your-agent] up. listening on {self.a2a.inbox}")
    async def run(self):
        while True:
            try:
                msg = await self.a2a.receive(timeout=5)
            except (RedisTimeoutError, asyncio.TimeoutError):
                continue
            except Exception as e:
                print(f"[your-agent] loop error: {e}"); await asyncio.sleep(2); continue
            if msg is None or msg.message_type != MessageType.TASK_DELEGATION:
                continue
            try:
                print(f"[your-agent] ===== delegation {msg.task_id} =====")
                await self.process(msg)
            except Exception as e:
                print(f"[your-agent] process error on {msg.task_id}: {e}"); await asyncio.sleep(1)
    async def process(self, msg):
        incident = msg.payload.get("incident", {})
        if not self.specialist.classify(incident):
            print(f"[your-agent] classify()=False — not mine, ignoring {msg.task_id}"); return
        # Step 1: gather live evidence via MCP (like the real specialists do)
        dev = incident.get("device_id", "router-1")
        print(f"[your-agent] step 1/2: reading qos_parser MCP evidence for {dev}")
        try:
            qos = (await self.mcp.qos_parser(dev)).get("data", {}).get("qos", {})
        except Exception as e:
            qos = {"error": str(e)}
        # Step 2: YOUR diagnosis
        print(f"[your-agent] step 2/2: running YOUR diagnose()")
        diagnosis = await self.specialist.diagnose(incident)
        cls = (qos.get("classes") or [{}])[0]
        if cls.get("drops_60s"):
            diagnosis.setdefault("evidence", []).insert(0,
                f"qos_parser(live): {cls['name']} {cls['drops_60s']} drops/60s, shape {cls.get('shape_kbps')}kbps < offered {cls.get('offered_kbps')}kbps")
        result = {"task_id": msg.task_id, "agent_id": self.specialist.agent_id,
                  "device_id": dev, "scenario_id": incident.get("scenario_id") or incident.get("incident_type"),
                  "mcp_evidence_sources": ["qos_parser"], **diagnosis}
        await self.a2a.send_response(to_agent=AgentRole.TEAM_LEADER, task_id=msg.task_id,
                                     result=result, correlation_id=msg.correlation_id)
        print(f"[your-agent] responded {msg.task_id} (confidence={diagnosis.get('confidence')})")

async def main():
    runner = SpecialistRunner(); await runner.init()
    try: await runner.run()
    except KeyboardInterrupt: pass

if __name__ == "__main__":
    asyncio.run(main())
