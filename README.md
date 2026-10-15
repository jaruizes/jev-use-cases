# Jev Decision Lab

> **When should you use Jev instead of a generative LLM?**

Jev Decision Lab is an interactive proof of concept comparing **TypeSafe Jev** with **Claude Haiku** and **Claude Sonnet** in realistic decision workflows. It measures the actual provider responses and latency, estimates their token costs, and lets you explore cases in which a generative model is required instead.

The objective is to understand the **different roles of semantic decision models and generative LLMs**, not to assume that Jev always wins.

<img src="docs/pictures/introduction.jpg" alt="introduction" style="zoom:50%;" />



## Jev and System One: the concepts

With a general-purpose LLM, a user typically supplies instructions and context, and the model produces content. For a business workflow, developers often constrain that output using a schema or a tool call and validate the returned fields.

With **Jev (System One)**, the request is explicitly structured around **bounded semantic questions**. The application sends the context as `state` and defines the decisions to make in `questions`.

| Jev primitive | Meaning | Typical output | Example in this project |
| --- | --- | --- | --- |
| **Choice** | Choose among declared options | One of the defined alternatives | Route a software task or classify an email |
| **Score** | Assess against an ordered rubric | Continuous score | Prioritize a B2B lead or an incident |
| **Noul** | Assess support for a yes/no proposition | Number between 0 and 1 | Detect a request to bypass approval or a security-risk signal |
| **Multiple questions** | Evaluate several bounded decisions over the same context | A structured collection of Choice, Score and Noul answers | Incident Triage |

A `Noul` value is a **model assessment**, not a certified probability of truth or permission to perform an action. Thresholding requires domain-specific validation. Scores and choices similarly require application-side policy, business review and (where appropriate) human approval.



### How invoking Jev differs from invoking Claude

A Jev request is explicitly defined by its input context and one or more typed questions:

```python
response = await client.system_one(
    state=incident_description,
    questions={
        "priority": Score(
            instructions="Assess operational priority from 0 to 4.",
            criteria=[
                "Informational", "Low", "Moderate", "High", "Critical"
            ],
        ),
        "security_risk": Noul(
            instructions="Is there evidence of a cybersecurity or data-security risk?"
        ),
        "team": Choice(
            instructions="Select the primary incident response team.",
            criteria={
                "PLATFORM": "Infrastructure and shared platform.",
                "BACKEND": "Business APIs, application and database behavior.",
                "SECURITY": "Cybersecurity threats or exposure.",
            },
        ),
    },
)

priority = response.scores["priority"].score
security_risk = response.nouls["security_risk"].noul
team = response.choices["team"].choice
```

**One Jev API call** evaluates all three questions against the same context. This is not three successive calls, and the output is not an architecture document or free-form prose.

For a **fair comparison**, the Claude adapter also uses **one API call** for Incident Triage and forces a structured tool response containing all three fields. Claude can therefore produce typed responses too: **structured output is not exclusive to Jev**. The key distinction is that Jev exposes bounded semantic questions as its native task interface, whereas Claude is a general-purpose generative model constrained for this experiment.



### Where each approach fits

- **Jev:** classification, prioritization, proposition evaluation and combinations of these decisions.
- **Claude Haiku/Sonnet:** the same decisions using structured tool responses, plus open-ended reasoning, writing and design.
- **Generative-only example:** designing an architecture and explaining alternatives and a migration plan cannot be fulfilled through Jev's Choice/Score/Noul interface alone.

For real systems, a semantic risk assessment is not an authorization control. Explicit permissions and approvals still need deterministic enforcement.



## Use cases and examples

Each use case has one editable Playground input and **five predefined demonstration scenarios** available in **Test Scenarios**.

| ID | Use case | Jev capability | Five example scenarios |
| --- | --- | --- | --- |
| UC1 | Intelligent Model Routing | Choice | Simple endpoint change; complex refactor; distributed consistency; missing context; documentation |
| UC2 | Intelligent Lead Scoring | Score (0–4) | Ready to buy; early interest; no opportunity; need without purchase plan; qualified deal |
| UC3 | Semantic Guardrails | Noul (0–1) | Explicit approval bypass; compliant approval; synonymous bypass; staging-only; negated bypass |
| UC4 | Architecture Decision & Planning | Generative LLM only | Insurance migration; retail events; healthcare; multi-tenant SaaS; legacy data migration |
| UC5 | Email Classification | Choice | Invoice dispute; sales inquiry; technical support; unsolicited offer; general message |
| UC6 | Incident Prioritization | Score (0–4) | Critical outage; high impact; moderate degradation; minor issue; informational |
| UC7 | Incident Triage · Multi-decision | Score + Noul + Choice in one request | Payment outage; credential exposure; cluster degradation; minor API bug; phishing with confirmed access |





## Using the application

### Playground — a single execution

Select one use case, edit or replace the provided input, choose Jev/Haiku/Sonnet where supported, and click **Run comparison**. Each provider receives equivalent context, and the UI displays:

- Structured decisions or generated text, raw responses and error details.
- Measured latency, provider-reported tokens and estimated USD costs.
- Projected costs per 1,000 equivalent decisions and Jev/Claude cost and latency ratios, where measurable.

This is an **isolated experiment**, not an aggregate accuracy measurement.



#### Example: UC6 (Incident Prioritization)

For instance, if we execute **UC6 (Incident Prioritization)** we are going to score an incident between 0-4 depending of the input:

![uc-6-input](docs/pictures/uc-6-input.jpg)



Click on "Run comparison" to get the results:

![uc-6-results](docs/pictures/uc-6-results.jpg)

