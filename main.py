from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import asyncio
import time
import random
from datetime import datetime
from typing import List

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# In-memory storage for notifications (in production, use a database)
notifications: List[dict] = []
notification_counter = 0

# Store the last time each client checked for updates
client_last_check = {}


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Main page with HTMX long-polling setup"""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "notifications": notifications[-10:],  # Show last 10 notifications
        },
    )


@app.get("/poll")
async def long_poll(request: Request, last_check: float = 0):
    """Long-polling endpoint that waits for new notifications"""
    client_id = request.client.host
    timeout = 30  # 30 seconds timeout
    check_interval = 1  # Check every second
    start_time = time.time()

    while (time.time() - start_time) < timeout:
        # Check if there are new notifications since last_check
        new_notifications = [
            notif for notif in notifications if notif["timestamp"] > last_check
        ]

        if new_notifications:
            # Return the notifications as HTML
            return templates.TemplateResponse(
                "notifications.html",
                {
                    "request": request,
                    "notifications": new_notifications,
                    "last_check": time.time(),
                },
            )

        # Wait before checking again
        await asyncio.sleep(check_interval)

    # Timeout reached, return empty response with updated timestamp
    return templates.TemplateResponse(
        "notifications.html",
        {"request": request, "notifications": [], "last_check": time.time()},
    )


@app.post("/add-notification")
async def add_notification(request: Request):
    """Add a new notification (simulates external events)"""
    global notification_counter
    notification_counter += 1

    # Simulate different types of notifications
    notification_types = [
        ("info", "New user registered"),
        ("success", "Payment processed successfully"),
        ("warning", "System maintenance scheduled"),
        ("error", "Failed login attempt detected"),
        ("info", "New comment on your post"),
    ]

    notif_type, message = random.choice(notification_types)

    notification = {
        "id": notification_counter,
        "type": notif_type,
        "message": f"{message} #{notification_counter}",
        "timestamp": time.time(),
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    notifications.append(notification)

    # Keep only the last 50 notifications
    if len(notifications) > 50:
        notifications.pop(0)

    return {"status": "success", "notification": notification}


@app.get("/status")
async def get_status(request: Request):
    """Get current system status"""
    return templates.TemplateResponse(
        "status.html",
        {
            "request": request,
            "total_notifications": len(notifications),
            "last_notification": notifications[-1] if notifications else None,
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
    )


# Background task to simulate periodic notifications
@app.on_event("startup")
async def startup_event():
    """Start background task to generate sample notifications"""
    asyncio.create_task(generate_sample_notifications())


async def generate_sample_notifications():
    """Generate notifications every 10-30 seconds for demo purposes"""
    while True:
        await asyncio.sleep(random.randint(10, 30))
        global notification_counter
        notification_counter += 1

        messages = [
            "System backup completed",
            "New order received",
            "User session expired",
            "Database optimization finished",
            "Security scan completed",
        ]

        notification = {
            "id": notification_counter,
            "type": random.choice(["info", "success", "warning"]),
            "message": random.choice(messages),
            "timestamp": time.time(),
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        notifications.append(notification)

        if len(notifications) > 50:
            notifications.pop(0)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
