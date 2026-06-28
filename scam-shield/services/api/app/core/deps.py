"""Dependency-injection wiring.

A single :class:`Container` builds the concrete adapters chosen by configuration
(in-memory vs Postgres repository, memory vs Redis broker, stub vs real LLM) and
is stored on ``app.state``. FastAPI ``Depends`` helpers pull collaborators from it,
so routes/handlers never construct their own infrastructure — they declare what
they need and the container provides it.
"""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, Header, HTTPException, Request, status

from scamshield_ai import AnalysisPipeline
from scamshield_ai.llm import get_provider

from ..domain.models import User
from ..realtime.broker import Broker
from ..realtime.memory_broker import MemoryBroker
from ..repositories.base import Repository
from ..repositories.memory import InMemoryRepository
from ..services.analysis_service import AnalysisService
from .config import Settings, get_settings
from .security import TokenError, decode_access_token


class Container:
    """Application composition root."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.repo: Repository = self._build_repo(settings)
        self.broker: Broker = self._build_broker(settings)
        self.pipeline = AnalysisPipeline(llm_provider=self._build_provider(settings))
        self.analysis = AnalysisService(self.repo, self.broker, self.pipeline)

    @staticmethod
    def _build_provider(settings: Settings):
        """Select the LLM-reasoning provider. A real provider (claude/openai) is
        only used when it actually has credentials; otherwise we fall back to the
        deterministic stub so /health reports the truth and we don't make doomed
        calls per utterance."""
        provider = get_provider(settings.llm_provider, model=settings.llm_model,
                                api_key=settings.llm_api_key)
        if getattr(provider, "available", True) is False:
            provider = get_provider("deterministic-stub")
        return provider

    @staticmethod
    def _build_repo(settings: Settings) -> Repository:
        if settings.using_postgres:
            from ..repositories.sql import SqlRepository  # imported only when needed
            return SqlRepository(settings.database_url)  # type: ignore[arg-type]
        return InMemoryRepository()

    @staticmethod
    def _build_broker(settings: Settings) -> Broker:
        if settings.using_redis:
            from ..realtime.redis_broker import RedisBroker
            return RedisBroker(settings.redis_url)  # type: ignore[arg-type]
        return MemoryBroker()


# --------------------------------------------------------------------------- #
# FastAPI dependency helpers
# --------------------------------------------------------------------------- #
def get_container(request: Request) -> Container:
    return request.app.state.container


def get_repo(container: Container = Depends(get_container)) -> Repository:
    return container.repo


def get_broker(container: Container = Depends(get_container)) -> Broker:
    return container.broker


def get_analysis(container: Container = Depends(get_container)) -> AnalysisService:
    return container.analysis


async def get_current_user(
    container: Container = Depends(get_container),
    authorization: Optional[str] = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    user = await _user_from_token(token, container, settings)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid or expired token")
    return user


async def _user_from_token(token: str, container: Container, settings: Settings) -> Optional[User]:
    try:
        payload = decode_access_token(token, settings.jwt_secret)
    except TokenError:
        return None
    return await container.repo.users.get(payload.get("sub", ""))
