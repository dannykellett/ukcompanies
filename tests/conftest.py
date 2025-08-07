"""Pytest fixtures and configuration for ukcompanies tests."""

import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[None, None]:
    """Placeholder fixture for async HTTP client."""
    # This will be implemented in future stories when we create the client
    yield None
