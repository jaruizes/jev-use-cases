import asyncio
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from .catalog import CASES, BY_ID, public_case
from .providers import claude, jev
from .pricing import estimate, list_prices, change_price
from .scenarios import reference, assess, public_scenarios, validate_dataset

logger = logging.getLogger("jev_decision_lab")
app = FastAPI(title="Jev Decision Lab API", version="0.1.0")
origins = [s.strip() for s in os.getenv("CORS_ORIGINS", "http://localhost:4200").split(",") if s.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST"], allow_headers=["*"])

class ExecuteRequest(BaseModel):
    useCaseId: str
    input: str = Field(min_length=1, max_length=20000)
    providers: list[Literal["jev", "haiku", "sonnet"]] = Field(min_length=1, max_length=3)
    scenarioId: str | None = None
    customScenario: dict[str, Any] | None = None

RUNS: dict[str, dict] = {}

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.get("/api/use-cases")
def use_cases():
    return [public_case(c) for c in CASES]

@app.get("/api/executions")
def executions():
    return list(reversed(list(RUNS.values())))

@app.get("/api/executions/{execution_id}")
def execution(execution_id: str):
    if execution_id not in RUNS:
        raise HTTPException(404, "Execution not found")
    return RUNS[execution_id]

@app.post("/api/executions")
async def execute(body: ExecuteRequest):
    case = BY_ID.get(body.useCaseId)
    if case is None:
        raise HTTPException(404, "Unknown use case")
    if len(set(body.providers)) != len(body.providers):
        raise HTTPException(422, "Duplicate providers")
    custom = None
    if body.customScenario is not None:
        try:
            custom = validate_dataset(case.id, [body.customScenario])[0]
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        if body.scenarioId != custom["id"] or body.input != custom["input"]:
            raise HTTPException(422, "Custom scenario ID and input must match the execution request")
    selected_reference = custom["expected"] if custom is not None else (reference(case.id, body.scenarioId, body.input) if body.scenarioId else None)
    async def run(provider: str) -> dict[str, Any]:
        started = time.perf_counter()
        try:
            if case.kind == "generation" and provider == "jev":
                return {"provider": provider, "status": "unsupported", "error": "This provider does not generate open-ended architecture artifacts", "latencyMs": 0}
            if provider == "jev":
                data = await jev.evaluate(case, body.input)
            else:
                data = await claude.evaluate(case, body.input, provider)
            return {"provider": provider, "status": "success", **data,
                    **estimate(provider, data.get("model"), data.get("usage")),
                    "correct": assess(case.id, data.get("value"), selected_reference),
                    "latencyMs": round((time.perf_counter() - started) * 1000, 2)}
        except Exception as exc:
            # Only log a sanitized summary: never log request bodies, headers,
            # credentials, provider response text or the full exception traceback.
            from anthropic import APIStatusError, APIConnectionError, APITimeoutError
            if isinstance(exc, APIStatusError):
                kind = "anthropic_api_error"
                detail = f"Anthropic HTTP {exc.status_code}; verify model access, model ID, credits and account permissions"
                logger.error("provider=%s use_case=%s category=%s http_status=%s exception_type=%s",
                             provider, case.id, kind, exc.status_code, type(exc).__name__)
            elif isinstance(exc, (APIConnectionError, APITimeoutError)):
                kind = "anthropic_connection_error"
                detail = "Anthropic connection failure or timeout"
                logger.error("provider=%s use_case=%s category=%s exception_type=%s",
                             provider, case.id, kind, type(exc).__name__)
            elif isinstance(exc, ValueError) and "not configured" in str(exc):
                kind = "configuration"
                detail = "Provider API key is not configured"
                logger.error("provider=%s use_case=%s category=%s", provider, case.id, kind)
            elif isinstance(exc, (ValueError, KeyError, TypeError)):
                kind = "invalid_provider_response"
                detail = "Provider response could not be parsed or validated"
                logger.error("provider=%s use_case=%s category=%s exception_type=%s",
                             provider, case.id, kind, type(exc).__name__)
            else:
                kind = "provider_error"
                detail = "Unexpected provider failure; check server logs"
                logger.error("provider=%s use_case=%s category=%s exception_type=%s",
                             provider, case.id, kind, type(exc).__name__)
            return {"provider": provider, "status": "error", "error": kind,
                    "detail": detail, "latencyMs": round((time.perf_counter() - started) * 1000, 2)}
    result = {
        "id": str(uuid4()), "useCaseId": case.id, "input": body.input,
        "scenarioId": custom["id"] if custom else (body.scenarioId if selected_reference is not None or (body.scenarioId and any(s["id"] == body.scenarioId and s["input"] == body.input for s in public_scenarios(case.id))) else None),
        "datasetSource": "custom" if custom else "built-in",
        "expected": selected_reference,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "results": await asyncio.gather(*(run(p) for p in body.providers)),
    }
    RUNS[result["id"]] = result
    return result

@app.get("/api/quality/{case_id}")
def quality(case_id: str):
    if case_id not in BY_ID:
        raise HTTPException(404, "Unknown use case")
    latest: dict[tuple[str, str], dict] = {}
    for run in RUNS.values():
        if run["useCaseId"] != case_id or not run.get("scenarioId"):
            continue
        for result in run["results"]:
            latest[(run["scenarioId"], result["provider"])] = result
    summary = []
    for provider in ("jev", "haiku", "sonnet"):
        evaluated = [item for (sid, name), item in latest.items() if name == provider and item.get("correct") is not None and item["status"] == "success"]
        correct = sum(item["correct"] is True for item in evaluated)
        summary.append({"provider": provider, "correct": correct, "total": len(evaluated),
                        "accuracyPercent": round(correct / len(evaluated) * 100, 1) if evaluated else None})
    return {"useCaseId": case_id, "results": summary, "referenceType": "illustrative"}

class PriceUpdate(BaseModel):
    inputUsdPerMillion: float = Field(ge=0, le=100000, allow_inf_nan=False)
    outputUsdPerMillion: float = Field(ge=0, le=100000, allow_inf_nan=False)

@app.get("/api/pricing")
def get_pricing():
    return list_prices()

@app.put("/api/pricing/{provider}")
def put_pricing(provider: str, body: PriceUpdate):
    try:
        return change_price(provider, body.inputUsdPerMillion, body.outputUsdPerMillion)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

class DatasetValidationRequest(BaseModel):
    useCaseId: str
    scenarios: list[dict[str, Any]]

@app.post("/api/datasets/validate")
def dataset_validation(body: DatasetValidationRequest):
    try:
        scenarios = validate_dataset(body.useCaseId, body.scenarios)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return {"valid": True, "useCaseId": body.useCaseId, "count": len(scenarios), "scenarios": scenarios}
