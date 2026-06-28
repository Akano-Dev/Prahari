# Stage 4 — Real Claude LLM Reasoning in the Engine

**Goal:** Make the `llm_reasoning` stage use the **real Claude API** for
genuine, fluent explanations and edge-case judgement — while keeping the
**deterministic stages as the sole decider** of the verdict (explainable,
auditable, and still works with the LLM offline).

## Design rules (must hold)
- **Claude explains, never decides.** `risk_scoring` (rules + patterns +
  behaviour + semantics) sets `is_scam` / `risk_score`. Claude output only fills
  `reasoning` and *advisory* nudges — it can never flip a verdict.
- **Graceful degradation.** Default provider stays the deterministic stub. Claude
  is selected only when `SCAMSHIELD_LLM_PROVIDER=claude` **and**
  `ANTHROPIC_API_KEY` is set. Any API error → fall back to the stub, log, keep
  serving. No key, no network → app still boots and scores.
- **Privacy.** Off by default; only the transcript needed for reasoning is sent,
  and only when explicitly enabled. Documented in ARCHITECTURE/README.

## Scope / tasks
- [ ] Consult the `claude-api` skill first for current model IDs, SDK usage,
      and params (do not hardcode from memory).
- [ ] Implement `ClaudeProvider` in `packages/ai_engine/.../llm/providers.py`
      behind the existing `LLMProvider` base: builds a tight system+user prompt
      from the deterministic findings, calls Claude (default model:
      `claude-sonnet-4-6`, configurable via `SCAMSHIELD_LLM_MODEL`), returns
      reasoning text + optional advisory note. Timeout + try/except → stub.
- [ ] Provider selection in the engine/container by env; `anthropic` SDK as an
      **optional** dependency (`[llm]` extra) — never required for default boot.
- [ ] `/health` reports the active provider (already wired) + model.
- [ ] Tests: provider falls back cleanly when no key (no network call); verdict
      is unchanged whether Claude is on or off (determinism guarantee). Mock the
      client — no live API call in CI.
- [ ] Docs: how to enable (env), cost/privacy note.

## Files
- `packages/ai_engine/scamshield_ai/llm/providers.py`, `base.py`
- `packages/ai_engine/scamshield_ai/stages/llm_reasoning.py`
- `packages/ai_engine/pyproject.toml` (`[project.optional-dependencies] llm`)
- `services/api/app/core/{config,deps}.py` (pass provider/model/key through)
- `packages/ai_engine/tests/test_llm_reasoning.py` (new)
- `docs/ARCHITECTURE.md` / `README.md` (enable + privacy note)

## Out of scope
- Local transformer/embedding models (a separate future stage if wanted).
- Replacing deterministic scoring with the LLM (explicitly forbidden).

## Acceptance criteria
- With no key: identical verdicts, stub reasoning, all tests green, app boots.
- With `SCAMSHIELD_LLM_PROVIDER=claude` + key: `reasoning` comes from Claude,
  verdict numerically unchanged; errors degrade to stub without 500s.
- `/health` shows `llm_provider: claude` + model when enabled.
