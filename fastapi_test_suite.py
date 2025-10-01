# ============================================================================
# main.py - Your FastAPI Application
# ============================================================================
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import asyncio
from datetime import datetime

# Event system for long-polling
class EventBus:
    def __init__(self):
        self.subscribers = []
    
    async def subscribe(self):
        queue = asyncio.Queue()
        self.subscribers.append(queue)
        return queue
    
    async def publish(self, event):
        for queue in self.subscribers:
            await queue.put(event)
    
    def unsubscribe(self, queue):
        if queue in self.subscribers:
            self.subscribers.remove(queue)

event_bus = EventBus()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown
    event_bus.subscribers.clear()

app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "Welcome to Live Updates"
    })

@app.get("/items", response_class=HTMLResponse)
async def get_items(request: Request):
    items = ["Item 1", "Item 2", "Item 3"]
    is_htmx = request.headers.get("HX-Request") == "true"
    
    if is_htmx:
        return templates.TemplateResponse("partials/items.html", {
            "request": request,
            "items": items
        })
    
    return templates.TemplateResponse("items.html", {
        "request": request,
        "items": items
    })

@app.post("/items", response_class=HTMLResponse)
async def create_item(request: Request):
    form = await request.form()
    item_name = form.get("name")
    
    # Publish event to subscribers
    await event_bus.publish({
        "type": "item_created",
        "data": item_name,
        "timestamp": datetime.now().isoformat()
    })
    
    return templates.TemplateResponse("partials/item.html", {
        "request": request,
        "item": item_name
    })

@app.get("/updates/poll", response_class=HTMLResponse)
async def poll_updates(request: Request, timeout: float = 30.0):
    """Long-polling endpoint for live updates - returns HTML for HTMX"""
    queue = await event_bus.subscribe()
    
    try:
        event = await asyncio.wait_for(queue.get(), timeout=timeout)
        # Return HTML fragment with the new item
        return templates.TemplateResponse("partials/item.html", {
            "request": request,
            "item": event["data"]
        })
    except asyncio.TimeoutError:
        # Return empty response and reconnect
        return ""
    finally:
        event_bus.unsubscribe(queue)

@app.get("/health")
async def health():
    return {"status": "healthy"}


# ============================================================================
# conftest.py - Pytest Configuration and Fixtures
# ============================================================================
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient
from main import app, event_bus

@pytest.fixture
def sync_client():
    """Synchronous TestClient for simple tests"""
    return TestClient(app)

@pytest_asyncio.fixture
async def async_client():
    """Async client for testing async endpoints"""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client

@pytest_asyncio.fixture(autouse=True)
async def reset_event_bus():
    """Reset event bus before each test"""
    event_bus.subscribers.clear()
    yield
    event_bus.subscribers.clear()

@pytest.fixture
def context():
    """Shared context for BDD steps"""
    return {}


# ============================================================================
# features/homepage.feature - BDD Feature File
# ============================================================================
"""
Feature: Homepage
    As a user
    I want to visit the homepage
    So that I can see the welcome message

    Scenario: User visits homepage
        When I visit the home page
        Then I should see the welcome message
        And the page should have the correct title
"""


# ============================================================================
# features/htmx_interactions.feature - HTMX Feature File
# ============================================================================
"""
Feature: HTMX Interactions
    As a user
    I want to use HTMX to load content dynamically
    So that I can have a smooth user experience

    Scenario: Load items via HTMX
        When I request items with HTMX headers
        Then I should receive an HTML fragment
        And the fragment should contain item data

    Scenario: Create item via HTMX
        When I submit a new item via HTMX
        Then I should receive the new item HTML
        And an event should be published
"""


# ============================================================================
# features/live_updates.feature - Long-polling Feature File
# ============================================================================
"""
Feature: Live Updates
    As a user
    I want to receive live updates
    So that I can see changes in real-time

    Scenario: Receive update via long-polling
        Given I am connected to the updates endpoint
        When a new item is created
        Then I should receive the update notification
        And the notification should contain the item data

    Scenario: Long-polling timeout
        When I connect to updates with a short timeout
        Then I should receive a timeout response
"""


