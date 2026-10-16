"""
ARGUS — Pytest configuration and shared fixtures.
Uses SQLite in-memory for tests — no PostgreSQL required.
"""

import asyncio
import os

# Override settings BEFORE importing the app
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-" + "x" * 48)
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.security import hash_password
from app.models.user import User, UserRole

# Patch app settings to use test DB before importing app
from app.core import config as _config
_config.settings.DATABASE_URL = "sqlite+aiosqlite:///:memory:"
_config.settings.APP_ENV = "test"

from app.main import app  # noqa: E402 — must come after env override

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Fresh in-memory database per test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestSessionLocal() as session:
        yield session
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession):
    """HTTPX AsyncClient wired to FastAPI with test DB session."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    # Use .example.com — RFC 2606 reserved domain, valid for email validation
    user = User(
        email="admin@example.com",
        username="testadmin",
        full_name="Test Admin",
        hashed_password=hash_password("TestAdmin@123!"),
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def analyst_user(db_session: AsyncSession) -> User:
    user = User(
        email="analyst@example.com",
        username="testanalyst",
        full_name="Test Analyst",
        hashed_password=hash_password("TestAnalyst@123!"),
        role=UserRole.SECURITY_ANALYST,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def viewer_user(db_session: AsyncSession) -> User:
    user = User(
        email="viewer@example.com",
        username="testviewer",
        full_name="Test Viewer",
        hashed_password=hash_password("TestViewer@123!"),
        role=UserRole.VIEWER,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def get_auth_token(client: AsyncClient, email: str, password: str) -> str:
    """Helper: login and return access token."""
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, f"Login failed ({resp.status_code}): {resp.text}"
    return resp.json()["access_token"]
