"""Unit tests for the EventBus class."""

import pytest
import asyncio
from typing import Dict, Any, List
from main_test_suite import EventBus


class TestEventBus:
    """Test suite for EventBus class."""

    def test_init(self) -> None:
        """Test EventBus initialization."""
        event_bus: EventBus = EventBus()
        assert event_bus.subscribers == []
        assert isinstance(event_bus.subscribers, list)

    @pytest.mark.asyncio
    async def test_subscribe(self) -> None:
        """Test subscribing to the event bus."""
        event_bus: EventBus = EventBus()
        my_queue: asyncio.Queue[Dict[str, Any]] = await event_bus.subscribe()

        assert isinstance(my_queue, asyncio.Queue)
        assert my_queue in event_bus.subscribers
        assert len(event_bus.subscribers) == 1

    @pytest.mark.asyncio
    async def test_subscribe_multiple(self) -> None:
        """Test multiple subscribers can be added."""
        event_bus: EventBus = EventBus()
        queue1: asyncio.Queue[Dict[str, Any]] = await event_bus.subscribe()
        queue2: asyncio.Queue[Dict[str, Any]] = await event_bus.subscribe()
        queue3: asyncio.Queue[Dict[str, Any]] = await event_bus.subscribe()

        assert len(event_bus.subscribers) == 3
        assert queue1 in event_bus.subscribers
        assert queue2 in event_bus.subscribers
        assert queue3 in event_bus.subscribers
        assert queue1 is not queue2
        assert queue2 is not queue3

    @pytest.mark.asyncio
    async def test_publish_single_subscriber(self) -> None:
        """Test publishing an event to a single subscriber."""
        event_bus: EventBus = EventBus()
        queue: asyncio.Queue[Dict[str, Any]] = await event_bus.subscribe()

        test_event: Dict[str, str] = {"type": "test", "data": "hello"}
        await event_bus.publish(test_event)

        received_event: Dict[str, Any] = await asyncio.wait_for(
            queue.get(), timeout=1.0
        )
        assert received_event == test_event

    @pytest.mark.asyncio
    async def test_publish_multiple_subscribers(self) -> None:
        """Test publishing an event to multiple subscribers."""
        event_bus: EventBus = EventBus()
        queue1: asyncio.Queue[Dict[str, Any]] = await event_bus.subscribe()
        queue2: asyncio.Queue[Dict[str, Any]] = await event_bus.subscribe()
        queue3: asyncio.Queue[Dict[str, Any]] = await event_bus.subscribe()

        test_event: Dict[str, str] = {"type": "test", "data": "broadcast"}
        await event_bus.publish(test_event)

        # All subscribers should receive the same event
        event1: Dict[str, Any] = await asyncio.wait_for(queue1.get(), timeout=1.0)
        event2: Dict[str, Any] = await asyncio.wait_for(queue2.get(), timeout=1.0)
        event3: Dict[str, Any] = await asyncio.wait_for(queue3.get(), timeout=1.0)

        assert event1 == test_event
        assert event2 == test_event
        assert event3 == test_event

    @pytest.mark.asyncio
    async def test_publish_multiple_events(self) -> None:
        """Test publishing multiple events in sequence."""
        event_bus: EventBus = EventBus()
        queue: asyncio.Queue[Dict[str, Any]] = await event_bus.subscribe()

        event1: Dict[str, str] = {"type": "event1", "data": "first"}
        event2: Dict[str, str] = {"type": "event2", "data": "second"}
        event3: Dict[str, str] = {"type": "event3", "data": "third"}

        await event_bus.publish(event1)
        await event_bus.publish(event2)
        await event_bus.publish(event3)

        received1: Dict[str, Any] = await asyncio.wait_for(queue.get(), timeout=1.0)
        received2: Dict[str, Any] = await asyncio.wait_for(queue.get(), timeout=1.0)
        received3: Dict[str, Any] = await asyncio.wait_for(queue.get(), timeout=1.0)

        assert received1 == event1
        assert received2 == event2
        assert received3 == event3

    @pytest.mark.asyncio
    async def test_publish_no_subscribers(self) -> None:
        """Test publishing when there are no subscribers."""
        event_bus: EventBus = EventBus()
        test_event: Dict[str, str] = {"type": "test", "data": "lonely"}

        # Should not raise an exception
        await event_bus.publish(test_event)
        assert len(event_bus.subscribers) == 0

    def test_unsubscribe(self) -> None:
        """Test unsubscribing from the event bus."""
        event_bus: EventBus = EventBus()
        queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        event_bus.subscribers.append(queue)

        assert queue in event_bus.subscribers
        event_bus.unsubscribe(queue)
        assert queue not in event_bus.subscribers

    def test_unsubscribe_nonexistent(self) -> None:
        """Test unsubscribing a queue that was never subscribed."""
        event_bus: EventBus = EventBus()
        queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()

        # Should not raise an exception
        event_bus.unsubscribe(queue)
        assert len(event_bus.subscribers) == 0

    @pytest.mark.asyncio
    async def test_unsubscribe_after_subscribe(self) -> None:
        """Test unsubscribing after subscribing."""
        event_bus: EventBus = EventBus()
        queue1: asyncio.Queue[Dict[str, Any]] = await event_bus.subscribe()
        queue2: asyncio.Queue[Dict[str, Any]] = await event_bus.subscribe()

        assert len(event_bus.subscribers) == 2

        event_bus.unsubscribe(queue1)
        assert len(event_bus.subscribers) == 1
        assert queue1 not in event_bus.subscribers
        assert queue2 in event_bus.subscribers

    @pytest.mark.asyncio
    async def test_publish_after_partial_unsubscribe(self) -> None:
        """Test publishing after some subscribers have unsubscribed."""
        event_bus: EventBus = EventBus()
        queue1: asyncio.Queue[Dict[str, Any]] = await event_bus.subscribe()
        queue2: asyncio.Queue[Dict[str, Any]] = await event_bus.subscribe()
        queue3: asyncio.Queue[Dict[str, Any]] = await event_bus.subscribe()

        # Unsubscribe second subscriber
        event_bus.unsubscribe(queue2)

        test_event: Dict[str, str] = {"type": "test", "data": "partial"}
        await event_bus.publish(test_event)

        # Only queue1 and queue3 should receive the event
        event1: Dict[str, Any] = await asyncio.wait_for(queue1.get(), timeout=1.0)
        event3: Dict[str, Any] = await asyncio.wait_for(queue3.get(), timeout=1.0)

        assert event1 == test_event
        assert event3 == test_event
        assert queue2.empty()

    @pytest.mark.asyncio
    async def test_queue_ordering(self) -> None:
        """Test that events maintain order in the queue."""
        event_bus: EventBus = EventBus()
        queue: asyncio.Queue[Dict[str, Any]] = await event_bus.subscribe()

        events: List[Dict[str, str]] = [
            {"type": "event", "data": "1"},
            {"type": "event", "data": "2"},
            {"type": "event", "data": "3"},
            {"type": "event", "data": "4"},
            {"type": "event", "data": "5"},
        ]

        for event in events:
            await event_bus.publish(event)

        for expected_event in events:
            received: Dict[str, Any] = await asyncio.wait_for(queue.get(), timeout=1.0)
            assert received == expected_event

    @pytest.mark.asyncio
    async def test_concurrent_publish(self) -> None:
        """Test concurrent publishing to multiple subscribers."""
        event_bus: EventBus = EventBus()
        queues: List[asyncio.Queue[Dict[str, Any]]] = [
            await event_bus.subscribe() for _ in range(5)
        ]

        test_event: Dict[str, str] = {"type": "concurrent", "data": "test"}

        # Publish concurrently
        await event_bus.publish(test_event)

        # All queues should receive the event
        tasks: List[asyncio.Task[Dict[str, Any]]] = [
            asyncio.wait_for(q.get(), timeout=1.0) for q in queues
        ]
        results: List[Dict[str, Any]] = await asyncio.gather(*tasks)

        assert all(result == test_event for result in results)

    @pytest.mark.asyncio
    async def test_event_types(self) -> None:
        """Test publishing different types of event data."""
        event_bus: EventBus = EventBus()
        queue: asyncio.Queue[Dict[str, Any]] = await event_bus.subscribe()

        # Test different data types
        events: List[Dict[str, Any]] = [
            {"type": "string", "data": "text"},
            {"type": "number", "data": 42},
            {"type": "list", "data": [1, 2, 3]},
            {"type": "dict", "data": {"nested": "value"}},
            {"type": "none", "data": None},
        ]

        for event in events:
            await event_bus.publish(event)

        for expected_event in events:
            received: Dict[str, Any] = await asyncio.wait_for(queue.get(), timeout=1.0)
            assert received == expected_event
