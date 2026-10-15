# Jev Decision Lab — Architecture

> **Status:** Implemented proof of concept, updated October 2026.  
> **Scope:** Current application architecture and development conventions, not a target-state wish list.  
> **Principle:** Keep the system understandable and evolvable through pragmatic, lightweight Specification-Driven Development (SDD).

## 1. Purpose and boundaries

Jev Decision Lab is a visual application for comparing **TypeSafe Jev (System One)** with **Anthropic Claude Haiku and Sonnet** on semantic decision-making tasks. It reports structured outputs, measured latency, estimated token costs, and agreement with illustrative reference labels.

There are **seven use cases**:

| ID | Use case | Jev operation | Evaluation |
| --- | --- | --- | --- |
| UC1 | Intelligent Model Routing | Choice | Exact route match |
| UC2 | Intelligent Lead Scoring | Score | Reference score within ±0.5 |
| UC3 | Semantic Guardrails | Noul | Boolean classification at threshold 0.5 |
| UC4 | Architecture Decision & Planning | Not applicable: generative Claude only | Qualitative review |
| UC5 | Email Classification | Choice | Exact category match |
| UC6 | Incident Prioritization | Score | Reference score within ±0.5 |
| UC7 | Incident Triage | **Score + Noul + Choice** in one call | All three answers must match the reference rules |

Jev evaluates bounded semantic questions. Claude uses forced tool outputs for comparable structured decisions, and generates prose for UC4. **A typed output is not exclusive to Jev**, and any semantic risk score is advisory, not an authorization mechanism.

### Current functional areas

1. **Overview:** seven-case catalog and feature navigation.
2. **Playground:** one editable input, one provider comparison, detailed response, latency, costs and Jev/Claude ratios.
3. **Test Scenarios:** five predefined scenarios per case, 1–20 iterations, provider selection, sequential rounds with parallel providers, progress and per-batch summaries.
4. **Pricing Settings:** inspect and edit per-provider USD-per-million-token rates.
5. **History:** review API executions recorded in the current backend process.

There is **no Benchmarks feature**. The earlier `/benchmarks` path redirects to `/test-scenarios`.

## 2. Architectural principles

- **Simplicity before abstraction:** introduce layers or patterns only when they solve an observed need.
- **Feature-first organization:** keep Angular pages and presentation concerns close to their feature.
- **Small components and readable templates:** favor separate `.ts` and `.html` files for nontrivial views.
- **Explicit API boundary:** external model SDKs and credentials stay in the backend.
- **Typed, validated contracts:** distinguish structured decisions, generated text, provider errors, missing cost data and reference judgments.
- **Faithful comparison:** use equivalent input context, one provider request per comparison, and clearly distinguish actual usage from cost estimates.
- **Safe failure:** return useful sanitized error categories and log diagnostic metadata without leaking credentials or user input.
- **No fabricated quality claims:** reference labels are illustrative; they are not expert-certified ground truth.
- **Lightweight SDD:** document observable behavior and acceptance criteria without introducing process overhead.

## 3. System overview

```text
Browser
  │
  ▼
Angular 20 SPA (Nginx)
  ├── Overview
  ├── Playground (single execution)
  ├── Test Scenarios (repeated runs / local report)
  ├── Pricing Settings
  └── History
  │
  │ HTTP JSON via /api (Nginx reverse proxy)
  ▼
FastAPI (Python)
  ├── Catalog + reference scenarios
  ├── Execute request orchestration
  │     ├── TypeSafe Jev SDK → System One
  │     └── Anthropic SDK → Claude Haiku / Sonnet
  ├── Reference agreement evaluation
  ├── Token-cost estimation and rate registry
  ├── In-memory execution history
  └── SQLite pricing settings
        └── Docker named volume (pricing-data)
```

Docker Compose runs the `frontend` and `api` services. Nginx serves Angular and proxies `/api/` to FastAPI. API keys are loaded from the local `.env` file into the API service, never into the Angular build.

### Runtime configuration

- `TYPESAFE_API_KEY`: Jev credentials.
- `ANTHROPIC_API_KEY`: Anthropic credentials.
- `CLAUDE_HAIKU_MODEL` and `CLAUDE_SONNET_MODEL`: selected API models; defaults are Claude Haiku 5.5 and Sonnet 5.5.
- `CORS_ORIGINS`: backend CORS configuration.
- `PRICING_DB_PATH`: optional backend path for the SQLite price registry (default `/app/data/pricing.sqlite3`).
- `JEV_INPUT_USD_PER_MTOK`: earlier pricing override convention; Pricing Settings is now the primary editable rate mechanism.

## 4. Frontend architecture

### Technology and conventions

