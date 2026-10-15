# Implementation status — v0.1

Implemented:
- Angular responsive dashboard with routes and functional feature folders.
- Live Playground for the 4 defined use cases, including input editing, provider selection and results.
- FastAPI typed catalog/execution endpoints and adapter separation.
- Jev Choice/Score/Noul, Anthropic Claude and an intentionally simple deterministic baseline.
- Docker Compose, basic backend tests, in-memory execution history and safe server-only API credentials.

Not implemented yet:
- Bulk benchmark runner, ground truth datasets, statistics and exports.
- Persistent execution history (current history is process memory).
- Verified cost computation and pricing/version registry.
- OAuth/authentication, rate limiting and deployment hardening.

## Launch
```sh
cp .env.example .env
# Add TYPESAFE_API_KEY and ANTHROPIC_API_KEY as needed
docker compose up --build
```
Open http://localhost:4200. API docs: http://localhost:8000/docs.
Use the `rules` provider to explore without external credentials.

Backend tests:
```sh
cd backend
pip install -r requirements.txt
pytest -q
```

**Important:** Model IDs in .env.example are configurable defaults and should be verified with your current provider account. Jev SDK response shape is based on public documentation, but live provider tests require credentials. The code has not been validated against live provider APIs in this environment. Provider calls may incur charges. The rule baseline is intentionally naive. The architecture design case is open-ended and supported only by Claude.

This release implements a Playground, not a validated benchmark; do not interpret side-by-side single calls as statistically meaningful comparisons.
