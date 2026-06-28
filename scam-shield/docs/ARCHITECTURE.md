# ScamShield — Architecture & Design Decisions

This document explains **every major design decision** before the code, as
requested. It is the single source of architectural truth.

## 1. Monorepo, four components

```
scam-shield/
├── packages/ai_engine/   Pure-Python hybrid detection pipeline (no web/db deps)
├── services/api/         FastAPI backend (auth, ingest, WS, persistence, reports)
├── apps/dashboard/       React + Vite + TS enterprise dashboard
├── apps/android/         Kotlin app (call detection, on-device STT, WS streaming)
└── infra/                docker-compose, Dockerfiles, env templates
```

**Why a monorepo:** the four components share one contract (the explainable
analysis schema). Co-locating them keeps that contract in lock-step and lets the
dashboard, API, and reports import the *same* Pydantic models.

**Why the engine is a standalone package with no web/db dependencies:** it must
be testable in isolation, embeddable in the API, and reusable from batch jobs
(SMS/screenshot/WhatsApp uploads) — so it depends on nothing but the standard
library + Pydantic.

## 2. Hybrid pipeline, not LLM-only (explicit requirement)

The pipeline is an **ordered chain of dependency-injected stages**, each
implementing a small `Stage` protocol and mutating a shared `ConversationState`:

```
language_detection → ner → intent → rule_engine → pattern_matching
   → semantic_similarity → knowledge_base → llm_reasoning → risk_scoring
```

Design rules:
- **Deterministic stages decide risk; the LLM only explains.** `risk_scoring`
  fuses the deterministic signals (rules, patterns, behaviour, semantics). The
  `llm_reasoning` stage produces human-readable reasoning and *advisory* nudges
  but can never, by itself, flip a verdict. This keeps the system explainable,
  cheap, and robust when the LLM is offline.
- **Graceful degradation.** Heavy stages (semantic embeddings, real NER, real
  LLM) are injected adapters with light deterministic fallbacks, so the whole
  pipeline runs with zero external models or API keys and you upgrade stages
  independently.
- **Sentence-by-sentence over rolling state.** Each utterance produces a
  `risk_delta` and updates a call-level score + behaviour timeline — this is what
  makes detection *live* and the timeline explainable.

## 3. Reuse of the proven rule engine

The original Prahari red-flag engine is multilingual (English/Hindi/Hinglish),
explainable, and works with no training data. It is lifted in verbatim as the
`rule_engine` stage and drives `pattern_matching` (scam-type classification).
Rewriting it would discard tested, working IP for no benefit.

## 4. Explainability is a typed contract, never a bare score

`RiskAssessment` (see `ai_engine/schemas.py`) always carries: behaviour breakdown,
fired signals **with evidence spans**, detected entities, scam-type scores, an
officer-claim consistency check, reasoning text, confidence, recommendation, and a
**timeline**. API, dashboard, and PDF reports all consume this one model.

## 5. Backend: runs-anywhere defaults, production-ready seams

- **Repositories behind interfaces.** Default `InMemoryRepository` boots with no
  database; `SqlRepository` (SQLAlchemy/Postgres) is the production impl, selected
  by `DATABASE_URL`. Wired via FastAPI dependency injection.
- **Realtime broker behind an interface.** Default `MemoryBroker` (in-process
  pub/sub) lets one process fan out WS updates; `RedisBroker` (selected by
  `REDIS_URL`) scales across processes/pods.
- **JWT auth, self-contained.** HS256 implemented on the standard library so auth
  works here with no extra dependency; swappable for PyJWT/Auth0 in production.
- **Reports.** `ReportService` renders the assessment to HTML always, and to PDF
  when `reportlab` is installed (optional dependency).

**Why these seams:** the spec demands Postgres/Redis/Docker for production, but a
scaffold that only runs inside Docker is hard to iterate on. Interfaces + DI give
us both: `pytest` and `uvicorn` work immediately; `docker compose up` gives the
full Postgres/Redis stack.

## 6. Android platform reality (critical, non-obvious)

Since Android 10, third-party apps **cannot record the remote party of a phone
call** — `MediaRecorder`/`AudioRecord`/`SpeechRecognizer` only receive the local
mic / your own voice, and the call audio source is reserved for the system dialer.
Therefore ScamShield's honest, lawful design is:

1. Detect the incoming call via `CallScreeningService` / `PhoneStateListener`.
2. Show caller number, contact name (if `READ_CONTACTS` granted), unknown-caller
   flag, and live duration.
3. Prompt the user (with **explicit, logged consent**) to switch to **speaker**,
   then capture **mic audio** and run on-device STT (`SpeechRecognizer`).
4. Stream transcript chunks over a WebSocket to the backend; render live risk back
   as a high-priority notification.

We never claim to silently tap the call. Consent + speaker-mode is the only
capability actually available, and call-recording legality varies by jurisdiction.

## 7. Scam-type extensibility

Scam categories live in a registry (`ai_engine/categories.py`) keyed by id, each
with matcher patterns and a weight. Adding a category is one entry; nothing else
changes. The 20 required categories ship; more are a data edit.

## 8. Security & privacy posture

- Transcripts are sensitive. The dashboard/UI never call third parties; the LLM
  stage is **off by default** (provider-agnostic stub) and only enabled with an
  explicit provider + key.
- All risk decisions are explainable and locally reproducible from the
  deterministic stages, so the system is auditable.
