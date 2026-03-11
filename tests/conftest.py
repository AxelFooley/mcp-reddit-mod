"""Pytest configuration and shared fixtures for MCP server testing."""

import pytest

# Enable anyio plugin for async test support
pytest_plugins = ["anyio"]


@pytest.fixture
def server_config():
    """Provide test server configuration.

    This fixture returns configuration parameters for the MCP server.
    Will be used in Wave 1 when server implementation exists.

    Returns:
        dict: Server configuration with host, port, and transport settings.
    """
    return {
        "host": "0.0.0.0",
        "port": 8000,
        "transport": "streamable-http",
    }


@pytest.fixture
async def mcp_client():
    """Provide async MCP client for testing.

    This fixture will create an async HTTP client for MCP protocol testing.
    Will be implemented in Wave 1 when server is available.

    Yields:
        Async client instance for making MCP requests.
    """
    # Placeholder for Wave 1 implementation
    # Will return an httpx.AsyncClient configured for MCP protocol
    pytest.skip("Wave 0 stub - async client fixture implemented in 01-01")
    yield  # pragma: no cover


@pytest.fixture
def sample_tool_response():
    """Provide sample tool response structure for testing.

    Returns the expected structure of MCP tool responses
    according to the MCP specification.
    """
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "content": [
                {
                    "type": "text",
                    "text": "Sample response"
                }
            ]
        }
    }
}


@pytest.fixture
def sample_error_response():
    """Provide sample error response structure for testing.

    Returns the expected structure of MCP error responses
    according to the MCP JSON-RPC specification.
    """
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "error": {
            "code": -32600,
            "message": "Invalid Request",
            "data": None
        }
    }
}
