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

Implemented: per-request estimated USD cost and projected cost per 1,000 equivalent calls, derived from provider-reported token usage; side-by-side cost bars in Playground; versioned standard rate lookup for Claude Haiku 4.5 and Sonnet 4.5; optional operator-configured Jev input-token rate. Unknown models, missing usage and unconfigured Jev pricing display N/A, **never $0**.

To estimate Jev costs, set `JEV_INPUT_USD_PER_MTOK` in `.env` to your independently verified current TypeSafe input rate (USD per million tokens). The application assumes Jev output tokens are free under the configured plan. It does not assert this reflects the account invoice. Restart/recreate API after editing .env.

Not in M1: batch/caching tariffs, invoice reconciliation, benchmarking distributions, authoritative dataset assessment, persistence.
