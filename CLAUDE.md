# CLAUDE.md — Agentic Digital Marketing Copilot

> Project context for Claude Code. Read this fully before scaffolding or writing code.
> When in doubt about scope, prefer the **v1** definition below and defer anything marked **v2**.

---

## 1. What this is

An agentic system that turns a **campaign brief** into **platform-specific marketing copy**, runs it through a **critic + eval loop** until it passes a quality gate, and lets a **human approve or regenerate** before anything is finalized. Built as a portfolio flagship for AI Engineering interviews.

The copy generation is the *easy* part. The engineering value — and what this project must showcase — is:

1. **Multi-agent orchestration** with a real revision loop (copywriter ↔ critic), not a single prompt.
2. **Guardrails** — schema-validated outputs + brand-safety enforcement (no false claims, on-tone).
3. **Evaluation** — a rubric-based LLM-as-judge that scores every asset and *gates* the loop.
4. **Human-in-the-loop** — nothing is "final" without explicit approval.

Keep these four pillars visible and well-tested. They are the differentiators in interviews. Do **not** let this collapse into a thin "generate captions" wrapper.

---

## 2. Scope

### v1 (build this — and only this, first)

- Input: a campaign brief (brand/product, goal, audience, tone, target platforms).
- Agents: **Strategist**, **Copywriter**, **Brand-Safety Critic**.
- Orchestration: LangGraph graph with a **copywriter → critic revision loop**, gated by an eval score, with a **max-iteration guard**.
- Guardrails: Pydantic schema validation on every agent output + a brand-guideline / banned-claims check.
- Eval: rubric LLM-as-judge scoring each asset (clarity, CTA strength, brand fit, platform fit) → score + rationale.
- Output: 2–3 platform-specific assets, each with its score and the critic's notes.
- Backend: FastAPI (async), streams agent progress to the client.
- Frontend: Flutter app — brief form → live agent progress → review cards (asset + score + notes) → approve / regenerate.
- Persistence: SQLite (campaigns, assets, runs).
- Packaging: Dockerized, deployable to a free tier.

### v2 (DO NOT build yet — leave clean seams for these)

- Research agent + web search.
- Brand-voice RAG over the brand's past content (vector DB; possibly vectorless for guideline docs).
- LiteLLM gateway for cost routing (cheap model for drafts, strong model for finals).
- Langfuse tracing + prompt versioning + eval-over-time dashboard.
- Social Media Publishing Layer — publish via MCP tools (`post_to_platform`, `schedule_post`, `get_post_status`), OAuth, scheduling, retry/idempotency. **Rule when added: draft → human approves → publish. Never auto-publish.**
- A/B variant generation + predicted-performance ranking.

> Design v1 so these slot in later without rewrites: keep the LLM call behind a thin client, keep prompts in their own module, keep agents as independent nodes.

---

## 3. Architecture

```
Brief
  │
  ▼
[Strategist]  → produces a campaign plan (angle, key messages, per-platform direction)
  │
  ▼
[Copywriter]  → drafts asset(s) per target platform   ◄────────────┐
  │                                                                 │ (revise with critic feedback)
  ▼                                                                 │
[Brand-Safety Critic + Eval judge]                                  │
  │   - guardrail checks (schema, banned claims, tone)              │
  │   - rubric score per asset                                      │
  │                                                                 │
  ├── score ≥ threshold  → PASS → return assets ──────────────► Human review (approve / regenerate)
  └── score <  threshold AND iterations < MAX → loop back ─────────┘
                          (else return best-so-far, flagged)
```

The conditional edge (pass / loop / give-up) is the heart of the system. Test it explicitly.

---

## 4. Tech stack

