"""
Main entry point for italia-career-mod MCP server.

This module loads configuration and starts the FastMCP server with
streamable-http transport for Docker deployment.
"""

import sys
from src.config import load_config, validate_reddit_credentials, SERVER_HOST, SERVER_PORT
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
    
    # Print server startup information
    print(f"Starting {config['name']} v{config['version']}")
    print(f"Description: {config['description']}")
    print(f"Binding to {config['host']}:{config['port']}")
    print(f"Transport: streamable-http")
    print()
    
    # Start the MCP server with streamable-http transport
    # host="0.0.0.0" allows Docker container external access (MCPF-02)
    # port=8000 is the standard MCP HTTP endpoint port
    # transport="streamable-http" provides bidirectional JSON-RPC over HTTP (MCPF-01)
    mcp.run(
        transport="streamable-http",
        host=SERVER_HOST,
        port=SERVER_PORT
    )


if __name__ == "__main__":
    main()
