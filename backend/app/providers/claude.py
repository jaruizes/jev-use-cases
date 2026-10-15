import json
import os
from anthropic import AsyncAnthropic


def decision_schema(case) -> dict:
    """A forced tool call provides a typed decision rather than brittle text parsing."""
    if case.kind == "multi":
        properties = {
            "priority": {"type": "integer", "minimum": 0, "maximum": 4},
            "security_risk": {"type": "number", "minimum": 0, "maximum": 1},
            "team": {"type": "string", "enum": list(case.criteria["team"])},
        }
        return {
            "name": "submit_decision",
            "description": "Submit all three decisions about the incident.",
            "input_schema": {"type": "object", "properties": properties,
                             "required": list(properties), "additionalProperties": False},
        }
    if case.kind == "choice":
        value = {"type": "string", "enum": list(case.criteria.keys())}
    elif case.kind == "score":
        value = {"type": "integer", "minimum": 0, "maximum": len(case.criteria) - 1}
    elif case.kind == "noul":
        value = {"type": "number", "minimum": 0, "maximum": 1}
    else:
        raise ValueError("Structured decisions are not supported for generation")
    return {
        "name": "submit_decision",
        "description": "Submit the final structured decision for the given request.",
        "input_schema": {
            "type": "object",
            "properties": {"value": value},
            "required": ["value"],
            "additionalProperties": False,
        },
    }


def extract_decision(response, case):
    tools = [block for block in response.content
             if block.type == "tool_use" and block.name == "submit_decision"]
    if len(tools) != 1:
        raise ValueError("Claude did not provide exactly one structured decision")
    payload = tools[0].input
    if not isinstance(payload, dict):
        raise ValueError("Invalid Claude decision tool payload")
    if case.kind != "multi" and "value" not in payload:
        raise ValueError("Claude decision tool payload is missing value")
    if case.kind == "multi":
        if set(payload) != {"priority", "security_risk", "team"}:
            raise ValueError("Missing or extra incident triage decisions")
        priority, risk, team = payload["priority"], payload["security_risk"], payload["team"]
        if type(priority) is not int or not 0 <= priority <= 4:
            raise ValueError("Invalid triage priority")
        if type(risk) not in (float, int) or not 0 <= risk <= 1:
            raise ValueError("Invalid triage security probability")
        if not isinstance(team, str) or team not in case.criteria["team"]:
            raise ValueError("Invalid triage team")
        return {"priority": priority, "security_risk": float(risk), "team": team}, payload
    value = payload["value"]
    if case.kind == "choice":
        if not isinstance(value, str) or value not in case.criteria:
            raise ValueError("Invalid choice")
    elif case.kind == "score":
        if type(value) is not int or not 0 <= value < len(case.criteria):
            raise ValueError("Invalid integer score")
    elif case.kind == "noul":
        if type(value) not in (int, float) or not 0 <= value <= 1:
            raise ValueError("Invalid noul score")
        value = float(value)
    return value, payload


async def evaluate(case, text: str, provider: str) -> dict:
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise ValueError("ANTHROPIC_API_KEY is not configured")
    env_name = "CLAUDE_HAIKU_MODEL" if provider == "haiku" else "CLAUDE_SONNET_MODEL"
    model = os.getenv(env_name, "claude-haiku-4-5" if provider == "haiku" else "claude-sonnet-4-5")
    kwargs = {
        "model": model,
        "max_tokens": 1600 if case.kind == "generation" else 512,
        "messages": [{"role": "user", "content": text}],
    }
    if case.kind == "generation":
        kwargs["system"] = case.prompt + "\nRespond with Markdown."
    else:
        constraint = (
            "Return priority (0–4), security_risk (0–1), and team (PLATFORM/BACKEND/SECURITY) based on the incident. "
            "Use the field definitions in the tool schema."
            if case.kind == "multi" else
            f"Allowed choices and definitions: {json.dumps(case.criteria)}."
            if case.kind == "choice" else
            f"Ordered scoring rubric indexed from 0: {json.dumps(case.criteria)}."
            if case.kind == "score" else
            "Assess how strongly the given request supports the proposition. "
            "Use 0 for false and 1 for true."
        )
        kwargs["system"] = f"{case.prompt}\n{constraint}\nCall submit_decision exactly once."
        kwargs["tools"] = [decision_schema(case)]
        kwargs["tool_choice"] = {"type": "tool", "name": "submit_decision"}

    async with AsyncAnthropic() as client:
        response = await client.messages.create(**kwargs)

    if case.kind == "generation":
        value = "\n".join(block.text for block in response.content if block.type == "text")
        if not value.strip():
            raise ValueError("Claude produced no architecture document")
        raw = value
    else:
        value, raw = extract_decision(response, case)
    return {
        "value": value,
        "raw": raw,
        "usage": {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        },
        "model": response.model,
    }