- Angular 20, standalone components, lazy-loaded feature routes, strict TypeScript.
- Angular Router and `HttpClient` for application navigation and API access.
- Signals for view state and template updates; template-driven form bindings in existing screens.
- Styles currently live mainly in `src/styles.css`; component-specific styling can be extracted as complexity grows.
- No NgRx or generalized feature-facade layer is required for the current PoC.

### Current repository layout (key files)

```text
frontend/src/
├── main.ts
├── styles.css
└── app/
    ├── app.component.ts                   # Shell and navigation
    ├── app.routes.ts                      # Lazy feature routes
    ├── core/models.ts                     # Shared API/view types
    ├── services/
    │   ├── use-cases-api.service.ts
    │   └── executions-api.service.ts
    └── features/
        ├── dashboard/dashboard.page.ts
        ├── playground/
        │   ├── playground.page.ts
        │   ├── playground.page.html
        │   └── components/provider-results.component.*
        ├── test-scenarios/test-scenarios.page.*
        ├── pricing/pricing.page.*
        └── results/results.page.ts
```

**Component roles:** page components manage interactions and local state; small presentation components render provider results; API services wrap ordinary HTTP requests; models describe the frontend/backend contract.

The Pricing Settings page currently injects `HttpClient` directly. This is an exception to the intended API-service boundary; extracting a `PricingApiService` would improve consistency if the feature grows. Likewise, the Test Scenarios page owns its current batch orchestration and reporting calculations; splitting those computations into pure functions would aid testability without changing functionality.

### Routes

| Path | Page |
| --- | --- |
| `/` | Overview |
| `/playground/:id` | Single input and provider comparison |
| `/test-scenarios` | Repeated reference scenarios |
| `/pricing` | Pricing Settings |
| `/results` | Execution history |
| `/benchmarks` | Redirect to Test Scenarios (compatibility) |

## 5. Backend architecture

### Implementation layout

```text
backend/
├── requirements.txt
├── Dockerfile
├── app/
│   ├── main.py                # FastAPI endpoints and execution coordination
│   ├── catalog.py             # Seven use cases and question definitions
│   ├── scenarios.py           # Five references per use case, agreement rules
│   ├── pricing.py             # SQLite rate registry and cost estimates
│   └── providers/
│       ├── jev.py             # System One Choice / Score / Noul adapter
│       └── claude.py          # Anthropic forced-tool / generative adapter
└── tests/                     # API, adapters, scoring, pricing tests
```

`main.py` validates inbound requests with Pydantic and orchestrates the selected provider adapters concurrently for each execution. It then attaches latency, usage-based estimates and reference comparison results. For an unsupported operation (Jev on UC4), the response explicitly reports `unsupported`, rather than pretending the model has generated a document.

### Provider execution

**Jev:** `AsyncTypeSafeClient.system_one(state=..., questions=...)` receives an input state and explicitly typed questions. Choice returns a selected option, Score a continuous value and Noul a proposition assessment. UC7 sends three questions—`priority`, `security_risk`, `team`—in **one System One request**.

**Claude:** `AsyncAnthropic.messages.create(...)` handles both decision use cases and generative architecture work. Decisions force a `submit_decision` tool call with a validated schema. UC7 returns the same three named fields in one Anthropic request. UC4 instead returns free-form Markdown content.

**Request equivalence:** each provider receives the same incident/task input and analogous decision constraints. Jev and Claude retain their different native semantics and tokenization; identical token counts should not be assumed.

### HTTP endpoints

| Endpoint | Method | Responsibility |
| --- | --- | --- |
| `/api/health` | GET | Liveness |
| `/api/use-cases` | GET | Use cases, criteria, supported providers and scenarios |
| `/api/executions` | POST | Run a single input against selected providers |
| `/api/executions` | GET | Recent execution history |
| `/api/executions/{execution_id}` | GET | Individual execution details |
| `/api/quality/{case_id}` | GET | Session-local agreement over latest scenario attempts |
| `/api/pricing` | GET | Current editable pricing registry |
| `/api/pricing/{provider}` | PUT | Update provider input/output prices |

The execution request currently uses `useCaseId`, `input`, `providers`, and optional `scenarioId`. The response includes an execution ID, use-case and scenario metadata, a timestamp, and per-provider entries such as `status`, `value`, `raw`, `usage`, `latencyMs`, `correct`, and pricing metadata.

The API returns HTTP 200 when orchestration completes even if some provider entries have `status: error`; clients must inspect **individual provider statuses**. Errors are logged using sanitized categories instead of provider exception content.

## 6. Scenarios, quality and reporting

Each use case has five demonstration inputs in `scenarios.py`. Reference results are **illustrative** and should not be treated as expert-validated labels.

- **Choice:** exact label match.
- **Score:** reference tolerance of ±0.5 to accommodate Jev's continuous scores.
- **Noul:** compare proposition classification using threshold 0.5.
- **Incident Triage:** correct only if priority, security-risk classification **and** responsible team all pass.
- **Architecture Design:** no automatic correct/incorrect result; evaluate the generated artifact qualitatively.

