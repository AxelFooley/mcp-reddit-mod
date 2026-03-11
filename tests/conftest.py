"""
Pytest configuration and shared fixtures for MCP server testing.

This module provides common fixtures and configuration for testing
the italia-career-mod MCP server implementation.
"""

import pytest
import asyncio
from typing import AsyncGenerator

# Enable anyio for async test support
pytest_plugins = ["anyio"]


@pytest.fixture
def event_loop():
    """
    Create an event loop for async tests.

    This fixture ensures that each test gets its own event loop,
    preventing state leakage between tests.
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mcp_server_instance():
    """
    Fixture providing the MCP server instance for testing.

    This fixture will be implemented in Wave 1 (01-01-PLAN.md)
    once the FastMCP server is created.

    Yields:
        The FastMCP server instance configured for testing
    """
    # Wave 0 stub - implementation in 01-01
    pytest.skip("Wave 0 stub - server implementation in 01-01-PLAN.md")


@pytest.fixture
async def mcp_client():
    """
    Fixture providing an async MCP client for testing.

    This fixture will be implemented in Wave 1 (01-01-PLAN.md)
    once the FastMCP server transport is configured.

    Yields:
        An async client capable of making MCP protocol requests
    """
    # Wave 0 stub - implementation in 01-01
    pytest.skip("Wave 0 stub - client implementation in 01-01-PLAN.md")


@pytest.fixture
def sample_reddit_config():
    """
    Fixture providing sample Reddit configuration for testing.

    Returns:
        dict: Sample Reddit API credentials and configuration
    """
    return {
        "client_id": "test_client_id",
        "client_secret": "test_client_secret",
        "username": "test_user",
        "password": "test_password",
        "user_agent": "italia-career-mod/0.1.0 by test_user"
    }


# Test configuration markers
def pytest_configure(config):
    """
    Configure pytest with custom markers.

    This function sets up custom markers that can be used
    to categorize tests (e.g., slow, integration, etc.).
    """
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
