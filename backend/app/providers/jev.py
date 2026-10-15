import os
from typesafe_sdk import AsyncTypeSafeClient, Choice, Score, Noul

async def evaluate(case, text: str) -> dict:
    if not os.getenv("TYPESAFE_API_KEY"):
        raise ValueError("TYPESAFE_API_KEY is not configured")
    if case.kind == "generation":
        raise ValueError("Jev cannot generate open-ended architecture documents")
    if case.kind == "multi":
        questions = {
            "priority": Score(instructions="Rate operational incident priority from 0 to 4 based on business impact, urgency and workarounds.", criteria=case.criteria["priority"]),
            "security_risk": Noul(instructions=case.criteria["security_risk"]),
            "team": Choice(instructions="Choose the primary team responsible for handling the incident.", criteria=case.criteria["team"]),
        }
        async with AsyncTypeSafeClient() as client:
            response = await client.system_one(state=text, questions=questions)
        answers = {
            "priority": response.scores["priority"].score,
            "security_risk": response.nouls["security_risk"].noul,
            "team": response.choices["team"].choice,
        }
        return {
            "value": answers,
            "raw": {
                "priority": response.scores["priority"].model_dump(mode="json"),
                "security_risk": response.nouls["security_risk"].model_dump(mode="json"),
                "team": response.choices["team"].model_dump(mode="json"),
            },
            "usage": response.usage.model_dump(mode="json") if getattr(response, "usage", None) else None,
            "model": "jev-latest",
        }
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
