"""
Test multi-browser long-polling to verify items appear in all connected browsers
"""
import pytest
from playwright.sync_api import Page, expect, Browser
import time


@pytest.fixture
def live_server():
    """Use the live server fixture from features/conftest.py"""
    import threading
    import uvicorn
    from main_test_suite import app

    port = 8766
    server_url = f"http://localhost:{port}"

    def run_server():
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="error")

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(1)

    yield server_url


def test_multi_browser_long_polling(browser: Browser, live_server):
    """Test that items created in one browser appear in another browser via long-polling"""
    # Reset items list
    from main_test_suite import items_list
    items_list.clear()

    # Create two browser contexts (simulating two different users/sessions)
    context1 = browser.new_context()
    context2 = browser.new_context()

    page1 = context1.new_page()
    page2 = context2.new_page()

    try:
        # Both browsers navigate to the app
        print(f"\n=== Browser 1: Navigating to {live_server} ===")
        page1.goto(live_server)
        page1.wait_for_selector('input[name="name"]', timeout=5000)

        print(f"=== Browser 2: Navigating to {live_server} ===")
        page2.goto(live_server)
        page2.wait_for_selector('input[name="name"]', timeout=5000)

        # Browser 1 adds "Item 1"
        print("\n=== Browser 1: Adding 'Item 1' ===")
        page1.fill('input[name="name"]', "Item 1")
        page1.click("button[type='submit']")
        time.sleep(0.5)

        # Wait for Item 1 to appear in both browsers
        print("=== Waiting for 'Item 1' to appear in Browser 1 ===")
        item1_browser1 = page1.locator(".item").filter(has_text="Item 1")
        expect(item1_browser1).to_be_visible(timeout=5000)
        print("✓ Item 1 visible in Browser 1")

        print("=== Waiting for 'Item 1' to appear in Browser 2 ===")
        item1_browser2 = page2.locator(".item").filter(has_text="Item 1")
        expect(item1_browser2).to_be_visible(timeout=5000)
        print("✓ Item 1 visible in Browser 2")

        # Browser 2 adds "Item 2"
        print("\n=== Browser 2: Adding 'Item 2' ===")
        page2.fill('input[name="name"]', "Item 2")
        page2.click("button[type='submit']")
        time.sleep(0.5)

        # Wait for Item 2 to appear in both browsers
        print("=== Waiting for 'Item 2' to appear in Browser 2 ===")
        item2_browser2 = page2.locator(".item").filter(has_text="Item 2")
        expect(item2_browser2).to_be_visible(timeout=5000)
        print("✓ Item 2 visible in Browser 2")

        print("=== Waiting for 'Item 2' to appear in Browser 1 ===")
        item2_browser1 = page1.locator(".item").filter(has_text="Item 2")
        expect(item2_browser1).to_be_visible(timeout=5000)
        print("✓ Item 2 visible in Browser 1")

        # Browser 1 adds "Item 3"
        print("\n=== Browser 1: Adding 'Item 3' ===")
        page1.fill('input[name="name"]', "Item 3")
        page1.click("button[type='submit']")
        time.sleep(0.5)

        # Wait for Item 3 to appear in both browsers
        print("=== Waiting for 'Item 3' to appear in Browser 1 ===")
        item3_browser1 = page1.locator(".item").filter(has_text="Item 3")
        expect(item3_browser1).to_be_visible(timeout=5000)
        print("✓ Item 3 visible in Browser 1")

        print("=== Waiting for 'Item 3' to appear in Browser 2 ===")
        item3_browser2 = page2.locator(".item").filter(has_text="Item 3")
        expect(item3_browser2).to_be_visible(timeout=5000)
        print("✓ Item 3 visible in Browser 2")

        # Verify both browsers have all 3 items
        print("\n=== Final verification ===")
        items_browser1 = page1.locator(".item")
        items_browser2 = page2.locator(".item")

        expect(items_browser1).to_have_count(3, timeout=2000)
        expect(items_browser2).to_have_count(3, timeout=2000)

        print("✓ Browser 1 has 3 items")
        print("✓ Browser 2 has 3 items")
        print("\n=== Test PASSED ===\n")

    finally:
        context1.close()
        context2.close()
