# ============================================================================
# features/steps/live_update_steps.py - Long-polling Steps
# ============================================================================
import pytest
from pytest_bdd import scenarios, given, when, then
import threading
import time

scenarios("../live_updates.feature")


@given("I am connected to the updates endpoint")
def connect_updates(sync_client, context):
    # Start polling in a background thread
    def poll():
        response = sync_client.get("/updates/poll?timeout=5.0")
        context["polling_response"] = response

    context["polling_thread"] = threading.Thread(target=poll)
    context["polling_thread"].start()
    time.sleep(0.1)  # Let the connection establish


@when("a new item is created")
def create_item(sync_client, context):
    response = sync_client.post("/items", data={"name": "Live Update Item"})
    context["create_response"] = response
    time.sleep(0.1)  # Let the event propagate


@then("I should receive the update notification")
def check_notification(context):
    # Wait for polling thread to complete
    context["polling_thread"].join(timeout=10)
    result = context["polling_response"]
    # Check for HTML content instead of JSON
    assert result.status_code == 200
    assert "Live Update Item" in result.text


@then("the notification should contain the item data")
def check_notification_data(context):
    from bs4 import BeautifulSoup

    result = context["polling_response"]
    soup = BeautifulSoup(result.text, "html.parser")
    assert soup.find(class_="item") is not None
    assert "Live Update Item" in soup.text


@given("I'm connected to the updates endpoint with a short timeout")
def connect_updates_short_timeout(sync_client, context):
    response = sync_client.get("/updates/poll?timeout=0.1")
    context["response"] = response


@when("I wait for the timeout period")
def wait_for_timeout(context):
    time.sleep(0.2)  # Wait slightly longer than timeout


@then("I should receive a timeout response")
def check_timeout(context):
    assert context["response"].status_code == 200
    assert context["response"].text == ""  # Empty HTML on timeout

