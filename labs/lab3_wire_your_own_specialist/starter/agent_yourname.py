"""
Lab 3 starter — QoS Specialist agent.

Fill in the two methods marked `# TODO:`. Run the tests in
test_my_specialist.py until they all pass.

The contract you're implementing is the same one the production agents follow
(agents/stability/agent_a2a.py etc.) — two methods do all the work, everything
else is protocol plumbing the Team Leader handles.
"""
from __future__ import annotations

from typing import Any


class QoSSpecialist:
    """A specialist for QoS misconfiguration faults on Cisco IOS-XE / Arista EOS.

    Two responsibilities:
      1. classify()  — given an incoming incident, decide whether to handle it.
      2. diagnose()  — given an incident this specialist handles, return root
                       cause + proposed remediation.
    """

    def __init__(self):
        self.agent_id = "qos-specialist-ws-c2"
        # Optional: declare which scenario_ids this specialist owns. The tests
        # don't require you to use this — but the production pattern is to drive
        # classify() off a known scenario set, not free-text keyword match.
        self.known_scenarios = {"qos_interface_congested"}

    # ------------------------------------------------------------------
    # TODO 1: implement classify()
    # ------------------------------------------------------------------
    def classify(self, incident: dict[str, Any]) -> bool:
        """Return True if this is a QoS incident this specialist should handle.

        Inputs:
            incident — dict with keys:
                - "raw_message": str        (the syslog text)
                - "scenario_id": str | None (set by the trigger button)
                - "device_id":   str

        Rules to encode (the tests pin these):
          - Return True if 'qos', 'policy-map', 'shaping', or 'congestion'
            appears (case-insensitive substring) in raw_message.
          - Return True if scenario_id is in self.known_scenarios.
          - Return False otherwise.

        Hint: use `(incident.get("raw_message") or "").lower()` to handle missing keys.
        """
        # TODO: implement
        raise NotImplementedError("Lab 3 attendee: implement QoSSpecialist.classify()")

    # ------------------------------------------------------------------
    # TODO 2: implement diagnose()
    # ------------------------------------------------------------------
    async def diagnose(self, incident: dict[str, Any]) -> dict[str, Any]:
        """Return a diagnosis envelope for the QoS incident.

        Return shape (the tests pin these keys):
          {
            "root_cause":      <str>,           # human-readable, one sentence
            "evidence":        [<str>, ...],    # facts you used (>=1)
            "proposed_fix":    {
                "commands":   [<str>, ...],     # CLI lines to apply (>=1)
                "rollback":   [<str>, ...],     # CLI lines to undo  (>=1)
            },
            "risk_assessment": "low" | "medium" | "high",
            "confidence":      <float 0..1>,    # >0.7 for known scenarios
          }

        For the unknown scenario case, return confidence < 0.5 and risk
        "unknown" (or "medium" — your call).

        Hint: in the production system this method calls an LLM. For the
        workshop you can hard-code a believable response keyed off
        incident['scenario_id'] — same pattern as services/shared/stub_llm_client.py.
        """
        # TODO: implement
        raise NotImplementedError("Lab 3 attendee: implement QoSSpecialist.diagnose()")
