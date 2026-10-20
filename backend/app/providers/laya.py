"""Laya System One compatible HTTP adapter. Only used by Playground."""
import os
import httpx


def _questions(case):
    if case.kind == "multi":
        return {
            "priority": {"type": "score", "instructions": "Rate operational incident priority from 0 to 4 based on business impact, urgency and workarounds.", "criteria": case.criteria["priority"]},
            "security_risk": {"type": "noul", "instructions": case.criteria["security_risk"]},
            "team": {"type": "choice", "instructions": "Choose the primary team responsible for handling the incident.", "criteria": case.criteria["team"]},
        }
    question = {"type": case.kind, "instructions": case.prompt}
    if case.kind in ("choice", "score"):
        question["criteria"] = case.criteria
    return {"decision": question}


def _answer(answers, name, kind, criteria):
    if not isinstance(answers, dict) or not isinstance(answers.get(name), dict):
        raise ValueError("Missing Laya decision")
    data = answers[name]
    field = {"choice": "choice", "score": "score", "noul": "noul"}[kind]
    value = data.get(field)
    if kind == "choice":
        if not isinstance(value, str) or value not in criteria:
            raise ValueError("Invalid Laya choice")
    elif kind == "score":
        if type(value) not in (float, int) or isinstance(value, bool) or not 0 <= value <= len(criteria) - 1:
            raise ValueError("Invalid Laya score")
        value = float(value)
    else:
        if type(value) not in (float, int) or isinstance(value, bool) or not 0 <= value <= 1:
            raise ValueError("Invalid Laya noul")
        value = float(value)
    return value


async def evaluate(case, text: str) -> dict:
    if case.kind == "generation":
        raise ValueError("Laya cannot generate architecture documents")
    url = os.getenv("LAYA_BASE_URL", "http://laya:8000").rstrip("/") + "/v1/systemone"
    timeout = float(os.getenv("LAYA_TIMEOUT_SECONDS", "120"))
    headers = {}
    if os.getenv("LAYA_API_KEY"):
        headers["Authorization"] = "Bearer " + os.environ["LAYA_API_KEY"]
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, json={"state": text, "questions": _questions(case)}, headers=headers)
        response.raise_for_status()
        data = response.json()
    if not isinstance(data, dict):
        raise ValueError("Invalid Laya response")
    answers = data.get("answers")
    if case.kind == "multi":
        values = {
            "priority": _answer(answers, "priority", "score", case.criteria["priority"]),
            "security_risk": _answer(answers, "security_risk", "noul", None),
            "team": _answer(answers, "team", "choice", case.criteria["team"]),
        }
        value, raw = values, {key: answers[key] for key in values}
    else:
        value = _answer(answers, "decision", case.kind, case.criteria)
        raw = answers["decision"]
    routing = data.get("routing")
    model = routing.get("model") if isinstance(routing, dict) else None
    return {"value": value, "raw": raw, "usage": data.get("usage"), "model": "laya-" + (str(model) if model else "local"),
            "pricingStatus": "self_hosted_unpriced"}
