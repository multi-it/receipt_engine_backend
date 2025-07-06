import pytest
import asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.database.connection import Base, get_session
from app.database.models import UserModel
from app.auth.security import hash_password, create_access_token
from main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def test_session(test_engine):
    async_session = sessionmaker(
        bind=test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session

@pytest.fixture
async def test_client(test_session):
    def override_get_session():
        return test_session
    
    app.dependency_overrides[get_session] = override_get_session
    # Правильная инициализация для новых версий httpx
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
    app.dependency_overrides.clear()

@pytest.fixture
def sync_test_client(test_session):
    def override_get_session():
        return test_session
    
    app.dependency_overrides[get_session] = override_get_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

@pytest.fixture
async def test_user(test_session):
    user = UserModel(
        fullname="Test User",
        username="testuser",
        email="test@example.com",
        password_hash=hash_password("testpassword123")
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user

@pytest.fixture
def auth_headers(test_user):
    token = create_access_token({"user_id": test_user.id, "username": test_user.username})
    return {"Authorization": f"Bearer {token}"}
