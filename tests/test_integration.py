# ============================================================================
# tests/test_integration.py - Integration Tests
# ============================================================================
from typing import AsyncGenerator
from fastapi.testclient import TestClient
from httpx import AsyncClient, Response
import pytest
import asyncio
from bs4 import BeautifulSoup, Tag


@pytest.mark.asyncio
async def test_full_flow_with_multiple_subscribers(async_client: AsyncClient):
    """Test multiple clients receiving updates simultaneously"""

    # Create two polling tasks
    async def poll_updates(client_id: str) -> tuple[str, Response]:
        response: Response = await async_client.get("/updates/poll?timeout=5.0")
        return client_id, response

    task1: asyncio.Task[tuple[str, Response]] = asyncio.create_task(
        poll_updates("client1")
    )
    task2: asyncio.Task[tuple[str, Response]] = asyncio.create_task(
        poll_updates("client2")
    )

    # Wait for connections to establish
    await asyncio.sleep(0.1)

    # Create an item
    await async_client.post("/items", data={"name": "Broadcast Item"})

    # Both clients should receive the update
    results = await asyncio.gather(task1, task2)

    for client_id, response in results:
        assert response.status_code == 200
        assert "Broadcast Item" in response.text
        soup: BeautifulSoup = BeautifulSoup(response.text, "html.parser")
        item: Tag | None = soup.find(class_="item")
        assert item is not None


@pytest.mark.asyncio
async def test_htmx_and_polling_integration(async_client: AsyncClient):
    """Test that HTMX post triggers polling updates"""

    # Start polling
    poll_task: asyncio.Task[Response] = asyncio.create_task(
        async_client.get("/updates/poll?timeout=5.0")
    )

    # Wait for connections to establish
    await asyncio.sleep(0.1)

    # Create item via HTMX
    response: Response = await async_client.post(
        "/items", data={"name": "HTMX Created Item"}, headers={"HX-Request": "true"}
    )

    assert response.status_code == 200
    assert "HTMX Created Item" in response.text

    # Check polling received the update as HTML
    poll_response: Response = await poll_task

    assert poll_response.status_code == 200
    assert "HTMX Created Item" in poll_response.text

    # Verify it's a proper HTML fragment
    soup: BeautifulSoup = BeautifulSoup(poll_response.text, "html.parser")
    item: Tag | None = soup.find(class_="item")
    assert item is not None


def test_health_check(sync_client: TestClient):
    """Simple synchronous test"""
    response: Response = sync_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

