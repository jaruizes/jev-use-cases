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
        "email-classification", "Email Classification", "choice",
        "Classify incoming business emails by intent.",
        "Subject: Invoice discrepancy. Hello, the amount charged on invoice INV-204 differs from the agreed price. Please send a corrected invoice.",
        "Choose the primary business intent of this email using exactly one category.",
        {
            "SALES": "New business inquiries, sales and commercial proposals.",
            "SUPPORT": "Product or service problems and troubleshooting.",
            "BILLING": "Invoices, payments, refunds and billing discrepancies.",
            "SPAM": "Unsolicited or irrelevant promotional messages.",
            "OTHER": "Messages with another purpose or insufficient information.",
        },
    ),
    UseCase(
        "incident-prioritization", "Incident Prioritization", "score",
        "Prioritize operational incidents according to business impact and urgency.",
        "Our checkout is unavailable for all customers during peak sales hours. Payments cannot be completed, no workaround exists and support is receiving hundreds of reports.",
        "Rate incident priority from 0 to 4 using affected users, business impact, urgency and availability of workarounds.",
        [
            "Informational or cosmetic issue with no material business impact",
            "Low impact, limited scope and a workaround",
            "Moderate impact or partial degradation",
            "High impact affecting key workflows or many users",
            "Critical outage or severe data/security risk needing immediate response",
        ],
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

from .scenarios import public_scenarios

def public_case(case: UseCase) -> dict:
    return {
        "id": case.id, "name": case.name, "kind": case.kind,
        "description": case.description, "example": case.example,
        "prompt": case.prompt, "criteria": case.criteria,
        "scenarios": public_scenarios(case.id),
        "providers": ["haiku", "sonnet"] if case.kind == "generation" else ["jev", "haiku", "sonnet"],
    }
