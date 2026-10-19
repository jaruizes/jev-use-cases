import asyncio
from types import SimpleNamespace
import httpx
import pytest
from app.catalog import BY_ID
from app.providers import laya


def test_question_mapping():
    assert laya._questions(BY_ID["email-classification"])["decision"]["type"] == "choice"
    assert laya._questions(BY_ID["lead-scoring"])["decision"]["type"] == "score"
    assert laya._questions(BY_ID["semantic-guardrails"])["decision"]["type"] == "noul"
    assert set(laya._questions(BY_ID["incident-triage"])) == {"priority", "security_risk", "team"}


@pytest.mark.parametrize("case_id,payload,expected", [
    ("email-classification", {"decision": {"choice": "BILLING"}}, "BILLING"),
    ("lead-scoring", {"decision": {"score": 3.5}}, 3.5),
    ("semantic-guardrails", {"decision": {"noul": 0.7}}, 0.7),
    ("incident-triage", {"priority": {"score": 4.0}, "security_risk": {"noul": 0.1}, "team": {"choice": "BACKEND"}},
     {"priority": 4.0, "security_risk": 0.1, "team": "BACKEND"}),
])
def test_laya_adapter(monkeypatch, case_id, payload, expected):
    async def handler(request):
        assert request.url.path == "/v1/systemone"
        return httpx.Response(200, json={"answers": payload, "routing": {"model": "multilingual"}})
    transport = httpx.MockTransport(handler)
    real = httpx.AsyncClient
    monkeypatch.setattr(laya.httpx, "AsyncClient", lambda **kwargs: real(transport=transport))
    result = asyncio.run(laya.evaluate(BY_ID[case_id], "example"))
    assert result["value"] == expected
    assert result["model"] == "laya-multilingual"


def test_invalid_choice_rejected():
    with pytest.raises(ValueError):
        laya._answer({"decision": {"choice": "UNKNOWN"}}, "decision", "choice",
                     BY_ID["email-classification"].criteria)
