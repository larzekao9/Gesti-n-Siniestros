"""Pytest configuration: async test fixtures for DB, HTTP client, and seed data."""

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from main import app
from app.core.database import get_db
from app.models.base import Base
from app.models.tenant import Tenant
from app.models.user import Role, User
from app.core.security import hash_password

DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    """Provide an isolated in-memory SQLite session for each test."""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    # Inject the SQLite factory into app.state so TenantMiddleware uses it
    app.state._middleware_session_factory = session_factory

    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    app.state._middleware_session_factory = None
    await engine.dispose()


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncClient:
    """HTTP test client wired to the in-memory test database."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def tenant_a(db_session: AsyncSession) -> Tenant:
    """Seed Tenant A into the test database."""
    tenant = Tenant(name="Aseguradora A", slug="aseguradora-a")
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


@pytest_asyncio.fixture
async def tenant_b(db_session: AsyncSession) -> Tenant:
    """Seed Tenant B into the test database."""
    tenant = Tenant(name="Aseguradora B", slug="aseguradora-b")
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


@pytest_asyncio.fixture
async def user_admin(db_session: AsyncSession, tenant_a: Tenant) -> User:
    """Seed an admin user belonging to Tenant A."""
    user = User(
        email="admin@aseguradora-a.com",
        hashed_password=hash_password("Password123!"),
        full_name="Admin User",
        role=Role.ADMIN,
        tenant_id=tenant_a.id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def user_supervisor(db_session: AsyncSession, tenant_a: Tenant) -> User:
    """Seed a supervisor user belonging to Tenant A."""
    user = User(
        email="supervisor@aseguradora-a.com",
        hashed_password=hash_password("Password123!"),
        full_name="Supervisor User",
        role=Role.SUPERVISOR,
        tenant_id=tenant_a.id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def user_analyst(db_session: AsyncSession, tenant_a: Tenant) -> User:
    """Seed an analyst user belonging to Tenant A."""
    user = User(
        email="analyst@aseguradora-a.com",
        hashed_password=hash_password("Password123!"),
        full_name="Analyst User",
        role=Role.ANALYST,
        tenant_id=tenant_a.id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