# ============================================================================
# features/steps/page_steps.py - Homepage Steps
# ============================================================================
from pytest_bdd import scenarios, given, when, then, parsers
from bs4 import BeautifulSoup

scenarios('../homepage.feature')

@when('I visit the home page')
def visit_home(sync_client, context):
    context['response'] = sync_client.get("/")

@then('I should see the welcome message')
def check_welcome(context):
    assert context['response'].status_code == 200
    soup = BeautifulSoup(context['response'].text, 'html.parser')
    assert "Welcome" in soup.text

@then('the page should have the correct title')
def check_title(context):
    soup = BeautifulSoup(context['response'].text, 'html.parser')
    title = soup.find('title')
    assert title is not None
    assert "Welcome to Live Updates" in title.text


# ============================================================================
# features/steps/htmx_steps.py - HTMX Steps
# ============================================================================
from pytest_bdd import scenarios, when, then
import asyncio

scenarios('../htmx_interactions.feature')

@when('I request items with HTMX headers')
def request_items_htmx(sync_client, context):
    context['response'] = sync_client.get(
        "/items",
        headers={"HX-Request": "true"}
    )

@then('I should receive an HTML fragment')
def check_fragment(context):
    assert context['response'].status_code == 200
    # Fragment shouldn't have full HTML structure
    assert "<html>" not in context['response'].text.lower()

@then('the fragment should contain item data')
def check_item_data(context):
    soup = BeautifulSoup(context['response'].text, 'html.parser')
    assert "Item 1" in soup.text

@when('I submit a new item via HTMX')
def submit_item_htmx(sync_client, context):
    context['response'] = sync_client.post(
        "/items",
        data={"name": "New Test Item"},
        headers={"HX-Request": "true"}
    )

@then('I should receive the new item HTML')
def check_new_item(context):
    assert context['response'].status_code == 200
    assert "New Test Item" in context['response'].text

@then('an event should be published')
def check_event_published(context):
    # Event publishing is verified in async tests
    assert context['response'].status_code == 200


# ============================================================================
# features/steps/live_update_steps.py - Long-polling Steps
# ============================================================================
import pytest
from pytest_bdd import scenarios, given, when, then
import asyncio

scenarios('../live_updates.feature')

@pytest.fixture
def polling_task(context):
    context['polling_task'] = None
    yield
    if context.get('polling_task') and not context['polling_task'].done():
        context['polling_task'].cancel()

@given('I am connected to the updates endpoint')
@pytest.mark.asyncio
async def connect_updates(async_client, context, polling_task):
    async def poll():
        response = await async_client.get("/updates/poll?timeout=5.0")
        return response
    
    context['polling_task'] = asyncio.create_task(poll())
    await asyncio.sleep(0.1)  # Let the connection establish

@when('a new item is created')
@pytest.mark.asyncio
async def create_item(async_client, context):
    response = await async_client.post(
        "/items",
        data={"name": "Live Update Item"}
    )
    context['create_response'] = response
    await asyncio.sleep(0.1)  # Let the event propagate

@then('I should receive the update notification')
@pytest.mark.asyncio
async def check_notification(context):
    result = await context['polling_task']
    # Check for HTML content instead of JSON
    assert result.status_code == 200
    assert 'Live Update Item' in result.text

@then('the notification should contain the item data')
@pytest.mark.asyncio
async def check_notification_data(context):
    result = await context['polling_task']
    soup = BeautifulSoup(result.text, 'html.parser')
    assert soup.find(class_='item') is not None
    assert 'Live Update Item' in soup.text

@when('I connect to updates with a short timeout')
@pytest.mark.asyncio
async def connect_short_timeout(async_client, context):
    response = await async_client.get("/updates/poll?timeout=0.1")
    context['response'] = response

