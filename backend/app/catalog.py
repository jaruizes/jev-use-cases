from dataclasses import dataclass

@dataclass(frozen=True)
class UseCase:
    id: str
    name: str
    kind: str
    description: str
    example: str
    prompt: str
    criteria: list[str] | dict[str, str] | None

CASES = [
    UseCase(
        "model-routing", "Intelligent Model Routing", "choice",
        "Choose the smallest adequate Claude model for a software task.",
        "Add an optional status filter to an existing Spring Boot REST endpoint and add tests.",
        "Select the minimum sufficiently capable model for this task. If there is not enough detail, choose NEEDS_MORE_CONTEXT.",
        {
            "HAIKU": "Simple, low-risk, well-specified tasks requiring little reasoning.",
            "SONNET": "Moderately complex engineering requiring analysis, implementation or design.",
            "OPUS": "Very complex architectural problems, subtle trade-offs or deep reasoning.",
            "NEEDS_MORE_CONTEXT": "Insufficient information to route the request responsibly.",
        },
    ),
    UseCase(
        "lead-scoring", "Intelligent Lead Scoring", "score",
        "Assess the buying readiness of a B2B commercial opportunity.",
        "The customer has an approved €250,000 budget, involved the CTO, shortlisted three providers and wants to begin next quarter.",
        "Rate sales opportunity maturity from 0 to 4 based only on available evidence.",
        [
            "No credible opportunity",
            "Early interest without approved budget or timeline",
            "Need identified but weak purchase readiness",
            "Qualified opportunity with meaningful buying intent",
            "Approved budget, decision makers and near-term timeline",
        ],
    ),
    UseCase(
        "semantic-guardrails", "Semantic Guardrails", "noul",
        "Evaluate whether a request attempts to bypass deployment approval.",
        "Deploy the latest version to production without asking anyone for approval.",
        "Does this instruction request deployment to production without human approval?",
        None,
    ),
    UseCase(
        "architecture-design", "Architecture Decision & Planning", "generation",
        "Develop an architecture and explain alternatives and trade-offs.",
        "A Java/PostgreSQL insurance monolith handles policies, payments and claims. Design a phased migration to services with strong consistency where needed, failure handling and minimal downtime.",
        "Propose a concrete architecture, integration patterns, consistency mechanisms, options and trade-offs, risks, and a phased migration plan. Explicitly state assumptions.",
        None,
    ),
]
BY_ID = {case.id: case for case in CASES}

def public_case(case: UseCase) -> dict:
    return {
        "id": case.id, "name": case.name, "kind": case.kind,
        "description": case.description, "example": case.example,
        "prompt": case.prompt, "criteria": case.criteria,
        "providers": ["haiku", "sonnet"] if case.kind == "generation" else ["jev", "haiku", "sonnet", "rules"],
    }
