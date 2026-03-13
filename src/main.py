"""
Main entry point for mcp-reddit-mod MCP server.

This module loads configuration and starts the FastMCP server with
streamable-http transport for Docker deployment.
"""

from src.config import SERVER_HOST, SERVER_PORT, load_config, validate_reddit_credentials
from src.server import mcp


def main():
    """
    Load configuration and start the MCP server.

    This function:
    1. Loads environment configuration
    2. Validates Reddit credentials (logs warning if missing)
    3. Starts the MCP server with streamable-http transport

    The server binds to 0.0.0.0:8000 for Docker container accessibility.
    """
    # Load environment configuration
    config = load_config()

    # Validate Reddit credentials
    # Note: Phase 1 doesn't use Reddit, so we only warn if credentials are missing
    missing = validate_reddit_credentials()
    if missing:
        print(f"Warning: Missing Reddit credentials: {', '.join(missing)}")
        print("These are required for Phase 3 but optional for Phase 1.")
        print()

    # Set environment variables for FastMCP to pick up
    import os
    os.environ["MCP_HOST"] = SERVER_HOST
    os.environ["MCP_PORT"] = str(SERVER_PORT)

    # Print server startup information
    print(f"Starting {config['name']} v{config['version']}")
    print(f"Description: {config['description']}")
    print(f"Binding to {SERVER_HOST}:{SERVER_PORT}")
    print("Transport: streamable-http")
    print()

    # Start the MCP server with streamable-http transport
    # FastMCP reads MCP_HOST and MCP_PORT from environment variables
    mcp.run(
        transport="streamable-http"
    )


if __name__ == "__main__":
    main()
