"""ScamShield API — application factory.

Builds the DI :class:`Container` from settings, mounts routers, and exposes a
liveness/readiness endpoint. Runs on the in-memory repo + broker by default, so
``uvicorn app.main:app`` works with no Postgres/Redis. Set ``DATABASE_URL`` /
``REDIS_URL`` to switch to the production adapters (selection is in ``deps.py``).
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import Settings, get_settings
from .core.deps import Container
from .routes import analysis, auth, calls, reports, ws


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(
        title="ScamShield API",
        version="0.1.0",
        description="Defensive real-time scam-call detection. Live transcript in, "
                    "explainable risk out. Not a tool for deceiving anyone.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Composition root — one container per app instance.
    app.state.container = Container(settings)

    @app.get("/health", tags=["meta"])
    async def health() -> dict:
        c: Container = app.state.container
        llm = getattr(c.pipeline.stages[-1], "provider", None)
        return {
            "status": "ok",
            "storage": "postgres" if settings.using_postgres else "in-memory",
            "broker": "redis" if settings.using_redis else "in-memory",
            "llm_provider": getattr(llm, "name", settings.llm_provider),
            "llm_model": getattr(llm, "model", None),
            "scam_categories": len(__import__("scamshield_ai.categories",
                                              fromlist=["CATEGORIES"]).CATEGORIES),
        }

    app.include_router(auth.router)
    app.include_router(calls.router)
    app.include_router(calls.stats_router)
    app.include_router(analysis.router)
    app.include_router(reports.router)
    app.include_router(ws.router)
    return app


app = create_app()
