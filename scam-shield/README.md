# ScamShield — Real-Time AI Scam-Call Detection Platform

> A **defensive** anti-fraud platform. It listens to a suspicious call *as it
> happens*, detects scam tactics sentence-by-sentence with an explainable hybrid
> AI pipeline, and pushes a live, fully-reasoned verdict to an enterprise
> dashboard. It exists to **protect** people — never to deceive anyone.

ScamShield is a monorepo with four components:

| Component | Path | Stack | Status in this scaffold |
|---|---|---|---|
| **AI Detection Engine** | `packages/ai_engine` | Pure-Python hybrid pipeline | ✅ runs + tested |
| **Backend API** | `services/api` | FastAPI · WS · JWT · (Postgres/Redis ready) | ✅ runs + tested |
| **Web Dashboard** | `apps/dashboard` | React + Vite + TypeScript | 🧱 real scaffold |
| **Android App** | `apps/android` | Kotlin · CallScreeningService · STT · WS | 🧱 real scaffold |

```
              ┌──────────────┐   WebSocket    ┌───────────────────────────┐
   📱 Android │ Call detect  │ ─ transcript ─▶│  FastAPI ingest /ws/calls │
   (speaker   │ + on-device  │                │         │                 │
    mic, with │ STT          │◀── live risk ──│         ▼                 │
    consent)  └──────────────┘                │   AI hybrid pipeline      │
                                              │  (lang→NER→intent→rules→  │
   🖥  Dashboard ◀── live push ── Redis/WS ───│   pattern→semantic→KB→    │
   (enterprise, dark, real-time)              │   LLM-reason→risk fusion) │
                                              │         │                 │
                                              │         ▼  Postgres        │
                                              │   incidents · evidence ·   │
                                              │   reports (PDF)            │
                                              └───────────────────────────┘
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for every major design decision
and the platform-reality constraints (notably: Android cannot tap the live
call-audio stream, so we capture **speaker-mode mic audio with explicit consent**).

## Quick start (engine + backend, runs locally with no Postgres/Redis)

```bash
cd services/api
python -m pip install -e ../../packages/ai_engine -e .
uvicorn app.main:app --reload          # http://127.0.0.1:8000/docs
pytest ../../packages/ai_engine services/api   # from repo root
```

The backend boots with an **in-memory repository + in-memory broker** so it runs
out of the box; set `DATABASE_URL` / `REDIS_URL` to switch to Postgres/Redis.

## Optional: real Claude reasoning

The `llm_reasoning` stage can use the **real Claude API** for fluent,
edge-case-aware explanations. It is **off by default** and **never decides the
verdict** — the deterministic stages set `is_scam`/`risk_score`; Claude only
phrases the "why". Enable it with an Anthropic key:

```bash
pip install -e "packages/ai_engine[llm]"     # installs the anthropic SDK
export SCAMSHIELD_LLM_PROVIDER=claude
export ANTHROPIC_API_KEY=sk-ant-...           # required; without it we stay on the stub
export SCAMSHIELD_LLM_MODEL=claude-opus-4-8   # optional (default)
uvicorn app.main:app
```

`GET /health` then reports `"llm_provider": "claude"` and the model. Any API
error, refusal, or missing key transparently falls back to the deterministic
explanation, so detection never breaks and the app always boots. Transcripts are
only sent to Claude when this is explicitly enabled.

## Reuse note

The detection backbone reuses the proven, **multilingual (English/Hindi/Hinglish)**
red-flag rule engine from the original Prahari project as the deterministic
`rule_engine` + `pattern_matching` stages — explainable and effective with zero
training data — and surrounds it with NER, intent, semantic-similarity, knowledge-
base, and provider-agnostic LLM-reasoning stages.
