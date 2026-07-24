import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.db.database import get_db
from app.models.base import Base
from app.models.user import User
from app.core.security import hash_password, create_access_token


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create an in-memory SQLite database session for each test."""
    test_engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestAsyncSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)

    async with TestAsyncSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client with overridden database dependency."""
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> User:
    """Fixture that creates and returns a test user in the DB."""
    user = User(
        fullname="Test User",
        email="testuser@example.com",
        hashed_password=hash_password("TestPassword123!"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def authenticated_client(
    client: AsyncClient, test_user: User
) -> AsyncClient:
    """Fixture returning an AsyncClient authenticated with a valid JWT cookie."""
    token = create_access_token(test_user.id)
    client.cookies.set("access_token", token)
    return client
