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


@pytest.fixture
def mock_reddit_credentials(monkeypatch):
    """
    Mock Reddit credentials for testing (REDI-01, REDI-02).

    This fixture sets up test environment variables for Reddit API
    credentials, allowing tests to run without exposing real credentials.

    Args:
        monkeypatch: Pytest monkeypatch fixture for environment modification

    Returns:
        dict: Dictionary of mock environment variables
    """
    mock_env = {
        "REDDIT_CLIENT_ID": "test_client_id",
        "REDDIT_CLIENT_SECRET": "test_secret",
        "REDDIT_USERNAME": "test_user",
        "REDDIT_PASSWORD": "test_password",
        "REDDIT_USER_AGENT": "test_agent",
    }
    for key, value in mock_env.items():
        monkeypatch.setenv(key, value)
    return mock_env


@pytest.fixture
def praw_mock(monkeypatch):
    """
    Mock PRAW Reddit class for testing.

    This fixture patches the praw.Reddit class to return a mock instance,
    allowing tests to verify Reddit client behavior without making actual API calls.

    Args:
        monkeypatch: Pytest monkeypatch fixture for patching

    Yields:
        Mock: Mocked PRAW Reddit instance
    """
    from unittest.mock import Mock
    mock_instance = Mock()
    mock_instance.user.me.return_value = Mock(name="test_user")
    with monkeypatch.context() as m:
        m.setattr("praw.Reddit", Mock(return_value=mock_instance))
        yield mock_instance


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
