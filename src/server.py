"""
FastMCP server instance for italia-career-mod.

This module creates and configures the MCP server using the FastMCP framework.
It provides tool registration and server metadata for AI agent interactions.
"""

from mcp.server.fastmcp import FastMCP
from src.config import SERVER_NAME, SERVER_VERSION, SERVER_DESCRIPTION

# =============================================================================
# MCP Server Instance
# =============================================================================

# Create FastMCP server instance
# Note: FastMCP uses 'instructions' for description (shown to LLM clients)
# Version is typically set via package metadata or initialization options
mcp = FastMCP(
    name=SERVER_NAME,
    instructions=SERVER_DESCRIPTION,
)


# =============================================================================
# Tool Registration
# =============================================================================

@mcp.tool()
def status() -> str:
    """
    Get server status.

    This is a placeholder tool for Phase 1 to verify tool discovery.
    Phase 3 will implement Reddit moderation tools.

    Returns:
        str: Server status message.
    """
    return "Server operational. Reddit tools coming in Phase 3."


# =============================================================================
# Server Export
# =============================================================================

# The mcp instance is exported for use in main.py
# Do NOT call mcp.run() in this file - that happens in main.py
