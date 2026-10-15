from fastapi.testclient import TestClient
from app.main import app
from app.scenarios import validate_dataset, public_scenarios
import pytest

client = TestClient(app)

def custom(case="email-classification"):
    return {"useCaseId": case, "scenarios": [
        {"id":"spam1","title":"Prize message","input":"You've won a free phone!","expected":"SPAM"}]}

def test_validation_api_accepts_custom_reference():
    response = client.post("/api/datasets/validate", json=custom())
    assert response.status_code == 200
    assert response.json()["count"] == 1

def test_bad_choice_rejected():
    value = custom()
    value["scenarios"][0]["expected"] = "INVALID"
    assert client.post("/api/datasets/validate",json=value).status_code == 422

def test_duplicate_ids_rejected():
    value = custom()
    value["scenarios"].append(dict(value["scenarios"][0]))
    assert client.post("/api/datasets/validate",json=value).status_code == 422

def test_score_rejects_boolean_and_out_of_range():
    for invalid in (True, 5, "4", 1.5):
        data = {"useCaseId":"incident-prioritization","scenarios":[
            {"id":"one","title":"Outage","input":"Service unavailable","expected":invalid}]}
        assert client.post("/api/datasets/validate",json=data).status_code == 422

def test_multi_shape():
    data = {"useCaseId":"incident-triage","scenarios":[
        {"id":"triage1","title":"API outage","input":"API returns errors",
         "expected":{"priority":4,"security_risk":0,"team":"BACKEND"}}]}
    assert client.post("/api/datasets/validate",json=data).status_code == 200
    data["scenarios"][0]["expected"]["team"] = "WRONG"
    assert client.post("/api/datasets/validate",json=data).status_code == 422

def test_generation_expected_must_be_null():
    data = {"useCaseId":"architecture-design","scenarios":[
        {"id":"arch1","title":"Design","input":"Design a distributed service","expected":None}]}
    assert client.post("/api/datasets/validate",json=data).status_code == 200
    data["scenarios"][0]["expected"] = "some text"
    assert client.post("/api/datasets/validate",json=data).status_code == 422

def test_custom_reference_used_in_execution(monkeypatch):
    async def fake_jev(case, text):
        return {"value":"SPAM","model":"jev-latest","raw":{},"usage":{"input_tokens":100,"output_tokens":0}}
    monkeypatch.setattr("app.main.jev.evaluate",fake_jev)
    data=custom()
    scenario=data["scenarios"][0]
    result=client.post("/api/executions",json={
        "useCaseId":data["useCaseId"],"input":scenario["input"],
        "scenarioId":scenario["id"],"customScenario":scenario,"providers":["jev"]})
    assert result.status_code == 200
    body=result.json()
    assert body["datasetSource"] == "custom"
    assert body["expected"] == "SPAM"
    assert body["results"][0]["correct"] is True

def test_custom_input_mismatch_rejected_before_provider():
    scenario=custom()["scenarios"][0]
    response=client.post("/api/executions",json={
        "useCaseId":"email-classification","input":"different text",
        "scenarioId":scenario["id"],"customScenario":scenario,"providers":["jev"]})
    assert response.status_code == 422

def test_built_in_counts():
    assert all(len(public_scenarios(case)) == 30 for case in
               ("model-routing","lead-scoring","semantic-guardrails",
                "email-classification","incident-prioritization","incident-triage","architecture-design"))
