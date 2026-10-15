from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)

def test_catalog_contains_six_cases():
    response = client.get("/api/use-cases")
    assert response.status_code == 200
    cases = {c["id"]: c for c in response.json()}
    assert len(cases) == 6
    assert cases["email-classification"]["kind"] == "choice"
    assert cases["incident-prioritization"]["kind"] == "score"
    assert "BILLING" in cases["email-classification"]["criteria"]
    assert len(cases["incident-prioritization"]["criteria"]) == 5
    assert cases["architecture-design"]["providers"] == ["haiku", "sonnet"]
    assert all("rules" not in c["providers"] for c in cases.values())

def test_missing_case_rejected():
    response = client.post("/api/executions", json={"useCaseId":"missing","input":"hello","providers":["jev"]})
    assert response.status_code == 404

def test_rule_provider_rejected():
    response = client.post("/api/executions", json={"useCaseId":"lead-scoring","input":"hello","providers":["rules"]})
    assert response.status_code == 422

def test_duplicate_providers_rejected():
    response = client.post("/api/executions", json={"useCaseId":"lead-scoring","input":"hello","providers":["haiku","haiku"]})
    assert response.status_code == 422

def test_generation_without_jev():
    response = client.post("/api/executions", json={"useCaseId":"architecture-design","input":"Design an architecture","providers":["jev"]})
    assert response.status_code == 200
    assert response.json()["results"][0]["status"] == "unsupported"
