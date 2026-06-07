"""
Stability Specialist Agent — stripped attendee version.

Production (~800 lines, agents/stability/agent_a2a.py) has ContextNode +
AnalyzeNode + ValidateNode + KG queries + DT sandbox + 7-step verifiability
chain emission. This is the laptop version: receive delegation -> gather MCP
evidence -> call stub LLM -> send response.

The flow demonstrates the protocol pattern. The production flow is identical
in shape, just with more node implementations and persistence.
"""
from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timezone

import redis.asyncio as redis

sys.path.insert(0, "/app")
from shared.a2a_protocol import A2AChannel, AgentRole, MessageType  # noqa: E402
from shared.mcp_client import MCPClient  # noqa: E402
from shared.stub_llm_client import get_llm_client  # noqa: E402


REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")


class StabilityAgent:
    def __init__(self):
        self.agent_id = "stability-agent-ws-c2"
        self.role = AgentRole.STABILITY_SPECIALIST
        self.mcp = MCPClient()
        self.llm = get_llm_client("stability")
        self.r: redis.Redis | None = None
        self.a2a: A2AChannel | None = None

    async def init(self):
        self.r = await redis.from_url(REDIS_URL, decode_responses=True)
        self.a2a = A2AChannel(self.r, self.role)
        print(f"[{self.agent_id}] initialized. listening on {self.a2a.inbox}")

    async def run(self):
        while True:
            try:
                msg = await self.a2a.receive(timeout=5)
                if msg is None:
                    continue
                if msg.message_type != MessageType.TASK_DELEGATION:
                    continue
                print(f"\n[{self.agent_id}] ===== delegation {msg.task_id} =====")
                await self.process(msg)
            except Exception as e:
                print(f"[{self.agent_id}] loop error: {e}")
                await asyncio.sleep(2)

    async def process(self, msg):
        incident = msg.payload.get("incident", {})
        device_id = incident.get("device_id", "router-1")
        scenario_id = incident.get("scenario_id") or incident.get("incident_type")
        start = datetime.now(timezone.utc)

        # --- Step 1: gather context via MCP -----------------------------
        print(f"[{self.agent_id}] step 1/3: gathering MCP evidence for {device_id}")
        evidence = {}
        try:
            evidence["ospf"] = (await self.mcp.ospf_parser(device_id)).get("data", {})
        except Exception as e:
            evidence["ospf"] = {"error": str(e)}
        try:
            evidence["interfaces"] = (await self.mcp.interface_parser(device_id)).get("data", {})
        except Exception as e:
            evidence["interfaces"] = {"error": str(e)}
        try:
            evidence["bgp"] = (await self.mcp.bgp_summary(device_id)).get("data", {})
        except Exception as e:
            evidence["bgp"] = {"error": str(e)}

        # --- Step 2: ask the LLM for a diagnosis ------------------------
        print(f"[{self.agent_id}] step 2/3: LLM diagnosis for scenario={scenario_id}")
        diagnosis = await self.llm.analyze(
            prompt=f"incident={incident} evidence={evidence}",
            scenario_id=scenario_id,
        )

        # --- Step 3: build response -------------------------------------
        duration = (datetime.now(timezone.utc) - start).total_seconds()
        result = {
            "task_id": msg.task_id,
            "agent_id": self.agent_id,
            "device_id": device_id,
            "scenario_id": scenario_id,
            "root_cause": diagnosis.get("root_cause"),
            "evidence": diagnosis.get("evidence", []),
            "proposed_fix": diagnosis.get("proposed_fix", {}),
            "risk_assessment": diagnosis.get("risk_assessment"),
            "confidence": diagnosis.get("confidence"),
            "authored_by": diagnosis.get("authored_by"),
            "title": diagnosis.get("title"),
            "llm_provider": diagnosis.get("llm_provider"),
            "llm_model": diagnosis.get("llm_model"),
            "tokens_used": diagnosis.get("tokens_used"),
            "duration_seconds": duration,
            "mcp_evidence_sources": list(evidence.keys()),
        }
        print(f"[{self.agent_id}] step 3/3: sending response to team_leader "
              f"(confidence={result['confidence']}, duration={duration:.2f}s)")
        await self.a2a.send_response(
            to_agent=AgentRole.TEAM_LEADER,
            task_id=msg.task_id,
            result=result,
            correlation_id=msg.correlation_id,
        )

    async def close(self):
        await self.mcp.close()
        await self.llm.close()
        if self.r:
            await self.r.close()


async def main():
    a = StabilityAgent()
    await a.init()
    try:
        await a.run()
    except KeyboardInterrupt:
        pass
    finally:
        await a.close()


if __name__ == "__main__":
    asyncio.run(main())
