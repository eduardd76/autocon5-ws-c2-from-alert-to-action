"""
Stub LLM client — returns canned responses keyed off scenario_id.

This is the workshop-ONLY replacement for the real multi-provider LLM client
in agents/shared/llm_client.py. The production stack calls fine-tuned 7B models
on dedicated HF endpoints (Qwen2.5/CodeLlama/Mistral/Llama3) or falls back to
gpt-4o-mini. For a laptop demo with no API keys we hard-code the responses so
the agent reasoning chain is identical every time.

If LLM_PROVIDER=openai is set AND OPENAI_API_KEY is present, this client
delegates to openai (a one-liner — left as a curiosity for after the workshop).
"""
from __future__ import annotations

import json
import os
from typing import Any


# Canned responses keyed off scenario_id. Add a new entry here when you
# wire your own specialist in Lab 3.
CANNED: dict[str, dict[str, Any]] = {
    "ospf_neighbor_down": {
        "root_cause": "OSPF hello-interval mismatch on GigabitEthernet0/1 — local 10s, neighbor 30s",
        "evidence": [
            "show ip ospf interface Gi0/1 reports Hello 10s / Dead 40s",
            "neighbor adjacency stuck in INIT for 4m 23s",
            "no authentication mismatch (both none)",
        ],
        "proposed_fix": {
            "commands": [
                "interface GigabitEthernet0/1",
                "ip ospf hello-interval 30",
                "ip ospf dead-interval 120",
            ],
            "rollback": [
                "interface GigabitEthernet0/1",
                "no ip ospf hello-interval",
                "no ip ospf dead-interval",
            ],
        },
        "risk_assessment": "low",
        "confidence": 0.92,
    },
    "bgp_session_idle": {
        "root_cause": "BGP peer 10.0.0.2 stuck in Idle — TCP/179 unreachable, ACL on Gi0/0 dropping inbound",
        "evidence": [
            "show bgp summary: 10.0.0.2 state=Idle since 12m",
            "show access-list 101: deny tcp any any eq 179 (matches: 47)",
            "ping 10.0.0.2 succeeds, TCP-only blocked",
        ],
        "proposed_fix": {
            "commands": [
                "ip access-list extended 101",
                "no deny tcp any any eq 179",
                "permit tcp any any eq 179",
            ],
            "rollback": [
                "ip access-list extended 101",
                "no permit tcp any any eq 179",
                "deny tcp any any eq 179",
            ],
        },
        "risk_assessment": "medium",
        "confidence": 0.87,
    },
    "evpn_route_missing": {
        "root_cause": "EVPN Type-2 route for MAC aa:bb:cc:dd:ee:ff missing on Arista leaf-1 — RT import mismatch (VRF tenant-a configured to import 65000:200, peer advertising 65000:100)",
        "evidence": [
            "show bgp evpn route-type mac-ip: 0 entries for VNI 10100",
            "show vrf tenant-a: leaf-1 imports 65000:200, peer advertises 65000:100",
            "control-plane reachable, no underlay loss",
        ],
        "proposed_fix": {
            "commands": [
                "router bgp 65000",
                "vrf tenant-a",
                "route-target import evpn 65000:100",
            ],
            "rollback": [
                "router bgp 65000",
                "vrf tenant-a",
                "no route-target import evpn 65000:100",
            ],
        },
        "risk_assessment": "low",
        "confidence": 0.94,
    },
}

# Lab 3 attendees: append your scenario here.
# Example:
# CANNED["my_custom_scenario"] = {"root_cause": "...", ...}


class StubLLMClient:
    """Drop-in stand-in for the production LLMClient.

    Reads the scenario_id from the prompt's incident envelope and returns
    the matching canned response. If nothing matches, returns a generic
    'unable to diagnose' response so the agent code path still completes.
    """

    def __init__(self, agent_name: str = "stub"):
        self.agent_name = agent_name
        self.provider = os.getenv("LLM_PROVIDER", "stub").lower()

    async def analyze(self, prompt: str, scenario_id: str | None = None) -> dict[str, Any]:
        """Return a canned response for the given scenario.

        The production agent passes a long, formatted prompt (system + few-shot
        + evidence). We sidestep the prompt and key off scenario_id, which the
        Stability agent always sets from the incident envelope.
        """
        # SSOT: a YAML scenario in lab_scenarios/ wins over the built-in CANNED dict.
        try:
            from shared.scenario_loader import get_scenario
            _scn = get_scenario(scenario_id)
        except Exception:
            _scn = None
        if _scn:
            _fix = _scn.get("proposed_fix") or {}
            return {
                "root_cause": _scn.get("root_cause", f"scenario {scenario_id} (no root_cause authored)"),
                "evidence": _scn.get("evidence", []) or [],
                "proposed_fix": {"commands": _fix.get("commands", []) or [], "rollback": _fix.get("rollback", []) or []},
                "risk_assessment": _scn.get("risk_assessment", "unknown"),
                "confidence": float(_scn.get("confidence", 0.5) or 0.5),
                "llm_provider": "stub", "llm_model": "catalogue-v1", "tokens_used": 0,
                "authored_by": (_scn.get("provenance") or {}).get("author"),
                "title": _scn.get("title"),
            }
        if scenario_id and scenario_id in CANNED:
            response = CANNED[scenario_id].copy()
            response["llm_provider"] = "stub"
            response["llm_model"] = "canned-v1"
            response["tokens_used"] = 0
            return response

        return {
            "root_cause": f"stub: scenario unknown ({scenario_id!r})",
            "evidence": ["no canned response registered for this scenario"],
            "proposed_fix": {"commands": [], "rollback": []},
            "risk_assessment": "unknown",
            "confidence": 0.0,
            "llm_provider": "stub",
            "llm_model": "canned-v1",
            "tokens_used": 0,
        }

    async def close(self):
        pass


def get_llm_client(agent_name: str = "stub") -> StubLLMClient:
    """Factory. Production code has provider-switch logic here; we don't."""
    return StubLLMClient(agent_name=agent_name)
