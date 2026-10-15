from fastapi.testclient import TestClient
from app.main import app
from app.scenarios import public_scenarios

client = TestClient(app)

def test_triage_endpoint_preserves_three_decisions(monkeypatch):
    async def fake_jev(case, text):
        assert case.id == "incident-triage"
        return {
            "value": {"priority": 3.99, "security_risk": 0.03, "team": "BACKEND"},
            "raw": {"test": True},
            "usage": {"input_tokens": 400, "output_tokens": 10},
            "model": "jev-latest",
        }

    monkeypatch.setenv("TYPESAFE_API_KEY", "test-only")
    monkeypatch.delenv("JEV_INPUT_USD_PER_MTOK", raising=False)
    monkeypatch.setattr("app.main.jev.evaluate", fake_jev)
    scenario = public_scenarios("incident-triage")[0]
    response = client.post("/api/executions", json={
        "useCaseId": "incident-triage",
        "input": scenario["input"],
        "scenarioId": scenario["id"],
        "providers": ["jev"],
    })
    assert response.status_code == 200
    body = response.json()
    result = body["results"][0]
    assert result["status"] == "success"
    assert result["correct"] is True
    assert result["value"]["team"] == "BACKEND"
    assert result["value"]["priority"] == 3.99
    assert result["value"]["security_risk"] == 0.03
    assert result["estimatedCostUsd"] > 0
