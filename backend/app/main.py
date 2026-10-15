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

logger = logging.getLogger("jev_decision_lab")
app = FastAPI(title="Jev Decision Lab API", version="0.1.0")
origins = [s.strip() for s in os.getenv("CORS_ORIGINS", "http://localhost:4200").split(",") if s.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST"], allow_headers=["*"])

class ExecuteRequest(BaseModel):
    useCaseId: str
    input: str = Field(min_length=1, max_length=20000)
    providers: list[Literal["jev", "haiku", "sonnet"]] = Field(min_length=1, max_length=3)

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
    async def run(provider: str) -> dict[str, Any]:
        started = time.perf_counter()
        try:
            if case.kind == "generation" and provider == "jev":
                return {"provider": provider, "status": "unsupported", "error": "This provider does not generate open-ended architecture artifacts", "latencyMs": 0}
            if provider == "jev":
                data = await jev.evaluate(case, body.input)
            else:
                data = await claude.evaluate(case, body.input, provider)
            return {"provider": provider, "status": "success", **data, "latencyMs": round((time.perf_counter() - started) * 1000, 2)}
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
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "results": await asyncio.gather(*(run(p) for p in body.providers)),
    }
    RUNS[result["id"]] = result
    return result
