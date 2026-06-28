# ScamShield — Improvement Stages

This folder holds **one scoped `.md` per stage** of the UI/UX + functionality
overhaul requested by the product owner. The point of splitting it up is to keep
each stage **small, shippable, and verifiable** — and to *not over-build*. Each
doc lists its goal, the exact files it touches, acceptance criteria, and an
explicit **Out of scope** section so work doesn't bleed between stages.

## Decisions locked in

| Question | Choice |
|---|---|
| Live-call detection | **Polished live simulator** — realistic incoming-call UX streaming a transcript through the *real* detection pipeline. Fully local, no telephony account. |
| AI upgrade | **Claude LLM reasoning** — wire `llm_reasoning` to the real Claude API. Deterministic stages still *decide* the verdict; Claude only *explains*. |
| Visual direction | **Aurora glass** — dark glassmorphism, neon aurora gradients, frosted cards, big bold hero, glowing risk meter. |

## Stages

| # | Stage | File | Status |
|---|---|---|---|
| 1 | Aurora-glass UI redesign + design system | [STAGE-1-ui-redesign.md](STAGE-1-ui-redesign.md) | ✅ done |
| 2 | Routing, Account page, interactivity, alert+sound | [STAGE-2-interactivity-account-alerts.md](STAGE-2-interactivity-account-alerts.md) | ✅ done |
| 3 | Polished live incoming-call simulator | [STAGE-3-live-call-simulator.md](STAGE-3-live-call-simulator.md) | ✅ done |
| 4 | Real Claude LLM reasoning in the engine | [STAGE-4-ai-claude-reasoning.md](STAGE-4-ai-claude-reasoning.md) | ✅ done |

## Hard boundaries (apply to every stage)

- **Defensive only.** ScamShield detects and explains scams. We will **never**
  build anything that *places* spam/scam/"attack" calls to real phone numbers —
  that is illegal robocalling/harassment and is permanently out of scope.
- **No silent call tapping.** No app can read the remote party's live call audio
  (OS-blocked). "Live call" = a simulator here, or (future) an *inbound* number
  the user owns via a telephony provider, with consent.
- **Graceful degradation stays.** The engine and API must still boot with zero
  external models/keys. New AI is an *optional injected adapter*, never required.
