# ScamShield API

FastAPI backend: JWT auth, live WebSocket transcript ingest, hybrid AI analysis,
incident persistence, and downloadable reports. Runs on **in-memory repo + broker**
by default (no Postgres/Redis needed); set `DATABASE_URL` / `REDIS_URL` to switch
to the production adapters.

```bash
pip install -e ../../packages/ai_engine -e .
uvicorn app.main:app --reload        # http://127.0.0.1:8000/docs
pytest
```

## Endpoints
| Route | Method | Purpose |
|---|---|---|
| `/auth/register`, `/auth/login`, `/auth/me` | POST/GET | JWT auth |
| `/calls` | POST/GET | Create / list calls |
| `/calls/{id}/utterance` | POST | Push one transcript line (HTTP fallback for WS) |
| `/calls/{id}/end` | POST | End a call |
| `/analyze` | POST | One-shot analysis (SMS/screenshot/WhatsApp/voice) |
| `/incidents`, `/stats` | GET | Dashboard overview data |
| `/calls/{id}/report.html`, `.pdf` | GET | Downloadable incident report |
| `/ws/calls/{id}?token=` | WS | Android streams transcript, gets live risk |
| `/ws/dashboard?token=` | WS | Dashboard live assessment feed |
| `/health` | GET | Mode (storage/broker/llm) + category count |

## Layout (`app/`)
`core/` (config, self-contained JWT security, DI container) ·
`domain/` (Pydantic entities) · `repositories/` (interface + memory + SQL) ·
`realtime/` (broker interface + memory + redis) · `services/` (analysis, reports) ·
`schemas/` · `routes/`. Everything depends on interfaces, not concretes — see
`core/deps.py`.
