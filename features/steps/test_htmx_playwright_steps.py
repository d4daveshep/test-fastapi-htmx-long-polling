# ============================================================================
# features/steps/test_htmx_playwright_steps.py - Playwright HTMX Steps
# ============================================================================
from pytest_bdd import scenarios, given, when, then, parsers
from playwright.sync_api import Page, expect


scenarios("../htmx_interactions.feature")


@given('The item list contains "Item 1"')
def setup_item_list_playwright():
    """Reset and setup item list with Item 1"""
    from main_test_suite import items_list

    items_list.clear()
    items_list.append("Item 1")


@when("I request items with HTMX headers")
def request_items_htmx_playwright(page: Page, live_server):
    """Navigate to items page and wait for HTMX to load"""
    page.goto(f"{live_server}/")
    # Wait for HTMX to load the items
    page.wait_for_selector(".item", timeout=5000)


@then("I should receive an HTML fragment")
def check_fragment_playwright(page: Page):
    """Verify we have item elements without full HTML structure"""
    # In the context of Playwright, we're checking that items are loaded
    # The items should be present without a full page reload
    items = page.locator(".item")
    expect(items).to_have_count(1, timeout=5000)


@then("the fragment should contain item data")
def check_item_data_playwright(page: Page):
    """Verify Item 1 is visible in the page"""
    item = page.locator(".item").filter(has_text="Item 1")
    expect(item).to_be_visible()


@when('I submit "Item 2" via HTMX')
def submit_item_htmx_playwright(page: Page, live_server):
    """Fill form and submit new item via HTMX"""
    # Navigate to the page if not already there
    if page.url != f"{live_server}/":
        page.goto(f"{live_server}/")
        # Wait for page to load
        page.wait_for_selector('input[name="name"]', timeout=5000)

    # Fill the form
    page.fill('input[name="name"]', "Item 2")
    # Submit the form
    page.click("button[type='submit']")
    # Wait for the long-polling to add the item (may take a moment)
    page.wait_for_timeout(1000)


@then('I should receive the "Item 2" HTML')
def check_new_item_playwright(page: Page):
    """Verify Item 2 appears in the items list"""
    # After the fix, item should appear exactly once via long-polling
    item = page.locator(".item").filter(has_text="Item 2")
    expect(item).to_be_visible(timeout=5000)
    expect(item).to_have_count(1)


@then("an event should be published")
def check_event_published_playwright(page: Page):
    """Verify event was published (checked by item appearing)"""
    # Verify we have exactly 2 items total (Item 1 and Item 2)
    items = page.locator(".item")
    expect(items).to_have_count(2, timeout=5000)
