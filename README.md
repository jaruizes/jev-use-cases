# Jev Decision Lab

> **When should you use Jev instead of a generative LLM?**

A visual, reproducible proof of concept (PoC) to compare **Jev**, **Claude Haiku**, **Claude Sonnet** and **deterministic rules**, highlighting where structured decisions win on quality, latency or cost, and where an LLM is essential.

**Status:** v0.1 Playground implemented (Angular + FastAPI). The bulk benchmark runner, reference datasets, and persistence are planned. M1 provides estimated per-request costs and cost/1,000 projections (not invoices). This project does not assume that Jev will win any benchmark. See [implementation status](IMPLEMENTATION.md).

## Goals

- Show when deterministic rules, Jev or generative LLMs are the appropriate tools.
- Run the same decision scenarios against Jev and Claude with comparable information and scoring rubrics.
- Evaluate **quality, p50/p95 latency, cost, reliability and consistency**, including high-impact mistakes.
- Make everything explorable via a visual application, with editable inputs and real API executions.
- Publish reproducible results, not cherry-picked comparisons.

## Use cases

| ID | Use case | Domain | Capability | Key question |
| --- | --- | --- | --- | --- |
| UC1 | Intelligent Model Routing | AI/software engineering | Jev **Choice** | Which Claude model should handle this task? |
| UC2 | Intelligent Lead Scoring | B2B sales | Jev **Score** | How promising is this commercial opportunity? |
| UC3 | Semantic Guardrails | Agent governance | Jev **Noul** | Does this request semantically violate a policy? |
| UC5 | Email Classification | Business operations | Jev **Choice** | Where should an email be routed? |
| UC6 | Incident Prioritization | Operations | Jev **Score** | How urgent is the incident? |
| UC4 | Architecture Decision & Planning | Software architecture | **Generative LLM** | How do we design and explain a complex solution? |

Five are **candidate Jev use cases**, not predetermined victories.

### UC1 — Intelligent Model Routing (Choice)

Given a software engineering request, choose between **HAIKU**, **SONNET**, **OPUS** or **NEEDS_MORE_CONTEXT**, using explicit descriptions of each route.

**Example:** “Add an optional status filter to an existing Spring Boot REST endpoint, including tests.”

The UI lets the user edit the task, choose the evaluators (Jev / Haiku / Sonnet), inspect each selected route and compare timing, quality and cost.

**Dataset:** CRUD requests, documentation, refactoring, security-sensitive changes, distributed transactions and ambiguous work.

**Evaluation:** agreement with expert-reviewed labels, cost, latency, **under-routing** (choosing a model too weak) and **over-routing** (unnecessary expenditure). Where feasible, actually execute a subset of tasks on the selected model to validate end-to-end success and cost.

### UC2 — Intelligent Lead Scoring (Score)

Score B2B sales opportunities on a **0–4** priority scale using structured CRM attributes and natural-language descriptions.

**Example:** “The customer has approved a €250,000 budget, involved the CTO, shortlisted three vendors, and expects to start next quarter.”

| Score | Interpretation |
| --- | --- |
| 0 | No credible opportunity identified |
| 1 | Early interest, no approved budget or timeline |
| 2 | Need identified, weak purchasing readiness |
| 3 | Qualified opportunity with buying intent |
| 4 | Approved budget, decision makers and near-term timeline |

The UI offers editable fields, preset lead profiles and side-by-side score comparisons.

**Dataset:** strong opportunities, early-stage leads, incomplete data and conflicting buying signals.

**Evaluation:** error against independently reviewed scores, recall for high-priority cases, consistency, latency and cost. Compare with a deterministic baseline. **A priority score is not a calibrated conversion probability**; predicting conversion requires actual historical outcomes.

### UC3 — Semantic Guardrails (Noul)

Evaluate natural-language propositions such as:

> Does this instruction request a production deployment without human approval?

Examples should include explicit attempts to bypass approval, compliant deployment requests, paraphrases and ambiguous language. Show the returned numerical assessment, configured threshold and final decision.

**Evaluation:** false positives, false negatives, threshold sensitivity, cost and latency. Document when to escalate uncertainty to a human or LLM.

**Important:** semantic evaluation is an additional signal, **not an authorization mechanism**. Actual approvals and permissions must be enforced with deterministic server-side controls.

### UC4 — Architecture Decision & Planning (Generative LLM required)

A Java/PostgreSQL insurance monolith covers policies, payments and claims. Ask for a target architecture and phased migration plan while preserving consistency, failure resilience and service continuity.

The system must **identify architectural issues, propose alternatives, discuss trade-offs, select integration patterns and generate a written migration plan**.

This is deliberately an open-ended reasoning/generation task. Jev's bounded choice/score/evaluation interface cannot independently create the required design artifact. The UI should explain that limitation rather than present an unfair “Jev failed” latency comparison. Claude's outputs should be assessed against an architectural review rubric.

**Optional hybrid demonstration:** after Claude generates candidate designs, Jev evaluates a predefined criterion across those options. This does not imply Jev generated or reasoned through the entire architecture.

## Visual experience — Jev Decision Lab

The application will have two modes:

### Playground

1. Choose one of the six use cases.
2. Load a representative example or edit input data and semantic criteria.
3. Select providers: Jev, Claude Haiku and Claude Sonnet.
4. Execute real calls using backend-protected API credentials.
5. View results side by side: decision, raw output, duration, estimated cost, confidence/score when available, API errors and expected answer.
6. Repeat the experiment or try ambiguous/edge-case examples.

For UC4, display the generated proposal as readable Markdown, not merely raw JSON.

### Benchmark

