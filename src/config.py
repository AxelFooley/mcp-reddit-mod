"""
Configuration module for mcp-reddit-mod MCP server.

This module handles environment variable loading and server configuration.
It provides validation for required Reddit credentials and server settings.
"""

import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# =============================================================================
# Server Configuration
# =============================================================================

SERVER_NAME = os.getenv("SERVER_NAME", "mcp-reddit-mod")
SERVER_VERSION = os.getenv("SERVER_VERSION", "0.1.0")
SERVER_DESCRIPTION = os.getenv(
    "SERVER_DESCRIPTION",
    "AI-assisted Reddit moderation for r/reddit"
)

# Server binding configuration
# 0.0.0.0 allows Docker container external access
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))

# =============================================================================
# Reddit API Credentials
# =============================================================================

# Required for Phase 3 (Reddit integration)
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD")
REDDIT_USER_AGENT = os.getenv(
    "REDDIT_USER_AGENT",
    f"mcp-reddit-mod/{SERVER_VERSION} by {REDDIT_USERNAME or 'unknown'}"
)

# Reddit API request timeout (REDI-04)
# Default 30 seconds, configurable via REDDIT_REQUEST_TIMEOUT environment variable
# Must be positive integer between 1 and 600 seconds (10 minutes max)
_REDDIT_REQUEST_TIMEOUT_RAW = os.getenv("REDDIT_REQUEST_TIMEOUT", "30")

try:
    REDDIT_REQUEST_TIMEOUT = int(_REDDIT_REQUEST_TIMEOUT_RAW)
    if REDDIT_REQUEST_TIMEOUT <= 0:
        raise ValueError(f"REDDIT_REQUEST_TIMEOUT must be positive (got {REDDIT_REQUEST_TIMEOUT})")
    if REDDIT_REQUEST_TIMEOUT > 600:
        raise ValueError(f"REDDIT_REQUEST_TIMEOUT max is 600s (got {REDDIT_REQUEST_TIMEOUT})")
except ValueError as e:
    raise ValueError(
        f"Invalid REDDIT_REQUEST_TIMEOUT value: '{_REDDIT_REQUEST_TIMEOUT_RAW}'. "
        f"Must be an integer between 1 and 600 seconds. {e}"
    )

# =============================================================================
# Validation Functions
# =============================================================================


def validate_reddit_credentials() -> list[str]:
    """
    Validate that all required Reddit credentials are present.

    Returns:
        list[str]: List of missing environment variable names.
                   Empty list if all credentials are present.

    Example:
        >>> missing = validate_reddit_credentials()
        >>> if missing:
        ...     print(f"Missing credentials: {', '.join(missing)}")
    """
    required_vars = [
        "REDDIT_CLIENT_ID",
        "REDDIT_CLIENT_SECRET",
        "REDDIT_USERNAME",
        "REDDIT_PASSWORD",
    ]
    return [var for var in required_vars if not os.getenv(var)]


def get_server_config() -> dict:
    """
    Get the current server configuration.

    Returns:
        dict: Dictionary containing server configuration values.
    """
    return {
        "name": SERVER_NAME,
        "version": SERVER_VERSION,
        "description": SERVER_DESCRIPTION,
        "host": SERVER_HOST,
        "port": SERVER_PORT,
    }


def load_config() -> dict:
    """
    Load and validate configuration.

    This is the main entry point for configuration loading.
    It returns the server config and logs any missing Reddit credentials.

    Returns:
        dict: Server configuration dictionary.
    """
    config = get_server_config()

    # Check for missing Reddit credentials
    # Log warning but don't fail - Phase 1 doesn't use Reddit
    missing = validate_reddit_credentials()
    if missing:
        import warnings
        warnings.warn(
            f"Missing Reddit credentials: {', '.join(missing)}. "
            "These are required for Phase 3 but optional for Phase 1."
        )

    return config