@then('I should receive a timeout response')
def check_timeout(context):
    assert context['response'].status_code == 200
    assert context['response'].text == ""  # Empty HTML on timeout


# ============================================================================
# tests/test_integration.py - Integration Tests
# ============================================================================
import pytest
import asyncio

@pytest.mark.asyncio
async def test_full_flow_with_multiple_subscribers(async_client):
    """Test multiple clients receiving updates simultaneously"""
    
    # Create two polling tasks
    async def poll_updates(client_id):
        response = await async_client.get("/updates/poll?timeout=5.0")
        return client_id, response
    
    task1 = asyncio.create_task(poll_updates("client1"))
    task2 = asyncio.create_task(poll_updates("client2"))
    
    # Wait for connections to establish
    await asyncio.sleep(0.1)
    
    # Create an item
    await async_client.post("/items", data={"name": "Broadcast Item"})
    
    # Both clients should receive the update
    results = await asyncio.gather(task1, task2)
    
    for client_id, response in results:
        assert response.status_code == 200
        assert "Broadcast Item" in response.text
        soup = BeautifulSoup(response.text, 'html.parser')
        assert soup.find(class_='item') is not None

@pytest.mark.asyncio
async def test_htmx_and_polling_integration(async_client):
    """Test that HTMX post triggers polling updates"""
    
    # Start polling
    poll_task = asyncio.create_task(
        async_client.get("/updates/poll?timeout=5.0")
    )
    
    await asyncio.sleep(0.1)
    
    # Create item via HTMX
    response = await async_client.post(
        "/items",
        data={"name": "HTMX Created Item"},
        headers={"HX-Request": "true"}
    )
    
    assert response.status_code == 200
    assert "HTMX Created Item" in response.text
    
    # Check polling received the update as HTML
    poll_response = await poll_task
    
    assert poll_response.status_code == 200
    assert "HTMX Created Item" in poll_response.text
    
    # Verify it's a proper HTML fragment
    soup = BeautifulSoup(poll_response.text, 'html.parser')
    assert soup.find(class_='item') is not None

def test_health_check(sync_client):
    """Simple synchronous test"""
    response = sync_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


# ============================================================================
# templates/index.html - Base Template
# ============================================================================
"""
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
</head>
<body>
    <h1>Welcome to Live Updates</h1>
    
    <!-- Items list with initial load -->
    <div id="items" hx-get="/items" hx-trigger="load">
        Loading...
    </div>
    
    <!-- Form to add new items -->
    <form hx-post="/items" hx-target="#items" hx-swap="beforeend">
        <input type="text" name="name" placeholder="Item name">
        <button type="submit">Add Item</button>
    </form>
    
    <!-- HTMX long-polling for live updates -->
    <div hx-get="/updates/poll" 
         hx-trigger="load, every 100ms from:body" 
         hx-target="#items" 
         hx-swap="beforeend">
    </div>
</body>
</html>
"""


# ============================================================================
# templates/partials/items.html - Items Fragment
# ============================================================================
"""
{% for item in items %}
<div class="item">{{ item }}</div>
{% endfor %}
"""


# ============================================================================
# templates/partials/item.html - Single Item Fragment
# ============================================================================
"""
<div class="item">{{ item }}</div>
"""


# ============================================================================
# pytest.ini - Pytest Configuration
# ============================================================================
"""
[pytest]
asyncio_mode = auto
testpaths = tests features
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    asyncio: mark test as async
addopts = 
    -v
    --strict-markers
    --tb=short
"""


# ============================================================================
# requirements.txt - Dependencies
# ============================================================================
"""
fastapi==0.109.0
uvicorn==0.27.0
jinja2==3.1.3
python-multipart==0.0.6
httpx==0.26.0
pytest==8.0.0
pytest-asyncio==0.23.3
pytest-bdd==7.0.1
beautifulsoup4==4.12.3
"""