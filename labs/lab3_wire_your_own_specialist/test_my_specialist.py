"""Lab 3 — the 4 tests your QoSSpecialist must pass (run: pytest -v).
They import YOUR code from starter/agent_yourname.py. Red until you implement
classify() + diagnose(); green when the contract is met."""
import os, sys, asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "starter"))
from agent_yourname import QoSSpecialist  # noqa: E402

def test_classify_true_on_keyword():
    a = QoSSpecialist()
    assert a.classify({"raw_message": "%QOS-4-CONGESTION ... policy-map child-policy drops", "scenario_id": None}) is True

def test_classify_true_on_scenario_id():
    a = QoSSpecialist()
    assert a.classify({"raw_message": "", "scenario_id": "qos_interface_congested"}) is True

def test_classify_false_on_unrelated():
    a = QoSSpecialist()
    assert a.classify({"raw_message": "%OSPF-5-ADJCHG neighbor down", "scenario_id": "ospf_neighbor_down"}) is False

def test_diagnose_known_scenario_is_complete_and_confident():
    a = QoSSpecialist()
    d = asyncio.run(a.diagnose({"scenario_id": "qos_interface_congested", "device_id": "router-1"}))
    assert isinstance(d.get("root_cause"), str) and d["root_cause"].strip()
    assert isinstance(d.get("evidence"), list) and len(d["evidence"]) >= 1
    pf = d.get("proposed_fix", {})
    assert pf.get("commands") and pf.get("rollback")
    assert d.get("risk_assessment") in ("low", "medium", "high")
    assert isinstance(d.get("confidence"), (int, float)) and d["confidence"] > 0.7
