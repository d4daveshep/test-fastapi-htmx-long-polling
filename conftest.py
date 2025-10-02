# ============================================================================
# conftest.py - Pytest Configuration and Fixtures
# ============================================================================
from typing import AsyncGenerator, Generator, Dict, Any
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient
from main_test_suite import app, event_bus


@pytest.fixture
def sync_client() -> TestClient:
    """Synchronous TestClient for simple tests"""
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Async client for testing async endpoints"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest_asyncio.fixture
async def reset_event_bus() -> AsyncGenerator[None, None]:
    """Reset event bus before each test"""
    event_bus.subscribers.clear()
    yield
    event_bus.subscribers.clear()


@pytest.fixture(autouse=True)
def reset_event_bus_sync(request):
    """Reset event bus for sync/Playwright tests"""
    # Skip for async tests that use the async fixture
    if "reset_event_bus" in request.fixturenames:
        return
    event_bus.subscribers.clear()
    yield
    event_bus.subscribers.clear()


@pytest.fixture
def bdd_context() -> Dict[str, Any]:
    """Shared context for BDD steps"""
    return {}
