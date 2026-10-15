# Implementation status — v0.1

Implemented:
- Angular responsive dashboard with routes and functional feature folders.
- Live Playground for the 6 defined use cases, including input editing, provider selection and results.
- FastAPI typed catalog/execution endpoints and adapter separation.
- Jev Choice/Score/Noul, Anthropic Claude.
- Docker Compose, basic backend tests, in-memory execution history and safe server-only API credentials.

Not implemented yet:
- Bulk benchmark runner, ground truth datasets, statistics and exports.
- Persistent execution history (current history is process memory).
- Provider-billed cost reconciliation (M1 adds versioned estimated cost only).
- OAuth/authentication, rate limiting and deployment hardening.

## Launch
```sh
cp .env.example .env
# Add TYPESAFE_API_KEY and ANTHROPIC_API_KEY as needed
docker compose up --build
```
Open http://localhost:4200. API docs: http://localhost:8000/docs.
Configure provider API keys to execute live comparisons.

Backend tests:
```sh
cd backend
pip install -r requirements.txt
pytest -q
```

**Important:** Model IDs in .env.example are configurable defaults and should be verified with your current provider account. Jev SDK response shape is based on public documentation, but live provider tests require credentials. The code has not been validated against live provider APIs in this environment. Provider calls may incur charges. The architecture design case is open-ended and supported only by Claude.

This release implements a Playground, not a validated benchmark; do not interpret side-by-side single calls as statistically meaningful comparisons.

## M1 — Cost Intelligence

Implemented: per-request estimated USD cost and projected cost per 1,000 equivalent calls, derived from provider-reported token usage; side-by-side cost bars in Playground; versioned standard rate lookup for Claude Haiku 4.5 and Sonnet 4.5; published Jev list price of $0.042 per million input tokens (output free), with an optional override. Unknown models and missing usage display N/A, **never $0**.

By default Jev uses TypeSafe's published $0.042 per million input tokens and free output tokens ([official announcement, 2026-09-15](https://typesafe.ai/blog/introducing-system-one-models-and-jev)). Set `JEV_INPUT_USD_PER_MTOK` in `.env` only to override the published rate for a different agreement. Estimates are not actual invoices. Restart/recreate the API after editing .env.

Not in M1: batch/caching tariffs, invoice reconciliation, benchmarking distributions, authoritative dataset assessment, persistence.

## Demo scenarios and quality (M1.1)

- Six use cases now offer five selectable sample scenarios apiece, plus a "run all five" action.
- For the five structured-decision cases, each scenario contains an illustrative reference decision. The backend records per-execution matches and a per-provider reference agreement rate across the latest attempt at each scenario in the current session.
- Choice: strict match; Score: absolute difference <= 0.5 to support continuous Jev scoring; Noul: proposition true at >= 0.5.
- Architecture generation: five diverse prompts, **no automatic correctness score**. Manual architectural review is needed.
- A custom or edited input has no reference score, even if its contents resemble a preset.
- Playground outputs now summarize Jev-vs-Haiku/Sonnet cost and latency ratios where valid positive measurements exist; missing data displays N/A.
- Running all scenarios makes real provider calls (may incur charges); runs are sequential and reference summaries are session-only. This is not an expert-reviewed benchmark dataset.

Use `pytest -q` from `backend` to execute the new scenario and quality tests; Angular and live APIs still need verification in a local Docker build.

## Dedicated Test Scenarios UI

The old placeholder Benchmarks navigation was replaced by `/test-scenarios`. Playground now handles one isolated run only. Test Scenarios offers 5 fixed scenarios, 1–20 iterations, Jev/Haiku/Sonnet selection, predicted request count, sequential rounds, stopping after an in-flight round, and an isolated per-batch result report: matched/evaluated and provider failures, average latency, total estimated and per-call cost, Jev/Claude ratios, and detailed outcomes for all five scenarios. A batch of 5 scenarios × 3 iterations runs 15 rounds and 45 provider calls when all three are selected. It can incur real API charges. Results are not durable after page navigation or refresh. The `/benchmarks` URL redirects to the new view.
