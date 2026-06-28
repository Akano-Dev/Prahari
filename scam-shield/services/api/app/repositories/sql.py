"""SQLAlchemy / Postgres repository — the production adapter.

Guarded so importing this module is cheap; SQLAlchemy is only imported when a
``SqlRepository`` is actually constructed (i.e. when ``DATABASE_URL`` is set).
Uses the async engine so it fits FastAPI's async stack. Run Alembic migrations
(``infra/``) before first use.
"""
from __future__ import annotations

from typing import Optional

from ..domain.models import Call, Incident, User


def _import_sqlalchemy():
    try:
        import sqlalchemy as sa
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
        from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
    except ImportError as exc:  # pragma: no cover - only hit in prod without dep
        raise RuntimeError(
            "SQLAlchemy not installed. `pip install 'sqlalchemy[asyncio]' asyncpg` "
            "or unset DATABASE_URL to use the in-memory store."
        ) from exc
    return sa, AsyncSession, async_sessionmaker, create_async_engine, DeclarativeBase, Mapped, mapped_column


def build_models():
    """Define ORM tables lazily (keeps SQLAlchemy import out of cold paths)."""
    sa, _AS, _sm, _ce, DeclarativeBase, Mapped, mapped_column = _import_sqlalchemy()

    class Base(DeclarativeBase):
        pass

    class UserRow(Base):
        __tablename__ = "users"
        id: Mapped[str] = mapped_column(sa.String(32), primary_key=True)
        email: Mapped[str] = mapped_column(sa.String(255), unique=True, index=True)
        password_hash: Mapped[str] = mapped_column(sa.String(255))
        display_name: Mapped[str] = mapped_column(sa.String(255), default="")
        avatar: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)
        created_at: Mapped[sa.DateTime] = mapped_column(sa.DateTime(timezone=True))

    class CallRow(Base):
        __tablename__ = "calls"
        id: Mapped[str] = mapped_column(sa.String(32), primary_key=True)
        owner_id: Mapped[str] = mapped_column(sa.String(32), index=True)
        caller_number: Mapped[str] = mapped_column(sa.String(32), default="unknown")
        contact_name: Mapped[Optional[str]] = mapped_column(sa.String(255), nullable=True)
        is_known_contact: Mapped[bool] = mapped_column(sa.Boolean, default=False)
        status: Mapped[str] = mapped_column(sa.String(16), default="active")
        started_at: Mapped[sa.DateTime] = mapped_column(sa.DateTime(timezone=True))
        ended_at: Mapped[Optional[sa.DateTime]] = mapped_column(sa.DateTime(timezone=True), nullable=True)
        utterances: Mapped[dict] = mapped_column(sa.JSON, default=list)
        last_assessment: Mapped[Optional[dict]] = mapped_column(sa.JSON, nullable=True)
        peak_risk: Mapped[int] = mapped_column(sa.Integer, default=0)

    class IncidentRow(Base):
        __tablename__ = "incidents"
        id: Mapped[str] = mapped_column(sa.String(32), primary_key=True)
        call_id: Mapped[str] = mapped_column(sa.String(32), index=True)
        owner_id: Mapped[str] = mapped_column(sa.String(32), index=True)
        risk_score: Mapped[int] = mapped_column(sa.Integer)
        scam_type: Mapped[Optional[str]] = mapped_column(sa.String(64), nullable=True)
        caller_number: Mapped[str] = mapped_column(sa.String(32), default="unknown")
        created_at: Mapped[sa.DateTime] = mapped_column(sa.DateTime(timezone=True))
        assessment: Mapped[dict] = mapped_column(sa.JSON, default=dict)

    return Base, UserRow, CallRow, IncidentRow


class SqlRepository:
    """Async SQLAlchemy implementation of the :class:`Repository` facade.

    Intentionally constructed only when DATABASE_URL is configured. The mapping
    helpers convert between ORM rows and the Pydantic domain models so the rest
    of the app stays storage-agnostic. (Full CRUD bodies are elided to the
    essential operations the routes use.)
    """

    def __init__(self, database_url: str):
        (sa, AsyncSession, async_sessionmaker, create_async_engine,
         *_rest) = _import_sqlalchemy()
        self._engine = create_async_engine(database_url, future=True)
        self._session = async_sessionmaker(self._engine, class_=AsyncSession, expire_on_commit=False)
        self._Base, self._UserRow, self._CallRow, self._IncidentRow = build_models()
        # Concrete sub-repositories share the session factory.
        self.users = _SqlUserRepo(self._session, self._UserRow)
        self.calls = _SqlCallRepo(self._session, self._CallRow)
        self.incidents = _SqlIncidentRepo(self._session, self._IncidentRow)

    async def create_all(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(self._Base.metadata.create_all)


# The concrete sub-repos below follow the same straightforward pattern; kept
# compact since the in-memory repo is the tested default in this scaffold.
class _SqlUserRepo:
    def __init__(self, session, Row):
        self._session, self._Row = session, Row

    async def add(self, user: User) -> User:
        async with self._session() as s:
            s.add(self._Row(**user.model_dump()))
            await s.commit()
        return user

    async def get_by_email(self, email: str) -> Optional[User]:
        import sqlalchemy as sa
        async with self._session() as s:
            row = (await s.execute(sa.select(self._Row).where(self._Row.email == email))).scalar_one_or_none()
            return User.model_validate(row, from_attributes=True) if row else None

    async def get(self, user_id: str) -> Optional[User]:
        async with self._session() as s:
            row = await s.get(self._Row, user_id)
            return User.model_validate(row, from_attributes=True) if row else None

    async def update(self, user: User) -> User:
        async with self._session() as s:
            await s.merge(self._Row(**user.model_dump())); await s.commit()
        return user


class _SqlCallRepo:
    def __init__(self, session, Row):
        self._session, self._Row = session, Row

    async def add(self, call: Call) -> Call:
        async with self._session() as s:
            s.add(self._Row(**call.model_dump())); await s.commit()
        return call

    async def get(self, call_id: str) -> Optional[Call]:
        async with self._session() as s:
            row = await s.get(self._Row, call_id)
            return Call.model_validate(row, from_attributes=True) if row else None

    async def update(self, call: Call) -> Call:
        async with self._session() as s:
            await s.merge(self._Row(**call.model_dump())); await s.commit()
        return call

    async def list_for_owner(self, owner_id: str, limit: int = 50) -> list[Call]:
        import sqlalchemy as sa
        async with self._session() as s:
            rows = (await s.execute(
                sa.select(self._Row).where(self._Row.owner_id == owner_id)
                .order_by(self._Row.started_at.desc()).limit(limit))).scalars().all()
            return [Call.model_validate(r, from_attributes=True) for r in rows]


class _SqlIncidentRepo:
    def __init__(self, session, Row):
        self._session, self._Row = session, Row

    async def add(self, incident: Incident) -> Incident:
        async with self._session() as s:
            s.add(self._Row(**incident.model_dump())); await s.commit()
        return incident

    async def list_for_owner(self, owner_id: str, limit: int = 50) -> list[Incident]:
        import sqlalchemy as sa
        async with self._session() as s:
            rows = (await s.execute(
                sa.select(self._Row).where(self._Row.owner_id == owner_id)
                .order_by(self._Row.created_at.desc()).limit(limit))).scalars().all()
            return [Incident.model_validate(r, from_attributes=True) for r in rows]
