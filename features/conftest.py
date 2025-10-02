# ============================================================================
# features/conftest.py - Playwright Test Configuration
# ============================================================================
import pytest
import threading
import time
import uvicorn
from typing import Generator


@pytest.fixture(scope="session")
def live_server() -> Generator[str, None, None]:
    """Start a live server for Playwright tests"""
    from main_test_suite import app

    # Use a different port for testing
    port = 8765
    server_url = f"http://localhost:{port}"

    # Run server in a thread
    def run_server():
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="error")

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Wait for server to be ready
    time.sleep(1)

    yield server_url

    # Server will be stopped when thread exits (daemon thread)
