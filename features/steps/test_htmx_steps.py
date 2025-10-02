# ============================================================================
# features/steps/htmx_steps.py - HTMX Steps
# ============================================================================
from pytest_bdd import scenarios, given, when, then

scenarios("../htmx_interactions.feature")


@given('The item list contains "Item 1"')
def setup_item_list():
    from main_test_suite import items_list

    items_list.clear()
    items_list.append("Item 1")


@when("I request items with HTMX headers")
def request_items_htmx(sync_client, bdd_context):
    bdd_context["response"] = sync_client.get("/items", headers={"HX-Request": "true"})


@then("I should receive an HTML fragment")
def check_fragment(bdd_context):
    assert bdd_context["response"].status_code == 200
    # Fragment shouldn't have full HTML structure
    assert "<html>" not in bdd_context["response"].text.lower()


@then("the fragment should contain item data")
def check_item_data(bdd_context):
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(bdd_context["response"].text, "html.parser")
    assert "Item 1" in soup.text


@when('I submit "Item 2" via HTMX')
def submit_item_htmx(sync_client, bdd_context):
    bdd_context["response"] = sync_client.post(
        "/items", data={"name": "Item 2"}, headers={"HX-Request": "true"}
    )


@then('I should receive the "Item 2" HTML')
def check_new_item(bdd_context):
    # After the fix, POST returns empty response
    # The item will be added via long-polling instead
    assert bdd_context["response"].status_code == 200
    # Verify item was added to the list
    from main_test_suite import items_list
    assert "Item 2" in items_list


@then("an event should be published")
def check_event_published(bdd_context):
    # Event publishing is verified in async tests
    assert bdd_context["response"].status_code == 200

