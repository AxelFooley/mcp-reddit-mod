"""
Reddit client module for mcp-reddit-mod MCP server.

This module provides a lazy-initialization singleton PRAW Reddit client
that authenticates using script app credentials from environment variables.
It implements safe error handling that sanitizes error messages to prevent
credential leakage.

Key features:
- Lazy initialization singleton pattern (PRAW instances are thread-safe)
- Script app authentication (username/password, not OAuth flow)
- Credential validation before client creation
- Error message sanitization to prevent credential leakage
"""

import re

import praw

from src.config import (
    REDDIT_CLIENT_ID,
    REDDIT_CLIENT_SECRET,
    REDDIT_PASSWORD,
    REDDIT_REQUEST_TIMEOUT,
    REDDIT_USER_AGENT,
    REDDIT_USERNAME,
)

# Module-level singleton instance
_reddit_instance = None


def sanitize_error_message(error_message: str) -> str:
    """
    Remove potential credential values from error messages.

    PRAW may include credential values in error messages in some cases.
    This function sanitizes error messages by removing patterns that
    look like the credentials we have configured.

    Args:
        error_message: Original error message from PRAW.

    Returns:
        str: Sanitized error message safe for logging/display.
    """
    sanitized = error_message

    # Remove each credential value if present in the error message
    for cred_value in [REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD]:
        if cred_value and cred_value in sanitized:
            sanitized = sanitized.replace(cred_value, "***REDACTED***")

    # Also redact common Reddit API credential patterns
    # Reddit client_id pattern: 14-20 character alphanumeric string
    sanitized = re.sub(r'\b[a-zA-Z0-9]{14,20}\b', "***CLIENT_ID***", sanitized)

    return sanitized


def get_reddit_client() -> praw.Reddit:
    """
    Get or create the PRAW Reddit client instance.

    Uses lazy initialization singleton pattern to ensure only one
    PRAW instance exists per application runtime. PRAW instances
    are thread-safe and handle connection pooling internally.

    The client authenticates using script app credentials from environment
    variables (REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD).

    Returns:
        praw.Reddit: Authenticated PRAW Reddit client instance.

    Raises:
        ValueError: If required Reddit credentials are missing from environment.
        praw.exceptions.PRAWException: If authentication fails.
    """
    global _reddit_instance

    if _reddit_instance is None:
        # Validate credentials before creating client
        missing = []
        if not REDDIT_CLIENT_ID:
            missing.append("REDDIT_CLIENT_ID")
        if not REDDIT_CLIENT_SECRET:
            missing.append("REDDIT_CLIENT_SECRET")
        if not REDDIT_USERNAME:
            missing.append("REDDIT_USERNAME")
        if not REDDIT_PASSWORD:
            missing.append("REDDIT_PASSWORD")

        if missing:
            raise ValueError(
                f"Missing required Reddit credentials: {', '.join(missing)}. "
                "Please set these environment variables or add them to your .env file."
            )

        # Create PRAW instance with script app authentication
        # Script app auth is triggered by providing username/password
        _reddit_instance = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            username=REDDIT_USERNAME,
            password=REDDIT_PASSWORD,
            user_agent=REDDIT_USER_AGENT,
            # Disable read_only mode - we need mod access
            read_only=False,
            # Set HTTP request timeout (REDI-04)
            request_timeout=REDDIT_REQUEST_TIMEOUT,
        )

        # Verify authentication worked (makes a lightweight API call)
        # This raises praw.exceptions.PRAWException if auth fails
        try:
            _reddit_instance.user.me()
        except Exception as e:
            # Sanitize error to avoid leaking credentials
            sanitized_msg = sanitize_error_message(str(e))
            raise type(e)(
                f"Reddit authentication failed: {sanitized_msg}. "
                "Please verify your credentials in .env file."
            ) from e

    return _reddit_instance
