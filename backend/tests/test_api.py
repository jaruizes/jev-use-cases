from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)

def test_catalog_contains_four_cases():
    response = client.get("/api/use-cases")
    assert response.status_code == 200
    assert len(response.json()) == 4

def test_missing_case_rejected():
    response = client.post("/api/executions", json={"useCaseId":"missing","input":"hello","providers":["rules"]})
    assert response.status_code == 404

def test_rule_baseline_runs_without_credentials():
    response = client.post("/api/executions", json={"useCaseId":"lead-scoring","input":"Approved budget and CTO next quarter","providers":["rules"]})
    assert response.status_code == 200
    assert response.json()["results"][0]["status"] == "success"

def test_duplicate_providers_rejected():
    response = client.post("/api/executions", json={"useCaseId":"lead-scoring","input":"hello","providers":["rules","rules"]})
    assert response.status_code == 422
