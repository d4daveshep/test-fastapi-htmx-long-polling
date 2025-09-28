# README

This is a complete example showing realtime webpage updates using long-polling with FastAPI, Jinja2, and HTMX.
This example will simulate a real-time notification system.
Here's how it works:

## Key Components

**1. Long-Polling Endpoint (`/poll`)**

- Waits up to 30 seconds for new notifications
- Returns immediately when new data is available
- Uses asyncio for non-blocking waiting

**2. HTMX Integration**

- `hx-get="/poll"` initiates the long-polling request
- `hx-trigger="load"` starts polling immediately
- `hx-swap="beforeend"` appends new notifications
- No JavaScript required - pure declarative HTMX

**3. Real-time Features**

- Automatic background notification generation
- Manual notification creation via button
- Live status updates every 5 seconds
- Smooth animations for new notifications

## Long-Polling Flow

1. Client sends request to `/poll` with last check timestamp
2. Server waits (up to 30 seconds) for new notifications
3. When new data arrives, server responds immediately with HTML
4. HTMX receives the response and updates the DOM
5. A new polling request is automatically triggered
6. Process repeats for continuous real-time updates

This approach is more efficient than regular polling since the server only responds when there's actually new data, reducing unnecessary network traffic while maintaining real-time responsiveness.
