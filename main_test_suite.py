# ============================================================================
# main.py - Your FastAPI Application
# ============================================================================
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import asyncio
from datetime import datetime


# Event system for long-polling
class EventBus:
    def __init__(self):
        self.subscribers = []

    async def subscribe(self):
        queue = asyncio.Queue()
        self.subscribers.append(queue)
        return queue

    async def publish(self, event):
        for queue in self.subscribers:
            await queue.put(event)

    def unsubscribe(self, queue):
        if queue in self.subscribers:
            self.subscribers.remove(queue)


event_bus = EventBus()
items_list = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown
    event_bus.subscribers.clear()


app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index_test_suite.html",
        context={"title": "Welcome to Live Updates"},
    )


@app.get("/items", response_class=HTMLResponse)
async def get_items(request: Request):
    is_htmx = request.headers.get("HX-Request") == "true"

    if is_htmx:
        return templates.TemplateResponse(
            request=request,
            name="partials/items.html",
            context={"items": items_list},
        )

    return templates.TemplateResponse(
        request=request,
        name="items.html",
        context={"items": items_list},
    )


@app.post("/items", response_class=HTMLResponse)
async def create_item(request: Request):
    form = await request.form()
    item_name = form.get("name")

    # Add item to the list
    items_list.append(item_name)

    # Publish event to subscribers
    await event_bus.publish(
        {
            "type": "item_created",
            "data": item_name,
            "timestamp": datetime.now().isoformat(),
        }
    )

    # Return empty response - let long-polling handle UI update
    # This prevents duplicate items in the UI
    return ""


@app.get("/updates/poll", response_class=HTMLResponse)
async def poll_updates(request: Request, timeout: float = 30.0):
    """Long-polling endpoint for live updates - returns HTML for HTMX"""
    queue = await event_bus.subscribe()

    try:
        event = await asyncio.wait_for(queue.get(), timeout=timeout)
        # Return HTML fragment with the new item AND a new polling div
        # This ensures continuous polling
        return templates.TemplateResponse(
            request=request,
            name="partials/poll_response.html",
            context={"item": event["data"]},
        )
    except asyncio.TimeoutError:
        # Return new polling div to continue polling
        return templates.TemplateResponse(
            request=request,
            name="partials/poll_response.html",
            context={"item": None},
        )
    finally:
        event_bus.unsubscribe(queue)


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