- **Language:** Python 3.11+ (backend), Dart/Flutter (app).
- **Orchestration:** LangGraph.
- **Validation:** Pydantic v2 — every agent I/O is a typed model.
- **LLM:** provider-agnostic via a thin wrapper (`llm/client.py`). Default to one provider, model name from env. Do not hardcode model strings in business logic.
- **Backend:** FastAPI (async), SSE for streaming agent steps (simpler than WebSocket for v1).
- **DB:** SQLite via SQLModel (swap to Postgres later if needed).
- **Frontend:** Flutter, Riverpod for state, `dio` for HTTP, SSE client for live progress.
- **Packaging:** Docker + docker-compose (local), single Dockerfile for backend deploy.
- **CI:** GitHub Actions — lint (ruff) + format (black) + pytest on push.
- **Free-tier deploy target:** Render / Fly.io / Railway / HF Spaces (pick one; SQLite-friendly). Avoid anything that bills by default.
- **Secrets:** `.env` only, never committed. Provide `.env.example`.

---

## 5. Suggested repo structure

```
marketing-copilot/
├── CLAUDE.md
├── README.md
├── .env.example
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py              # FastAPI app + routes
│   │   ├── config.py            # env-driven settings
│   │   ├── models.py            # Pydantic + SQLModel schemas
│   │   ├── db.py                # SQLite session
│   │   ├── llm/
│   │   │   ├── client.py        # thin, swappable LLM wrapper
│   │   │   └── prompts/         # one file per agent prompt
│   │   ├── agents/
│   │   │   ├── strategist.py
│   │   │   ├── copywriter.py
│   │   │   └── critic.py        # guardrails + eval judge
│   │   ├── graph/
│   │   │   ├── state.py         # LangGraph state object
│   │   │   └── build.py         # nodes, edges, conditional loop
│   │   └── guardrails/
│   │       └── checks.py        # banned claims, tone, schema enforcement
│   └── tests/
└── app/                         # Flutter project
    └── lib/
        ├── main.dart
        ├── models/
        ├── services/            # api client + SSE
        ├── state/               # Riverpod providers
        └── screens/             # brief, run/progress, review
```

---

## 6. Core data models (sketch — adjust as needed)

```python
class Brief(BaseModel):
    brand: str
    product: str
    goal: str                      # e.g. "drive signups"
    audience: str
    tone: str                      # e.g. "playful, confident"
    platforms: list[str]           # e.g. ["instagram", "linkedin"]
    brand_guidelines: str | None    # plain-text rules for v1

class CampaignPlan(BaseModel):
    angle: str
    key_messages: list[str]
    per_platform_direction: dict[str, str]

class Asset(BaseModel):
    platform: str
    body: str
    cta: str
    hashtags: list[str] = []

class GuardrailResult(BaseModel):
    passed: bool
    violations: list[str]          # e.g. ["unverifiable claim: 'best in world'"]

class EvalScore(BaseModel):
    clarity: int                   # 1–5
    cta_strength: int
    brand_fit: int
    platform_fit: int
    overall: float                 # weighted; the gate compares this
    rationale: str

class AssetResult(BaseModel):
    asset: Asset
    guardrail: GuardrailResult
    score: EvalScore
    iterations: int
```

---

## 7. Agent contracts

- Each agent takes a typed input and returns a typed output (above). **No free-form strings crossing agent boundaries.**
- Prompts live in `llm/prompts/`, never inline in logic.
- The LLM wrapper must enforce JSON output and validate it against the expected Pydantic model; on parse failure, retry once with a repair instruction, then raise.
- **Critic** does two jobs and must keep them separate in output: (a) guardrail check → `GuardrailResult`, (b) rubric score → `EvalScore`. A guardrail failure forces a revision regardless of score.

---

## 8. LangGraph orchestration

- State holds: `brief`, `plan`, `current_assets`, `results`, `iteration`, `max_iterations` (e.g. 3), `threshold` (e.g. overall ≥ 4.0).
- Nodes: `strategist` → `copywriter` → `critic` → conditional edge.
- Conditional edge logic:
  - all assets pass guardrails AND meet threshold → **END** (return results).
  - else if `iteration < max_iterations` → increment, route back to `copywriter` **with the critic's feedback injected** so it actually improves.
  - else → **END**, return best-so-far with a `needs_human_attention` flag.
