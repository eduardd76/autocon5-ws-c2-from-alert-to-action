"""
Lab 3 reference solution — QoS Specialist agent.

This is what your `agent_yourname.py` should look like when all 4 tests pass.
Shown in the last 10 minutes of the workshop. Don't peek before you've tried.

Drop-in: rename to `agent_yourname.py` in starter/ to make the tests pass without
writing anything yourself. (You will not learn that way, but it's a valid
emergency escape.)
"""
from __future__ import annotations

from typing import Any


# Canned LLM responses keyed by scenario_id. In production this is replaced by
# a fine-tuned 7B model. The pattern is exactly the same shape either way.
_CANNED = {
    "qos_interface_congested": {
        "root_cause": "Voice-priority class on Gi0/1 child-policy is over-subscribed — shaping cap is 1 Mbps, 60s burst peaked at 1.7 Mbps",
        "evidence": [
            "show policy-map int Gi0/1: 4521 drops on class voice-priority in 60s",
            "show int Gi0/1 | inc rate: peak 1.7 Mbps over the last interval",
            "upstream router-2 marks DSCP EF correctly; receive side is the bottleneck",
        ],
        "proposed_fix": {
            "commands": [
                "policy-map child-policy",
                "class voice-priority",
                "priority 2000",
            ],
            "rollback": [
                "policy-map child-policy",
                "class voice-priority",
                "priority 1000",
            ],
        },
        "risk_assessment": "low",
        "confidence": 0.88,
    },
}


class QoSSpecialist:
    """A specialist for QoS misconfiguration faults on Cisco IOS-XE / Arista EOS."""

    KEYWORDS = ("qos", "policy-map", "shaping", "congestion")

    def __init__(self):
        self.agent_id = "qos-specialist-ws-c2"
        self.known_scenarios = {"qos_interface_congested"}

    def classify(self, incident: dict[str, Any]) -> bool:
        msg = (incident.get("raw_message") or "").lower()
        if any(k in msg for k in self.KEYWORDS):
            return True
        if (incident.get("scenario_id") or "") in self.known_scenarios:
            return True
        return False

    async def diagnose(self, incident: dict[str, Any]) -> dict[str, Any]:
        scenario = incident.get("scenario_id")
        if scenario in _CANNED:
            return _CANNED[scenario].copy()

        # Unknown scenario — degrade gracefully.
        return {
            "root_cause": f"QoS specialist: scenario {scenario!r} not in known catalogue",
            "evidence": ["fell through to generic QoS handler — no LLM available offline"],
            "proposed_fix": {
                "commands": ["! please review manually — generic handler did not match"],
                "rollback": ["! no rollback required (no changes proposed)"],
            },
            "risk_assessment": "unknown",
            "confidence": 0.2,
        }