- Select versioned datasets, providers and repetitions.
- Preview projected call counts and configure cost/request limits.
- Track progress, errors and completed runs.
- Compare **accuracy/weighted errors**, **p50/p95 latency**, **cost per 1,000 decisions**, consistency and critical-error rates.
- Filter by use case, provider, run and input category.
- Inspect individual failed cases and export CSV or JSON.
- Preserve model versions, prompts, pricing assumptions and timestamps for reproducibility.

**No hard-coded winner badges or invented numbers.** The UI should distinguish expected values, measured values and estimates.

## Architecture

```text
                 Angular frontend
          Home · Playground · Benchmarks · Results
                           |
                      REST / SSE
                           |
                   FastAPI backend
             Orchestration · Evaluation · Metrics
                           |
           +---------------+---------------+
           |               |               |
      Jev adapter     Claude adapter    Rule engine
           |               |               |
       TypeSafe API     Anthropic API    Local code
                           |
                       SQLite DB
                  Run and result history
```

- **Frontend:** Angular, reusable controls and charts, responsive layout and feature-based components.
- **Backend:** Python + FastAPI, typed contracts, provider adapters and a reusable benchmark runner.
- **Persistence:** SQLite for local execution history; JSONL for curated, versioned input datasets.
- **Testing:** unit, provider contract and mocked integration tests; UI smoke tests.
- **Local launch target:** Docker Compose.

**Security:** API keys must stay in backend environment variables, never in Angular bundles or the repository.

### Target repository layout

```text
jev-use-cases/
├── frontend/
│   └── src/app/
│       ├── core/
│       ├── shared/
│       └── features/
│           ├── dashboard/
│           ├── playground/
│           ├── benchmarks/
│           └── results/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── providers/
│   │   ├── use_cases/
│   │   ├── benchmark/
│   │   └── persistence/
│   └── tests/
├── datasets/
│   ├── model-routing/
│   ├── lead-scoring/
│   ├── semantic-guardrails/
│   └── architecture-design/
├── docs/
├── docker-compose.yml
└── README.md
```

The layout is a **plan**, not a representation of existing files.

## Benchmark methodology

1. Define scoring rules and expert-reviewed ground truth before evaluating models.
2. Use equivalent context, alternatives and constraints for each evaluated provider.
3. Include at least a deterministic baseline for tasks that admit explicit rules.
4. Use diverse datasets, including ambiguity, contradictions, near-misses and insufficient context.
5. Repeat requests and interleave provider order to reduce sequencing bias.
6. Measure end-to-end latency, failures and retries. Report p50/p95 rather than just averages.
7. Distinguish provider-reported usage/charges from cost estimates based on documented pricing.
8. Measure critical errors independently, especially under-routing and guardrail false negatives.
9. Record versions, configurations, datasets, rubric and limitations with each benchmark.
10. Evaluate UC4 separately: judge reasoning and generated artifacts, not impossible structured-output parity.

**Initial target:** 100 labelled cases each for UC1–UC3, approximately 5 repetitions per case and provider; a smaller qualitatively reviewed corpus for UC4. Counts and budget limits should be configurable.

Suggested acceptance criteria must be **configurable and validated against real results**: minimum decision quality, maximum critical-error rate and material cost/latency improvement compared with a relevant Claude baseline.

## Planned milestones

1. **Foundation:** Angular shell, FastAPI, configuration, adapters and Docker Compose.
2. **Playground:** four working use cases, editable examples, provider comparison and raw responses.
3. **Evaluation:** labelled datasets, deterministic controls and use-case-specific metrics.
4. **Benchmark mode:** repeatable runs, progress, persistence, reporting and exports.
5. **Demo readiness:** guided walkthrough, documented findings and reproducible example runs.

## Getting started (planned)

**Playground implemented:** start Angular and FastAPI locally with Docker Compose:

```bash
cp .env.example .env
# Set TYPESAFE_API_KEY and ANTHROPIC_API_KEY in .env
docker compose up --build
```

This README will be updated with verified startup commands and actual model/SDK identifiers when implementation lands.

## References

- [TypeSafe — Coding Agents](https://docs.typesafe.ai/introduction/coding-agents)
- [TypeSafe — System One](https://docs.typesafe.ai/concepts/system-one)
- [Anthropic API documentation](https://docs.anthropic.com/)

## Principle

> **Use deterministic code for exact rules, Jev for bounded context-dependent decisions, and generative LLMs for open-ended reasoning or new artifact generation.**

The goal is to **measure the boundary**, not assume it.

## Additional decision use cases

### UC5 — Email Classification (Choice)

Classify an email into SALES, SUPPORT, BILLING, SPAM or OTHER from its subject and body. Compare Jev with Claude Haiku/Sonnet for ambiguous requests, such as messages that contain both a support issue and a refund request.

### UC6 — Incident Prioritization (Score)

Assign a priority from 0 (informational) to 4 (critical) based on business impact, affected customers, urgency, and workarounds. Compare Jev with Claude Haiku/Sonnet; scoring is an assessment and must not bypass formal incident-management escalation policies.

**Playground provider selection:** only Jev, Claude Haiku and Claude Sonnet. UC4 explicitly highlights that Jev is not an LLM and cannot generate an open-ended architecture.

## M1 — Cost Intelligence

The Playground reports versioned **estimated** USD costs using provider-reported token usage. Claude Haiku 4.5 uses $1 input / $5 output per million tokens; Sonnet 4.5 uses $3 / $15. A Jev price must be supplied by the operator via `JEV_INPUT_USD_PER_MTOK` (USD per million input tokens); otherwise its cost is explicitly unavailable. No cost of $0 is invented. These figures do not include billing adjustments, cache/batch discounts, taxes, or volume changes.

Sources: [Haiku 4.5 pricing](https://www.anthropic.com/news/claude-haiku-4-5) · [Sonnet 4.5 pricing](https://www.anthropic.com/news/claude-sonnet-4-5).
