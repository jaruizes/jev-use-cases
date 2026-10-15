import os
from typesafe_sdk import AsyncTypeSafeClient, Choice, Score, Noul

async def evaluate(case, text: str) -> dict:
    if not os.getenv("TYPESAFE_API_KEY"):
        raise ValueError("TYPESAFE_API_KEY is not configured")
    if case.kind == "generation":
        raise ValueError("Jev cannot generate open-ended architecture documents")
    if case.kind == "choice":
        q = Choice(instructions=case.prompt, criteria=case.criteria)
    elif case.kind == "score":
        q = Score(instructions=case.prompt, criteria=case.criteria)
    else:
        q = Noul(instructions=case.prompt)
    async with AsyncTypeSafeClient() as client:
        response = await client.system_one(state=text, questions={"decision": q})
    if case.kind == "choice":
        answer = response.choices["decision"]
        value = answer.choice
    elif case.kind == "score":
        answer = response.scores["decision"]
        value = answer.score
    else:
        answer = response.nouls["decision"]
        value = answer.noul
    return {
        "value": value, "raw": answer.model_dump(mode="json"),
        "usage": response.usage.model_dump(mode="json") if getattr(response, "usage", None) else None,
        "model": "jev-latest",
    }
