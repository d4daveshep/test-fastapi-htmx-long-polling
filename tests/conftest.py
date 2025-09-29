import pytest
from fastapi.testclient import TestClient
import asyncio
from unittest.mock import patch
import time


@pytest.fixture
def main_client():
    """Test client for the main notification system"""
    from main import app, notifications, notification_counter

    # Clear notifications before each test
    notifications.clear()

    # Reset counter
    import main
    main.notification_counter = 0

    with TestClient(app) as client:
        yield client


@pytest.fixture
def polling_client():
    """Test client for the event polling system"""
    from test_long_polling import app, latest_events, user_event_notifiers, event_generator

    # Clear events before each test
    latest_events.clear()
    user_event_notifiers.clear()

    # Reset event generator
    event_generator.started = False

    with TestClient(app) as client:
        yield client


@pytest.fixture
def mock_time():
    """Mock time.time() for consistent testing"""
    with patch('time.time', return_value=1640995200.0):  # 2022-01-01 00:00:00 UTC
        yield


@pytest.fixture
def sample_notifications():
    """Sample notifications for testing"""
    return [
        {
            "id": 1,
            "type": "info",
            "message": "Test notification 1",
            "timestamp": 1640995200.0,
            "datetime": "2022-01-01 00:00:00"
        },
        {
            "id": 2,
            "type": "success",
            "message": "Test notification 2",
            "timestamp": 1640995260.0,
            "datetime": "2022-01-01 00:01:00"
        }
    ]


@pytest.fixture
def populate_notifications(main_client, sample_notifications):
    """Populate the main app with sample notifications"""
    from main import notifications
    notifications.extend(sample_notifications)
    yield
    notifications.clear()


@pytest.fixture
def populate_events(polling_client):
    """Populate the polling app with sample events"""
    from test_long_polling import latest_events
    latest_events["alice"] = ["Event 1 for Alice", "Event 2 for Alice"]
    latest_events["bob"] = ["Event 1 for Bob"]
    yield
    latest_events.clear()