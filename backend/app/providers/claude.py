import json
import os
from anthropic import AsyncAnthropic

async def evaluate(case, text: str, provider: str) -> dict:
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise ValueError("ANTHROPIC_API_KEY is not configured")
    env_name = "CLAUDE_HAIKU_MODEL" if provider == "haiku" else "CLAUDE_SONNET_MODEL"
    model = os.getenv(env_name, "claude-haiku-4-5" if provider == "haiku" else "claude-sonnet-4-5")
    if case.kind == "generation":
        instruction = case.prompt + "\nRespond with Markdown."
    else:
        constraint = (
            f"Only these choices are allowed: {json.dumps(case.criteria)}."
            if case.kind == "choice" else
            f"Use this ordered 0-based scoring rubric: {json.dumps(case.criteria)}."
            if case.kind == "score" else
            "Return a number between 0 and 1 estimating whether the proposition is true."
        )
        instruction = (
            f"{case.prompt}\n{constraint}\n"
            "Return ONLY valid JSON with a single field named value; "
            "its value must be a string for choice or number for score/noul. No markdown."
        )
    async with AsyncAnthropic() as client:
        res = await client.messages.create(
            model=model, max_tokens=1500 if case.kind == "generation" else 120,
            temperature=0, system=instruction,
            messages=[{"role": "user", "content": text}],
        )
    output = "".join(block.text for block in res.content if block.type == "text")
    if case.kind == "generation":
        value = output
    else:
        value = json.loads(output)["value"]
        if case.kind == "choice":
            if value not in case.criteria:
                raise ValueError("Claude returned a choice outside the permitted options")
        else:
            value = float(value)
            maximum = len(case.criteria) - 1 if case.kind == "score" else 1
            if not 0 <= value <= maximum:
                raise ValueError("Claude returned a score outside the permitted range")
    return {
        "value": value, "raw": output,
        "usage": {"input_tokens": res.usage.input_tokens, "output_tokens": res.usage.output_tokens},
        "model": model,
    }