- The copywriter must receive prior drafts + critic feedback on a revision pass (don't regenerate blind).

---

## 9. Guardrails (must-have, v1)

- **Schema:** every agent output validated by Pydantic; invalid → repair retry → fail loudly.
- **Brand safety:** check generated copy against `brand_guidelines` and a banned-claims list (absolute/unverifiable claims like "guaranteed", "best in the world", medical/financial promises). A violation blocks PASS.
- **Tone:** critic flags off-tone copy as a guardrail violation, not just a low score.
- Keep guardrail logic in `guardrails/checks.py`, callable independently and unit-tested.

---

## 10. Eval (must-have, v1)

- LLM-as-judge scoring each asset on the rubric in `EvalScore`, returning numbers **and** a rationale.
- `overall` is a documented weighted combination; the threshold gates the loop.
- Build a tiny **golden set** (5–10 hand-labeled briefs+assets with expected pass/fail) and a script to run the judge against it, so you can show the eval itself is calibrated. This is a strong interview talking point.

---

## 11. API surface (v1)

- `POST /campaigns` — submit a brief, returns a run id.
- `GET  /campaigns/{id}/stream` — SSE stream of agent steps + final results.
- `GET  /campaigns/{id}` — fetch a completed run.
- `POST /campaigns/{id}/assets/{platform}/approve` — mark asset approved.
- `POST /campaigns/{id}/assets/{platform}/regenerate` — re-run loop for one asset.

---

## 12. Flutter app (v1)

Three screens: **Brief** (form), **Run** (live agent progress via SSE), **Review** (asset cards with score + critic notes + Approve / Regenerate). Keep state in Riverpod; isolate API/SSE in `services/`.

---

## 13. Conventions & constraints

- Async everywhere on the backend.
- Type everything; run ruff + black in CI.
- No secrets in code; `.env` + `.env.example`.
- Structured logging on every LLM call (inputs, model, latency, token usage) — sets up v2 observability cleanly.
- Keep the LLM provider swappable; never import a provider SDK outside `llm/client.py`.
- Write a unit test for: guardrail checks, the eval judge parsing, and the conditional-edge routing.

---

## 14. Build order (do in sequence; finish each before moving on)

1. Scaffold repo, `config.py`, `.env.example`, `llm/client.py` (with JSON-validated calls), `GET /health`.
2. Define all Pydantic models in `models.py`.
3. Copywriter agent: brief → drafts, schema-validated. Test it.
4. Critic: guardrail checks + eval judge → `GuardrailResult` + `EvalScore`. Test both.
5. Strategist agent: brief → `CampaignPlan`.
6. LangGraph wiring: strategist → copywriter ↔ critic loop with threshold + max-iters. Test the routing.
7. FastAPI endpoints + SSE streaming + SQLite persistence.
8. Flutter app: brief → live run → review/approve.
9. Dockerize + docker-compose + GitHub Actions.
10. Deploy to free tier; write README with an architecture diagram + the four-pillar talking points.

---

## 15. Definition of done (v1)

- Submit a brief → watch agents work live → get 2–3 scored, guardrail-checked assets → approve or regenerate.
- The revision loop demonstrably improves a deliberately weak first draft.
- Guardrails block a brief that requests a false/absolute claim.
- The eval judge runs against the golden set and matches expected pass/fail.
- Runs end-to-end from a fresh `docker-compose up`.
- Deployed and reachable; README explains the architecture and why each pillar exists.

---

## 16. Open TODOs (decide later, don't block v1)

- Pick the single free-tier deploy target.
- Choose default LLM provider/model (env-driven).
- v3 corpus for brand-voice RAG.
- Target platforms for the v2 publishing layer (then verify their current API/OAuth terms).
