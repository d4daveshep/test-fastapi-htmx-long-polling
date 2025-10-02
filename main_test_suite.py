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
    items = ["Item 1", "Item 2", "Item 3"]
    is_htmx = request.headers.get("HX-Request") == "true"

    if is_htmx:
        return templates.TemplateResponse(
            request=request,
            name="partials/items.html",
            context={"items": items},
        )

    return templates.TemplateResponse(
        request=request,
        name="items.html",
        context={"items": items},
    )


@app.post("/items", response_class=HTMLResponse)
async def create_item(request: Request):
    form = await request.form()
    item_name = form.get("name")

    # Publish event to subscribers
    await event_bus.publish(
        {
            "type": "item_created",
            "data": item_name,
            "timestamp": datetime.now().isoformat(),
        }
    )

    return templates.TemplateResponse(
        request=request,
        name="partials/item.html",
        context={"item": item_name},
    )


@app.get("/updates/poll", response_class=HTMLResponse)
async def poll_updates(request: Request, timeout: float = 30.0):
    """Long-polling endpoint for live updates - returns HTML for HTMX"""
    queue = await event_bus.subscribe()

    try:
        event = await asyncio.wait_for(queue.get(), timeout=timeout)
        # Return HTML fragment with the new item
        return templates.TemplateResponse(
            request=request,
            name="partials/item.html",
            context={"item": event["data"]},
        )
    except asyncio.TimeoutError:
        # Return empty response and reconnect
        return ""
    finally:
        event_bus.unsubscribe(queue)


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
