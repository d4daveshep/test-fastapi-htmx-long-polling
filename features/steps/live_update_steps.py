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
    from bs4 import BeautifulSoup
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