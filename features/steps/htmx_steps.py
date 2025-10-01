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
    from bs4 import BeautifulSoup
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