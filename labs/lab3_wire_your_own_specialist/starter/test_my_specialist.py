"""
Lab 3 — TDD tests for the QoS specialist.

Run with:
    cd labs/lab3_wire_your_own_specialist
    python -m pytest starter/test_my_specialist.py -v

All 4 tests start RED. Edit starter/agent_yourname.py until all 4 are GREEN.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

# Make `agent_yourname` importable when run from the lab dir.
sys.path.insert(0, str(Path(__file__).parent))

from agent_yourname import QoSSpecialist


# --- classify() --------------------------------------------------------

def test_classify_recognizes_qos_keywords():
    agent = QoSSpecialist()
    cases = [
        {"raw_message": "%QOS-4-CONGESTION on Gi0/1", "scenario_id": None, "device_id": "r1"},
        {"raw_message": "policy-map child-policy dropped 100 packets", "scenario_id": None, "device_id": "r1"},
        {"raw_message": "shaping rate exceeded on Et1", "scenario_id": None, "device_id": "r1"},
        {"raw_message": "egress congestion detected", "scenario_id": None, "device_id": "r1"},
    ]
    for c in cases:
        assert agent.classify(c) is True, f"should classify as QoS: {c}"


def test_classify_rejects_non_qos():
    agent = QoSSpecialist()
    cases = [
        {"raw_message": "%OSPF-5-ADJCHG neighbor down", "scenario_id": None, "device_id": "r1"},
        {"raw_message": "%BGP-3-NOTIFICATION hold time expired", "scenario_id": None, "device_id": "r1"},
        {"raw_message": "interface Gi0/0 line protocol down", "scenario_id": None, "device_id": "r1"},
    ]
    for c in cases:
        assert agent.classify(c) is False, f"should NOT classify as QoS: {c}"


# --- diagnose() --------------------------------------------------------

def test_diagnose_returns_expected_shape():
    agent = QoSSpecialist()
    incident = {
        "scenario_id": "qos_interface_congested",
        "raw_message": "%QOS-4-CONGESTION on Gi0/1",
        "device_id": "router-1",
    }
    result = asyncio.run(agent.diagnose(incident))

    # Top-level keys
    for k in ("root_cause", "evidence", "proposed_fix", "risk_assessment", "confidence"):
        assert k in result, f"missing key: {k}"

    # Types
    assert isinstance(result["root_cause"], str) and len(result["root_cause"]) > 0
    assert isinstance(result["evidence"], list) and len(result["evidence"]) >= 1
    assert isinstance(result["proposed_fix"], dict)
    assert "commands" in result["proposed_fix"] and "rollback" in result["proposed_fix"]
    assert isinstance(result["proposed_fix"]["commands"], list) and len(result["proposed_fix"]["commands"]) >= 1
    assert isinstance(result["proposed_fix"]["rollback"], list) and len(result["proposed_fix"]["rollback"]) >= 1
    assert result["risk_assessment"] in ("low", "medium", "high", "unknown")
    assert 0.0 <= result["confidence"] <= 1.0


def test_diagnose_for_known_scenario_returns_high_confidence():
    agent = QoSSpecialist()
    incident = {
        "scenario_id": "qos_interface_congested",
        "raw_message": "%QOS-4-CONGESTION on Gi0/1",
        "device_id": "router-1",
    }
    result = asyncio.run(agent.diagnose(incident))
    assert result["confidence"] > 0.7, (
        f"known scenario should yield confidence > 0.7, got {result['confidence']}"
    )