In **Playground**, a single edited input is run once against selected providers. In **Test Scenarios**, five predefined inputs are repeated 1–20 times. For example, 5 scenarios × 3 iterations = 15 rounds and 45 provider calls with Jev, Haiku and Sonnet selected.

Test Scenarios computes a **batch-specific** report using only that page's collected executions: reference agreement, success/failure counts, average latency, total and average estimated cost, per-scenario responses, and relative Jev/Claude ratios. It does not mix older History runs into this aggregate. Stopping a test takes effect after the current request.

The `/api/quality/{case_id}` endpoint has distinct semantics: it summarizes the **latest attempt per scenario/provider** currently present in backend memory. This is not the same as the Test Scenarios batch report.

### Cost calculation

Cost estimate = `(input_tokens × input_rate + output_tokens × output_rate) / 1,000,000`, using the rate applicable to the **actual model** and saved configuration. Results include rate source and revision, so estimates can be interpreted later. Unknown models or missing token usage return an unavailable estimate rather than a fabricated zero.

The seeded rates are:

| Provider/model | Input USD / million | Output USD / million |
| --- | ---: | ---: |
| Jev | 0.042 | 0 |
| Claude Haiku 5.5 | 0.10 | 0.50 |
| Claude Sonnet 5.5 | 2 | 10 |

Haiku 5.5 has a separate published rate tier above 100,000 input tokens. The application uses that tier when the default published pricing is active; manually configured rates take precedence. The API persists pricing in SQLite under the `pricing-data` volume, but **individual executions are held in Python process memory**.

Cost projections are estimates, not invoices. They do not incorporate all potential cache, batch, negotiated-rate or tax adjustments.

## 7. Security, persistence and operational limits

- Provider credentials are read server-side from environment variables. They must not be committed or emitted to frontend bundles.
- The provider error handler avoids logging request bodies, provider response text or secrets.
- **Pricing Settings has no authentication.** The PoC is intended for local use; do not expose these write endpoints to the public internet.
- Execution history and scenario reports are **not durably stored**. Restarting the API clears the history, and refreshing Test Scenarios clears its current report.
- Concurrent pricing updates and cross-session traceability are limited by the PoC architecture.
- There is no production-grade rate limiting, user authentication, background job queue or cost budget enforcement. A repeated test can initiate real billable API calls.

## 8. Testing and local development

Run the entire stack:

```bash
cp .env.example .env
# Edit .env with TYPESAFE_API_KEY and ANTHROPIC_API_KEY
docker compose up -d --build
```

Frontend: `http://localhost:4200`; API docs: `http://localhost:8000/docs`.

Backend tests (outside Docker when pytest is not in the container runtime setup):

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

Angular build:

```bash
cd frontend
npm install
npm run build
```

Test priorities: schema validation, choice/score/noul adapters, multi-decision answers, scenario scoring, price-tier changes, missing pricing data, API failures and UI load/error states. Provider integrations should be mocked in automated tests; live API calls should be explicit, limited smoke checks.

**Validation note:** the architectural description reflects repository code; a successful Docker build and end-to-end live-provider verification must be established separately.

## 9. Pragmatic SDD and engineering conventions

For nontrivial changes, capture a brief living specification covering **purpose, inputs/outputs, UI states, API contracts, acceptance criteria and relevant tests**. Keep it alongside existing documentation when useful; do not create mandatory paperwork for small fixes.

Prefer English identifiers and narrow, meaningful responsibilities. Refactor repeated logic only when it is genuinely shared. Keep the distinction between **observed values**, **calculated estimates** and **reference judgments** explicit in all API and UI outputs.

### Architecture decision record

| ID | Decision | Status |
| --- | --- | --- |
| FE-001 | Feature-first Angular layout with standalone components and lazy routes | Implemented |
| FE-002 | Typed API services between feature pages and FastAPI | Partially implemented (Pricing page directly uses HttpClient) |
| FE-003 | Local signals and component state; no unnecessary global store | Implemented |
| FE-004 | Small components and dedicated templates for nontrivial views | Implemented, with remaining large-page refactoring opportunities |
| BE-001 | FastAPI orchestrates provider adapters and protects API keys | Implemented |
| BE-002 | Jev Choice/Score/Noul, including multiple questions in one call | Implemented |
| BE-003 | Claude uses forced tool outputs for bounded decisions | Implemented |
| DATA-001 | In-memory execution history; SQLite for editable pricing only | Implemented PoC limitation |
| QA-001 | Five illustrative scenarios per case and transparent reference agreement | Implemented |
| SDD-001 | Short, living specifications and tests over rigid ceremony | Adopted |

Update this document when a decision, boundary, or persisted contract changes. Avoid contradictory parallel specifications.
