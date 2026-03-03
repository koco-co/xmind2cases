# tests/conftest.py
import os
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# 测试文件路径
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs")


@pytest.fixture
def xmind8_file():
    """xmind8 版本测试文件"""
    return os.path.join(DOCS_DIR, "202602-数据资产v6.4.8(xmind8版本).xmind")


@pytest.fixture
def xmind2026_file():
    """xmind2026 版本测试文件"""
    return os.path.join(DOCS_DIR, "202602-数据资产v6.4.8(xmind2026版本).xmind")


@pytest.fixture
def reference_csv():
    """参考 CSV 文件"""
    return os.path.join(DOCS_DIR, "202602-数据资产v6.4.8(xmind8版本).csv")


# API Test Fixtures
@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session():
    """创建测试数据库会话"""
    from api.models.base import Base

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session

    await engine.dispose()


@pytest.fixture(scope="function")
async def client(db_session):
    """创建测试客户端"""
    from api.main import app
    from api.core.database import get_db
    from httpx import ASGITransport

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
