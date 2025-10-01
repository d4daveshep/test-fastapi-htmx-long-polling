# FastAPI + HTMX + Long-Polling Test Example

This project demonstrates testing a FastAPI application with Jinja2 templates, HTMX, and long-polling using pytest-bdd.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

Start the development server:
```bash
uvicorn main:app --reload
```

Visit http://localhost:8000 in your browser.

## Running Tests

Run all tests:
```bash
pytest
```

Run specific test types:
```bash
# BDD scenarios only
pytest features/

# Integration tests only
pytest tests/

# Verbose output
pytest -v

# Show print statements
pytest -s
```

## Project Structure

```
.
├── main.py                   # FastAPI application with long-polling
├── conftest.py              # Pytest fixtures and configuration
├── pytest.ini               # Pytest settings
├── requirements.txt         # Python dependencies
├── features/                # BDD feature files
│   ├── homepage.feature
│   ├── htmx_interactions.feature
│   ├── live_updates.feature
│   └── steps/              # Step definitions
│       ├── __init__.py
│       ├── page_steps.py
│       ├── htmx_steps.py
│       └── live_update_steps.py
├── tests/                   # Integration tests
│   ├── __init__.py
│   └── test_integration.py
└── templates/               # Jinja2 HTML templates
    ├── index.html
    ├── items.html
    └── partials/
        ├── items.html
        └── item.html
```

## Key Features

- **Pure HTMX** - No custom JavaScript needed for interactivity
- **Long-polling** - Server-sent updates via HTMX
- **BDD Testing** - Behavior-driven tests with pytest-bdd
- **Async Testing** - httpx.AsyncClient for async endpoints
- **Event Bus** - Pub/sub pattern for broadcasting live updates

## How It Works

1. HTMX loads items on page load via `hx-get="/items"`
2. Users can add items via the form using `hx-post="/items"`
3. Long-polling endpoint (`/updates/poll`) waits for events
4. When items are created, all connected clients receive HTML fragments
5. HTMX automatically reconnects after receiving updates

## Testing Strategy

The test suite uses two approaches:

1. **Synchronous TestClient** - For simple, fast tests (page rendering, HTMX headers)
2. **Async httpx.AsyncClient** - For testing async behavior (long-polling, concurrent connections)

BDD scenarios cover:
- Homepage rendering
- HTMX interactions (loading fragments, form submissions)
- Long-polling (receiving updates, timeouts)

Integration tests verify:
- Multiple clients receiving broadcast updates
- End-to-end flow from HTMX post to polling update
- Health check endpoint

## Learn More

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [HTMX Documentation](https://htmx.org/)
- [pytest-bdd Documentation](https://pytest-bdd.readthedocs.io/)
