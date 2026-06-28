# Prahari — Digital-Arrest Scam Detection & Prevention

**Prahari** (Hindi: *sentinel / guard*) is a **defensive** fraud-detection tool.
It scores how likely a message or call transcript is a **"digital arrest" scam**,
explains *which red flags fired*, and tells the user the safe action to take.

> **Mission / ethics.** Prahari exists to **protect** people from a scam that has
> cost Indian victims thousands of crores. It is **not** a tool for deceiving
> anyone. The synthetic generator produces *labelled examples only* — to train
> and test the classifier — modelled on scams already documented in public
> police cyber-crime advisories.

The "digital arrest" scam: fraudsters impersonate the police, CBI, ED, RBI or
Customs over WhatsApp/Skype video calls, claim the victim is implicated in a
crime (often a "seized parcel containing drugs"), place them under a fake
"digital arrest", isolate them, and coerce money transfers to a "safe account"
to "prove their innocence". **No real agency does any of this.**

---

## What it does

Given a message, Prahari returns an explainable verdict:

```
============== Prahari verdict ==============
  Risk score : 92/100  (Almost Certainly a Scam)
  Verdict    : ⚠ LIKELY SCAM
  ML p(scam) : 0.9998   rule score: 0.8372
  Red flags:
    • 'Digital arrest' / custody language  ("digital arrest")
        'Digital arrest' is not a real legal procedure …
    • Authority impersonation  ("CBI")
    • Demand to transfer money  ("safe account")
    • Requests OTP / bank / ID details  ("OTP")
    • Secrecy / stay-on-the-call pressure  ("Do not tell")
  WHAT TO DO:
    Hang up / stop replying. … Report at https://cybercrime.gov.in
    or call the cyber helpline 1930.
=============================================
```

The **score fuses two signals** so each covers the other's blind spot:

| Signal | Source | Strength |
|---|---|---|
| `rule_score` | Transparent red-flag engine (regex rules) | Always explains *why*; catches obvious scams even with little training data |
| `ml_probability` | TF-IDF + numeric features → LogisticRegression | Generalises to phrasings the rules miss |

`final = 100 × (0.65 · ml_probability + 0.35 · rule_score)`

**Languages.** Indian digital-arrest scripts are often *not* in English. Prahari
detects the same tactics in **English, romanized Hindi ("Hinglish")** —
e.g. *"paise transfer karo, OTP bhejo, warna giraftari ho jayegi"* — **and
Devanagari Hindi** (*"आप डिजिटल अरेस्ट में हैं"*). Both the rule patterns and the
synthetic training data carry all three.

**Web UI.** A self-contained page (`/app`) lets a non-technical person paste a
message and see the verdict, the warning signs, and the safe action — no install,
no build step, and the message never leaves the server.

---

## Architecture

```
src/prahari/
├── config.py            Paths, seeds, label schema, risk bands, dataset specs
├── cli.py               `prahari` command-line entry point
├── data/load.py         Phase 1 — unify Kaggle corpora → data/processed/dataset.csv
├── features/
│   ├── red_flags.py     Phase 2 — explainable weighted rule engine
│   └── text_features.py Phase 2 — numeric/structural features (sklearn transformer)
├── generator/
│   └── templates.py     Phase 3 — synthetic digital-arrest + legit examples
├── models/
│   ├── pipeline.py      Phase 4 — TF-IDF + numeric → LogisticRegression
│   ├── train.py         Phase 4 — fit + persist self-describing artifact
│   ├── predict.py       Phase 4 — score fusion + explanation
│   └── evaluate.py      Phase 4 — held-out metrics + plots → reports/
└── api/
    ├── schemas.py       Phase 5 — pydantic request/response models
    ├── server.py        Phase 5/7 — FastAPI: /health, /score, /app
    └── static/
        └── index.html   Phase 7 — self-contained web UI (no build, no CDN)
tests/                   Phase 6 — pytest suite (36 tests)
```

The red-flag engine and synthetic generator carry **English + Hindi/Hinglish**
patterns (Phase 7), so the same tactics are caught across languages.

---

## Install

```bash
python -m venv .venv
.venv/Scripts/activate            # Windows;  source .venv/bin/activate on macOS/Linux
pip install -e .                  # runtime deps from pyproject.toml
pip install pytest httpx          # for the test suite
```

Optional advanced extras (DistilBERT / SHAP) are feature-flagged in
`pyproject.toml` under `[advanced]` and intentionally kept out of the default
install.

---

## Quick start (no Kaggle download needed for a demo)

```bash
prahari augment        # build a dataset (synthetic-only if data/raw is empty)
prahari train          # → models/prahari_model.joblib
prahari evaluate       # → reports/metrics.json, confusion_matrix.png, roc_curve.png
prahari predict "You are under digital arrest, share the OTP now"
prahari serve          # web UI at http://127.0.0.1:8000/app  (API docs at /docs)
```

Then open **http://127.0.0.1:8000/app** and paste a message (English, Hinglish
or Hindi) to see the explained verdict.

> With no real data, training falls back to a **synthetic-only** corpus (you'll
> see a loud warning, and metrics will be near-perfect because the synthetic
> templates are trivially separable). For a **real** model, add the Kaggle CSVs
> first (below) and re-run `augment`.

### Using the real corpora

Download into `data/raw/` (gitignored), then `prahari augment` blends them with
the synthetic digital-arrest examples:

| Source | Kaggle slug |
|---|---|
| SMS spam/ham | `uciml/sms-spam-collection-dataset` |
| Fraud emails | `llabhishekll/fraud-email-dataset` |
| Phishing emails | `subhajournal/phishingemails` |

The loader is tolerant: it finds files by glob, sniffs encodings, and
auto-detects the text/label columns, skipping any missing source with a warning.

---

## CLI reference

| Command | Phase | Description |
|---|---|---|
| `prahari build-data` | 1 | Unify Kaggle corpora only |
| `prahari augment` | 3 | Add synthetic digital-arrest examples, write dataset |
| `prahari train` | 4 | Train the detector |
| `prahari evaluate` | 4 | Held-out metrics + plots → `reports/` |
| `prahari predict "<text>"` | 4 | Score one message (`--json` for machine output) |
| `prahari serve` | 5 | Launch the FastAPI server |
| `prahari gen-fixtures` | 6 | Write synthetic labelled test fixtures |

## HTTP API

```bash
curl -s localhost:8000/score -H "content-type: application/json" \
  -d '{"text":"CBI: you are under digital arrest, transfer Rs 50000 and share the OTP."}'
```

| Route | Method | Purpose |
|---|---|---|
| `/app` | GET | Human-facing web UI (paste a message → explained verdict) |
| `/score` | POST | Score one message, returns the JSON verdict |
| `/health` | GET | Liveness + whether a model is loaded |
| `/docs` | GET | Interactive OpenAPI docs |

`GET /health` reports liveness and whether a model is loaded; the model loads
lazily so the server starts before training.

---

## Tests

```bash
pytest            # 36 tests: red flags, features, loader, generator, predict,
                  #           multilingual (Hindi/Hinglish), API + web UI
```

The test suite trains a small model on synthetic data (session fixture), so it
is fully self-contained.

---

## Safe action (if you receive such a call)

Hang up / stop replying. No real police, CBI, ED, RBI or Cyber Crime official
arrests you over WhatsApp or a video call, and none will ever ask you to
transfer money to "prove your innocence" or for "safe custody". Do not share
OTPs or bank details. **Report at https://cybercrime.gov.in or call 1930.**

## License

MIT.
