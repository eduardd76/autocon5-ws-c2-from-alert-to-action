"""
Lab 3 — runner for YOUR specialist (optional Step 4 wire-in).

This wraps the QoSSpecialist you wrote in `starter/agent_yourname.py` in the A2A
protocol loop, so the Team Leader can delegate live incidents to it. Crucially,
it calls YOUR `classify()` / `diagnose()` — not the stub LLM. When you trigger a
QoS incident, the approval card you see is produced by the code YOU wrote.

To use: copy this folder to `services/your-agent/`, paste your two methods over
the ones below, then follow WIRING_GUIDE.md. (The default below is the QoS
reference solution, so the wire-in works out of the box for a demo.)
"""
from __future__ import annotations

import asyncio
import os
import sys
from typing import Any

import redis.asyncio as redis
from redis.exceptions import TimeoutError as RedisTimeoutError

sys.path.insert(0, "/app")
from shared.a2a_protocol import A2AChannel, AgentRole, MessageType  # noqa: E402

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")


# =====================================================================
# ▼▼▼  YOUR SPECIALIST — paste your classify() + diagnose() here  ▼▼▼
#     (default = the QoS reference solution so the wire-in runs as-is)
# =====================================================================
class YourSpecialist:
    def __init__(self):
        self.agent_id = "qos-specialist-ws-c2"
        self.known_scenarios = {"qos_interface_congested"}

    def classify(self, incident: dict[str, Any]) -> bool:
        text = (incident.get("raw_message") or "").lower()
        if any(k in text for k in ("qos", "policy-map", "shaping", "congestion")):
            return True
        return incident.get("scenario_id") in self.known_scenarios

    async def diagnose(self, incident: dict[str, Any]) -> dict[str, Any]:
        if incident.get("scenario_id") in self.known_scenarios:
            return {
                "root_cause": "Egress drops on GigabitEthernet0/1 — child-policy "
                              "'voice' shaping below offered load",
                "evidence": [
                    "show policy-map interface Gi0/1: 12,408 drops in class voice",
                    "shape average 50 Mbps < offered 78 Mbps",
                    "parent interface not congested",
                ],
                "proposed_fix": {
                    "commands": ["policy-map child-policy", " class voice",
                                 "  shape average 100000000"],
                    "rollback": ["policy-map child-policy", " class voice",
                                 "  shape average 50000000"],
                },
                "risk_assessment": "low",
                "confidence": 0.88,
            }
        return {
            "root_cause": "Unrecognized QoS pattern — manual review needed",
            "evidence": [], "proposed_fix": {"commands": [], "rollback": []},
            "risk_assessment": "unknown", "confidence": 0.2,
        }
# =====================================================================
# ▲▲▲  END of your specialist  ▲▲▲
# =====================================================================


class SpecialistRunner:
    """Protocol plumbing — identical in shape to services/stability-agent/main.py.
    Receives a delegation, runs YOUR specialist, returns the diagnosis."""

    def __init__(self):
        self.role = AgentRole.YOUR_SPECIALIST
        self.specialist = YourSpecialist()
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
                continue  # idle poll, nothing in the inbox — this is normal
            except Exception as e:
                print(f"[your-agent] loop error: {e}")
                await asyncio.sleep(2)
                continue
            if msg is None or msg.message_type != MessageType.TASK_DELEGATION:
                continue
            try:
                print(f"[your-agent] ===== delegation {msg.task_id} =====")
                await self.process(msg)
            except Exception as e:
                print(f"[your-agent] process error on {msg.task_id}: {e}")
                await asyncio.sleep(1)

    async def process(self, msg):
        incident = msg.payload.get("incident", {})
        if not self.specialist.classify(incident):
            print(f"[your-agent] classify()=False — not mine, ignoring {msg.task_id}")
            return
        diagnosis = await self.specialist.diagnose(incident)
        result = {
            "task_id": msg.task_id,
            "agent_id": self.specialist.agent_id,
            "device_id": incident.get("device_id"),
            "scenario_id": incident.get("scenario_id") or incident.get("incident_type"),
            **diagnosis,
        }
        await self.a2a.send_response(
            to_agent=AgentRole.TEAM_LEADER,
            task_id=msg.task_id,
            result=result,
            correlation_id=msg.correlation_id,
        )
        print(f"[your-agent] responded {msg.task_id} (confidence={diagnosis.get('confidence')})")


async def main():
    runner = SpecialistRunner()
    await runner.init()
    try:
        await runner.run()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    asyncio.run(main())
