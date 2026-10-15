from fastapi.testclient import TestClient
from app.main import app, RUNS
from app.scenarios import SCENARIOS, public_scenarios, reference, assess

client = TestClient(app)

def test_thirty_scenarios_for_each_use_case():
    assert len(SCENARIOS) == 7
    assert all(len(items) == 30 for items in SCENARIOS.values())
    catalog = client.get("/api/use-cases").json()
    assert all(len(item["scenarios"]) == 30 for item in catalog)

def test_reference_only_when_input_unchanged():
    case = public_scenarios("email-classification")[0]
    assert reference("email-classification", case["id"], case["input"]) == "BILLING"
    assert reference("email-classification", case["id"], "different text") is None

def test_scoring_accepts_jev_continuous_score():
    assert assess("incident-prioritization", 3.99, 4) is True
    assert assess("incident-prioritization", 3.4, 4) is False

def test_noul_uses_threshold_and_not_raw_equality():
    assert assess("semantic-guardrails", 0.85, 1) is True
    assert assess("semantic-guardrails", 0.15, 0) is True
    assert assess("semantic-guardrails", 0.9, 0) is False

def test_architecture_has_no_automatic_ground_truth():
    assert all(item["expected"] is None for item in public_scenarios("architecture-design"))

def test_quality_latest_execution_per_scenario():
    RUNS.clear()
    RUNS["1"] = {
        "useCaseId": "incident-prioritization", "scenarioId": "i1",
        "results": [{"provider": "jev", "status": "success", "correct": False}],
    }
    RUNS["2"] = {
        "useCaseId": "incident-prioritization", "scenarioId": "i1",
        "results": [{"provider": "jev", "status": "success", "correct": True}],
    }
    try:
        rows = client.get("/api/quality/incident-prioritization").json()["results"]
        jev = next(row for row in rows if row["provider"] == "jev")
        assert jev["total"] == 1
        assert jev["correct"] == 1
        assert jev["accuracyPercent"] == 100
    finally:
        RUNS.clear()
