"""Repository interfaces (ports).

Routes depend only on these Protocols, never on a concrete store. The default
adapter is :class:`InMemoryRepository`; :class:`SqlRepository` is the Postgres
production adapter. Selected by configuration in ``core/deps.py``.
"""
from __future__ import annotations

from typing import Optional, Protocol

from ..domain.models import Call, Incident, User


class UserRepository(Protocol):
    async def add(self, user: User) -> User: ...
    async def get_by_email(self, email: str) -> Optional[User]: ...
    async def get(self, user_id: str) -> Optional[User]: ...


class CallRepository(Protocol):
    async def add(self, call: Call) -> Call: ...
    async def get(self, call_id: str) -> Optional[Call]: ...
    async def update(self, call: Call) -> Call: ...
    async def list_for_owner(self, owner_id: str, limit: int = 50) -> list[Call]: ...


class IncidentRepository(Protocol):
    async def add(self, incident: Incident) -> Incident: ...
    async def list_for_owner(self, owner_id: str, limit: int = 50) -> list[Incident]: ...


class Repository(Protocol):
    """Aggregate facade exposing the three sub-repositories."""
    users: UserRepository
    calls: CallRepository
    incidents: IncidentRepository
