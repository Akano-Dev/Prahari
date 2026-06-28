"""In-memory repository — the zero-dependency default store.

Thread-safe enough for a single-process dev/test server. It lets the whole API,
WebSocket flow, and test suite run without Postgres. Swap for
:class:`SqlRepository` by setting ``DATABASE_URL``.
"""
from __future__ import annotations

from typing import Optional

from ..domain.models import Call, Incident, User


class InMemoryUserRepository:
    def __init__(self) -> None:
        self._by_id: dict[str, User] = {}
        self._by_email: dict[str, str] = {}

    async def add(self, user: User) -> User:
        self._by_id[user.id] = user
        self._by_email[user.email.lower()] = user.id
        return user

    async def get_by_email(self, email: str) -> Optional[User]:
        uid = self._by_email.get(email.lower())
        return self._by_id.get(uid) if uid else None

    async def get(self, user_id: str) -> Optional[User]:
        return self._by_id.get(user_id)

    async def update(self, user: User) -> User:
        self._by_id[user.id] = user
        self._by_email[user.email.lower()] = user.id
        return user


class InMemoryCallRepository:
    def __init__(self) -> None:
        self._calls: dict[str, Call] = {}

    async def add(self, call: Call) -> Call:
        self._calls[call.id] = call
        return call

    async def get(self, call_id: str) -> Optional[Call]:
        return self._calls.get(call_id)

    async def update(self, call: Call) -> Call:
        self._calls[call.id] = call
        return call

    async def list_for_owner(self, owner_id: str, limit: int = 50) -> list[Call]:
        calls = [c for c in self._calls.values() if c.owner_id == owner_id]
        calls.sort(key=lambda c: c.started_at, reverse=True)
        return calls[:limit]


class InMemoryIncidentRepository:
    def __init__(self) -> None:
        self._incidents: list[Incident] = []

    async def add(self, incident: Incident) -> Incident:
        self._incidents.append(incident)
        return incident

    async def list_for_owner(self, owner_id: str, limit: int = 50) -> list[Incident]:
        items = [i for i in self._incidents if i.owner_id == owner_id]
        items.sort(key=lambda i: i.created_at, reverse=True)
        return items[:limit]


class InMemoryRepository:
    def __init__(self) -> None:
        self.users = InMemoryUserRepository()
        self.calls = InMemoryCallRepository()
        self.incidents = InMemoryIncidentRepository()
