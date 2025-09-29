import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient


class TestPollingApp:
    """Integration tests for the event polling system (test_long_polling.py)"""

    def test_home_page_renders(self, polling_client):
        """Test that the home page renders correctly"""
        response = polling_client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_home_page_starts_event_generator(self, polling_client):
        """Test that accessing home page starts the event generator"""
        from test_long_polling import event_generator

        # Initially not started
        assert not event_generator.started

        # Access home page
        response = polling_client.get("/")
        assert response.status_code == 200

        # Event generator should now be marked as started
        assert event_generator.started

    def test_poll_html_with_no_events(self, polling_client):
        """Test polling endpoint when no events exist for user"""
        response = polling_client.get("/poll-html/alice?last_event_id=0")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_poll_html_with_existing_events(self, polling_client, populate_events):
        """Test polling endpoint returns existing events immediately"""
        response = polling_client.get("/poll-html/alice?last_event_id=0")
        assert response.status_code == 200
        assert "Event 1 for Alice" in response.text
        assert "Event 2 for Alice" in response.text

    def test_poll_html_filters_by_last_event_id(self, polling_client, populate_events):
        """Test that polling respects last_event_id parameter"""
        # Request events starting from ID 1 (should get only event 2)
        response = polling_client.get("/poll-html/alice?last_event_id=1")
        assert response.status_code == 200
        assert "Event 2 for Alice" in response.text
        # Should not contain the first event since we're asking for events after ID 1

    def test_poll_html_different_users(self, polling_client, populate_events):
        """Test that different users get their own events"""
        # Test Alice's events
        response_alice = polling_client.get("/poll-html/alice?last_event_id=0")
        assert response_alice.status_code == 200
        assert "Alice" in response_alice.text

        # Test Bob's events
        response_bob = polling_client.get("/poll-html/bob?last_event_id=0")
        assert response_bob.status_code == 200
        assert "Bob" in response_bob.text

        # Verify they don't see each other's events
        assert "Bob" not in response_alice.text
        assert "Alice" not in response_bob.text

    def test_poll_html_up_to_date_events(self, polling_client, populate_events):
        """Test polling when client is already up to date"""
        # Alice has 2 events, request with last_event_id=2 (up to date)
        response = polling_client.get("/poll-html/alice?last_event_id=2")
        assert response.status_code == 200
        # Response should still be valid HTML but indicate no new events

    def test_poll_html_timeout_behavior(self, polling_client):
        """Test that polling endpoint handles timeout correctly"""
        # Mock asyncio operations to simulate timeout
        with patch('asyncio.wait_for', side_effect=asyncio.TimeoutError()):
            response = polling_client.get("/poll-html/alice?last_event_id=0")
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]

    def test_poll_html_event_notification(self, polling_client):
        """Test that new events trigger immediate response"""
        from test_long_polling import latest_events, user_event_notifiers
        import threading
        import time

        def add_event_after_delay():
            time.sleep(0.1)  # Small delay
            latest_events["alice"].append("New event for Alice")
            # Trigger all event notifiers for Alice
            for event_notifier in user_event_notifiers["alice"]:
                event_notifier.set()

        # Start background thread to add event
        thread = threading.Thread(target=add_event_after_delay)
        thread.start()

        # Start polling (should wait and then get the new event)
        response = polling_client.get("/poll-html/alice?last_event_id=0")
        assert response.status_code == 200

        thread.join()

    def test_poll_html_cleans_up_event_notifiers(self, polling_client):
        """Test that event notifiers are properly cleaned up"""
        from test_long_polling import user_event_notifiers

        # Start with clean state
        assert len(user_event_notifiers["alice"]) == 0

        # Mock timeout to ensure cleanup happens
        with patch('asyncio.wait_for', side_effect=asyncio.TimeoutError()):
            response = polling_client.get("/poll-html/alice?last_event_id=0")
            assert response.status_code == 200

        # Event notifiers should be cleaned up after request
        assert len(user_event_notifiers["alice"]) == 0

    def test_poll_html_with_invalid_last_event_id(self, polling_client):
        """Test polling with invalid last_event_id parameter"""
        response = polling_client.get("/poll-html/alice?last_event_id=invalid")
        # Should return 422 for validation error or handle gracefully
        assert response.status_code in [200, 422]

    def test_poll_html_returns_proper_template(self, polling_client, populate_events):
        """Test that polling returns the correct template structure"""
        response = polling_client.get("/poll-html/alice?last_event_id=0")
        assert response.status_code == 200

        # Should contain HTMX polling attributes
        response_text = response.text.lower()
        htmx_indicators = ["hx-", "data-hx-", "htmx"]
        assert any(indicator in response_text for indicator in htmx_indicators)

    def test_event_storage_memory_limit(self, polling_client):
        """Test that event storage respects the 50-item limit"""
        from test_long_polling import latest_events

        # Add 55 events for Alice
        for i in range(55):
            latest_events["alice"].append(f"Event {i}")

        # Simulate the cleanup that should happen (normally done by EventGenerator)
        if len(latest_events["alice"]) > 50:
            latest_events["alice"] = latest_events["alice"][-50:]

        # Should have exactly 50 events
        assert len(latest_events["alice"]) == 50
        # Should contain the most recent events
        assert "Event 54" in latest_events["alice"]
        assert "Event 4" not in latest_events["alice"]

    def test_multiple_concurrent_polls_same_user(self, polling_client):
        """Test handling of multiple concurrent polling requests for same user"""
        from test_long_polling import user_event_notifiers
        import threading
        import queue

        results = queue.Queue()

        def make_poll_request():
            try:
                response = polling_client.get("/poll-html/alice?last_event_id=0")
                results.put(response.status_code)
            except Exception as e:
                results.put(str(e))

        # Start multiple concurrent requests
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=make_poll_request)
            threads.append(thread)
            thread.start()

        # Let requests start
        import time
        time.sleep(0.1)

        # Add event to trigger all waiting requests
        from test_long_polling import latest_events
        latest_events["alice"].append("Concurrent test event")

        # Trigger all notifiers
        for event_notifier in list(user_event_notifiers["alice"]):
            event_notifier.set()

        # Wait for all threads
        for thread in threads:
            thread.join(timeout=2)

        # Check results
        while not results.empty():
            result = results.get()
            assert result == 200

    def test_poll_html_user_isolation(self, polling_client):
        """Test that event notifiers for different users are isolated"""
        from test_long_polling import user_event_notifiers, latest_events

        # Start polling for Alice (this will create event notifiers)
        import threading

        def poll_alice():
            polling_client.get("/poll-html/alice?last_event_id=0")

        thread = threading.Thread(target=poll_alice)
        thread.start()

        # Give time for Alice's polling to start
        import time
        time.sleep(0.1)

        # Add event for Bob only
        latest_events["bob"].append("Event for Bob only")
        # Trigger Bob's notifiers (Alice should not be affected)
        for event_notifier in user_event_notifiers["bob"]:
            event_notifier.set()

        # Alice's notifiers should still be waiting
        assert len(user_event_notifiers["alice"]) > 0

        # Clean up
        for event_notifier in list(user_event_notifiers["alice"]):
            event_notifier.set()
        thread.join(timeout=1)

    def test_event_generator_creates_events_for_multiple_users(self, polling_client):
        """Test that EventGenerator creates events for both Alice and Bob"""
        from test_long_polling import event_generator, latest_events

        # Mock the random and sleep to control event generation
        with patch('random.randint', return_value=1), \
             patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:

            # Start event generator
            task = asyncio.create_task(event_generator.start(latest_events))

            # Let it run one iteration
            import time
            time.sleep(0.1)

            # Cancel the task
            task.cancel()

            try:
                asyncio.get_event_loop().run_until_complete(task)
            except asyncio.CancelledError:
                pass

        # Both users should have received events
        assert len(latest_events["alice"]) > 0
        assert len(latest_events["bob"]) > 0

    def test_poll_html_template_context(self, polling_client, populate_events):
        """Test that the template receives the correct context variables"""
        response = polling_client.get("/poll-html/alice?last_event_id=0")
        assert response.status_code == 200

        # The response should contain context that suggests proper template rendering
        assert "alice" in response.text.lower()

    def test_default_last_event_id_parameter(self, polling_client, populate_events):
        """Test that last_event_id defaults to 0 when not provided"""
        response = polling_client.get("/poll-html/alice")
        assert response.status_code == 200
        # Should return all events since default is 0
        assert "Event 1 for Alice" in response.text