In this case, Jev is 59.4 times cheaper than Haiku and 178.1 times cheaper than Sonnet. And latency is also better, 3 times faster than Haiku and 4.7 times faster than Sonnet.



Example: UC7 (Incident Triage · Multi-decision)

In this case we are going to ask several tasks at the same time: scoring, detection of security risk and the responsible team related to an incident

![uc-7-input](docs/pictures/uc-7-input.jpg)

If we click in "Run comparision" we'll get the results:

![uc-7-results](docs/pictures/uc-7-results.jpg)



In this case, Jev is 56.9 times cheaper and 3.8 times faster than Haiku and 170.7 times cheaper and 5.2 times faster than Sonnet.



### Test Scenarios — repeated scenarios

Select a use case and the providers, then configure **1–20 iterations per scenario**. Every case has five scenarios, so **5 scenarios × 3 iterations = 15 rounds**, or **45 billable provider calls** when three providers are selected.

After execution, the UI reports:

- Reference agreement (correct responses / evaluated responses) and provider failures.
- Mean latency, estimated total and average costs, and Jev/Claude ratios.
- A per-scenario breakdown showing the actual responses and mismatches.

References are **illustrative**, not independently verified ground truth. A Score matches its reference within ±0.5; a Noul is evaluated using a 0.5 threshold; UC7 requires all three fields to match. UC4 has no numerical accuracy score. These metrics demonstrate the mechanics of evaluation, not a generalized claim of model accuracy.

History and reports are currently held in memory (backend process and current browser page, respectively); they are not persistent across restarts/refreshes.

#### Example: incident priorization

In this case, we are going to execute three times the scenario of incident prioritization. We have five examples and the expected result of the priorization:

```
"incident-prioritization": [
  ("i1","Critical outage","Production checkout is down for every customer, payments are impossible, no workaround exists during peak trading.",4),
  ("i2","High business impact","A core order API is failing for thousands of customers, but some purchases complete through another channel.",3),
  ("i3","Moderate degradation","Reports take much longer for a subset of users. The service works and an alternative export path is available.",2),
  ("i4","Minor issue","A small admin team sees an alignment problem on a settings form; their work continues through a workaround.",1),
  ("i5","Informational","A test environment dashboard icon is a slightly different shade; no functionality or users are impacted.",0),
 ],
```

For instance, the incident "Production checkout is down for every customer, payments are impossible, no workaround exists during peak trading" should be prioritized with a value of 4.

As we can see in the picture, quality is similar between Jev and LLMs but cost and latency is better using Jev:



![test-scenario](docs/pictures/test-scenario.jpg)





## Build and run locally

### Requirements

- **Docker Engine / Docker Desktop** with Docker Compose v2.
- **TypeSafe API key** and **Anthropic API key** for live comparisons.
- Network connectivity to both provider APIs. Live requests can incur charges.

### 1. Clone the repository

```bash
git clone https://github.com/jaruizes/jev-use-cases.git
cd jev-use-cases
```



### 2. Configure environment variables

Create a local `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env` with your own credentials:

```dotenv
TYPESAFE_API_KEY=your-typesafe-key
ANTHROPIC_API_KEY=your-anthropic-key
CLAUDE_HAIKU_MODEL=claude-haiku-4-5
CLAUDE_SONNET_MODEL=claude-sonnet-4-5
CORS_ORIGINS=http://localhost:4200

# Optional Jev pricing override, USD per million input tokens:
# JEV_INPUT_USD_PER_MTOK=0.042
```

Never commit `.env` or put credentials in Angular code. The keys are only passed to the backend.



### 3. Build and start

```bash
docker compose up --build -d
```

The application is available at:

| Service | URL |
| --- | --- |
| Angular UI | http://localhost:4200 |
| API documentation (Swagger) | http://localhost:8000/docs |
| API health | http://localhost:8000/api/health |
| Playground: Incident Triage | http://localhost:4200/playground/incident-triage |
| Test Scenarios | http://localhost:4200/test-scenarios |



### 4. Inspect logs and stop

```bash
docker compose logs -f api frontend
docker compose down
```

After changing `.env`, recreate the API container:

```bash
docker compose up -d --force-recreate api
```



### 5. Run tests

Run the backend tests from your local Python environment:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

The frontend can be built separately using Node.js/npm:

```bash
cd frontend
npm install
npm run build
```



## Costs and interpretation

Estimates are based on reported tokens, a versioned price table and the configured API model. The currently configured rates are:

| Provider/model | USD per 1M input tokens | USD per 1M output tokens |
| --- | ---: | ---: |
| Jev | 0.042 | 0 |
| Claude Haiku 4.5 | 1 | 5 |
| Claude Sonnet 4.5 | 3 | 15 |

The Jev list price comes from [TypeSafe's System One announcement](https://typesafe.ai/blog/introducing-system-one-models-and-jev). Claude model rates come from [Haiku 4.5](https://www.anthropic.com/news/claude-haiku-4-5) and [Sonnet 4.5](https://www.anthropic.com/news/claude-sonnet-4-5). These are **estimates**, not invoices; they exclude negotiated terms, taxes, caching and batch effects.

The value of this project is showing the **boundary between bounded semantic decisions and open-ended generation**, along with measured behavior on specific examples — not asserting that one model universally outperforms another.

## References

- [TypeSafe — Introducing System One Models and Jev](https://typesafe.ai/blog/introducing-system-one-models-and-jev)
- [TypeSafe — System One](https://docs.typesafe.ai/concepts/system-one)
- [Anthropic API documentation](https://docs.anthropic.com/)
