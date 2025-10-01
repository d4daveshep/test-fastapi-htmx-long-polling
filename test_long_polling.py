import asyncio
from collections import defaultdict
import random
from typing import Any

from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Test Long Polling Events")

templates = Jinja2Templates(directory="templates")

# Store latest events for each user so we can track when updates are needed
latest_events: defaultdict[str, list[str]] = defaultdict(list)

# Event notification system for proper long polling. We use a dict with key=name and value=set of Events.
# Events are discarded after there is new activity or the timeout is reached.
# Each client browser window or tab get's it's own event notifier for each name
user_event_notifiers: dict[str, set[asyncio.Event]] = defaultdict(set)


class EventGenerator:
    """
    Class to generate events at random intervals and add them to the event storage
    """

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
        _: asyncio.Task = asyncio.create_task(event_generator.start(latest_events))

    return templates.TemplateResponse(
        request=request, name="home_polling.html", context={}
    )


@app.get("/poll-html/{name}", response_class=HTMLResponse)
async def poll_events_html(
    request: Request, name: str, last_event_id: int = Query(default=0)
) -> HTMLResponse:
    """
    HTMX-compatible long polling endpoint that returns HTML with embedded polling attributes for the specified user.
    Uses the same long polling logic but returns HTML that continues the polling loop.
    """
    user_events = latest_events[name]

    template_context: dict[str, Any] = {
        "request": request,
        "name": name,
        "events": user_events,
        "last_event_id": last_event_id,
    }

    # If we have new events then respond (i.e. return) immediately
    if len(user_events) > last_event_id:
        template_context["last_event_id"] = len(user_events)
        return templates.TemplateResponse(
            name="poll_events_fragment.html", context=template_context
        )

    # No new events, create an event notifier and wait
    event_notifier: asyncio.Event = asyncio.Event()
    user_event_notifiers[name].add(event_notifier)

    try:
        # Wait for new events or timeout (60 seconds)
        try:
            await asyncio.wait_for(event_notifier.wait(), timeout=60.0)
        except asyncio.TimeoutError:
            # Timeout reached, return current content and continue polling
            template_context["last_event_id"] = last_event_id
            return templates.TemplateResponse(
                name="poll_events_fragment.html", context=template_context
            )

        # Event was triggered, return updated content
        user_events = latest_events[name]
        template_context["last_event_id"] = len(user_events)
        return templates.TemplateResponse(
            name="poll_events_fragment.html", context=template_context
        )

    finally:
        # Clean up: remove the event notifier from the set
        user_event_notifiers[name].discard(event_notifier)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
