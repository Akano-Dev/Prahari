"""FastAPI application exposing the scam detector over HTTP.

Endpoints
---------
* ``GET  /``        — tiny human-readable landing blurb + mission note (JSON).
* ``GET  /app``     — the self-contained web UI (paste a message, see the verdict).
* ``GET  /health``  — liveness + whether a trained model is loaded.
* ``POST /score``   — score one message; returns the explainable verdict.

The app loads the model lazily on first ``/score`` so the server still starts
(and ``/health`` still answers) before a model has been trained.

Run with::

    prahari serve            # or: uvicorn prahari.api.server:app --reload
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from prahari import __version__, config
from prahari.api.schemas import HealthResponse, ScoreRequest, ScoreResponse
from prahari.models import predict as predict_mod

# The web UI is a single self-contained file (no build step, no CDN calls) so
# it works offline and never leaks the user's message to a third party.
_UI_PATH = Path(__file__).parent / "static" / "index.html"

app = FastAPI(
    title="Prahari — Digital-Arrest Scam Detector",
    version=__version__,
    description=(
        "Defensive fraud-detection API. Scores how likely a message is a "
        "'digital arrest' scam, lists the red flags, and returns the official "
        "safe action. Not a tool for deceiving anyone."
    ),
)


def _try_load() -> dict | None:
    try:
        return predict_mod.load_model()
    except FileNotFoundError:
        return None


@app.get("/", tags=["meta"])
def root() -> dict:
    return {
        "name": "Prahari",
        "what": "Digital-arrest scam detection & prevention (defensive).",
        "endpoints": ["/app", "/health", "/score (POST)", "/docs"],
        "safe_action": config.SAFE_ACTION_MESSAGE,
    }


@app.get("/app", response_class=HTMLResponse, tags=["meta"])
def web_app() -> HTMLResponse:
    """Serve the human-facing web UI (paste a message, get an explained verdict)."""
    try:
        return HTMLResponse(_UI_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:  # pragma: no cover - packaging safeguard
        raise HTTPException(status_code=500, detail="Web UI asset is missing.")


@app.get("/health", response_model=HealthResponse, tags=["meta"])
def health() -> HealthResponse:
    artifact = _try_load()
    return HealthResponse(
        status="ok",
        model_loaded=artifact is not None,
        version=__version__,
        trained_at=artifact.get("trained_at") if artifact else None,
    )


@app.post("/score", response_model=ScoreResponse, tags=["scoring"])
def score(req: ScoreRequest) -> ScoreResponse:
    try:
        result = predict_mod.predict(req.text)
    except FileNotFoundError as exc:
        # No model trained yet — 503 is the honest status here.
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return ScoreResponse(**result)
