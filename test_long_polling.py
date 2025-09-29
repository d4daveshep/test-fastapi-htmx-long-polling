import asyncio
from collections import defaultdict
import random
from typing import Optional, Dict, Set

from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Test Long Polling Events")

# Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Store latest events for each user
latest_events: defaultdict[str, list[str]] = defaultdict(list)
# Store event counters to track what each client has seen
# user_event_counters: defaultdict[str, int] = defaultdict(int)

# Event notification system for proper long polling
user_event_notifiers: Dict[str, Set[asyncio.Event]] = defaultdict(set)


class EventGenerator:
    def __init__(self) -> None:
        self.started: bool = False

    async def start(self, events_storage: defaultdict[str, list[str]]) -> None:
        self.started = True
        while True:
            sleep_time: int = random.randint(5, 10)
            message: str = f"Event: sleeping for {sleep_time} secs"
            print(message)

            # Add event to all user event lists
            for user in ["alice", "bob"]:
                events_storage[user].append(message)
                # Keep only last 50 events per user to prevent memory growth
                if len(events_storage[user]) > 50:
                    events_storage[user] = events_storage[user][-50:]

                # Notify all waiting clients for this user
                for event_notifier in user_event_notifiers[user]:
                    event_notifier.set()

            await asyncio.sleep(float(sleep_time))


event_generator: EventGenerator = EventGenerator()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # Start the event generator
    if not event_generator.started:
        task: asyncio.Task = asyncio.create_task(event_generator.start(latest_events))

    return templates.TemplateResponse("home_polling.html", {"request": request})


@app.get("/poll-html/{name}", response_class=HTMLResponse)
async def poll_events_html(
    request: Request, name: str, last_event_id: Optional[int] = Query(default=0)
) -> str:
    """
    HTMX-compatible long polling endpoint that returns HTML with embedded polling attributes.
    Uses the same long polling logic but returns HTML that continues the polling loop.
    """
    user_events = latest_events[name]

    # Check if we have new events immediately
    if len(user_events) > last_event_id:
        return templates.TemplateResponse(
            "poll_events_fragment.html",
            {
                "request": request,
                "name": name,
                "events": user_events,
                "last_event_id": len(user_events),
            },
        ).body.decode()

    # No new events, create an event notifier and wait
    event_notifier = asyncio.Event()
    user_event_notifiers[name].add(event_notifier)

    try:
        # Wait for new events or timeout (60 seconds)
        try:
            await asyncio.wait_for(event_notifier.wait(), timeout=60.0)
        except asyncio.TimeoutError:
            # Timeout reached, return current content and continue polling
            return templates.TemplateResponse(
                "poll_events_fragment.html",
                {
                    "request": request,
                    "name": name,
                    "events": user_events if user_events else None,
                    "last_event_id": last_event_id,
                },
            ).body.decode()

        # Event was triggered, return updated content
        user_events = latest_events[name]
        return templates.TemplateResponse(
            "poll_events_fragment.html",
            {
                "request": request,
                "name": name,
                "events": user_events,
                "last_event_id": len(user_events),
            },
        ).body.decode()

    finally:
        # Clean up: remove the event notifier from the set
        user_event_notifiers[name].discard(event_notifier)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)  # Different port to avoid conflicts

