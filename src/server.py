"""
FastMCP server instance for italia-career-mod.

This module creates and configures the MCP server using the FastMCP framework.
It provides tool registration and server metadata for AI agent interactions.
"""

import json

from mcp.server.fastmcp import FastMCP

from src.config import SERVER_DESCRIPTION, SERVER_NAME

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
    Get server status and available tools.

    Returns:
        str: Server status message indicating moderation tools are available.
    """
    return (
        "Server operational. Moderation tools available: "
        "get_modqueue, approve_item, remove_item, ban_user, get_user_history."
    )


@mcp.tool()
def get_modqueue_tool(subreddit: str, limit: int = 25) -> str:
    """
    Fetch modqueue items from a subreddit for moderator review.

    The modqueue contains items reported by users or caught by the spam filter.
    This tool returns items awaiting moderator action with metadata for review.

    Args:
        subreddit: Name of the subreddit (without r/ prefix), e.g., "test"
        limit: Maximum number of items to retrieve (default: 25, max: 100)

    Returns:
        str: JSON string containing list of modqueue items with keys:
            - thing_id: Reddit fullname (t1_* for comments, t3_* for submissions)
            - type: "comment" or "submission"
            - author: Username or "[deleted]"
            - body: Comment body or submission title/text
            - created_utc: Unix timestamp
            - subreddit: Subreddit name

    Examples:
        >>> get_modqueue_tool("testsub", limit=10)
    """
    from src.modtools import get_modqueue

    try:
        items = get_modqueue(subreddit, limit=min(limit, 100))
        return json.dumps(items, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def approve_item_tool(thing_id: str) -> str:
    """
    Approve a comment or submission, removing it from the modqueue.

    Approved items become visible to other users. This action is idempotent.

    Args:
        thing_id: Reddit fullname (e.g., "t1_abc123" for comment, "t3_def456" for submission)

    Returns:
        str: Success message or error details.

    Examples:
        >>> approve_item_tool("t1_abc123")
        >>> approve_item_tool("t3_def456")
    """
    from src.modtools import approve_item

    try:
        approve_item(thing_id)
        return json.dumps({"success": True, "message": f"Approved {thing_id}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def remove_item_tool(thing_id: str, reason: str = "", spam: bool = False) -> str:
    """
    Remove a comment or submission from public view.

    Removed items are hidden from all users except moderators.

    Args:
        thing_id: Reddit fullname (e.g., "t1_abc123" for comment, "t3_def456" for submission)
        reason: Moderation reason for the removal (for mod notes)
        spam: Whether to mark as spam (triggers Reddit's spam filtering)

    Returns:
        str: Success message or error details.

    Examples:
        >>> remove_item_tool("t1_abc123", reason="Spam")
        >>> remove_item_tool("t3_def456", spam=True)
    """
    from src.modtools import remove_item

    try:
        remove_item(thing_id, reason=reason, spam=spam)
        spam_note = " as spam" if spam else ""
        return json.dumps({
            "success": True,
            "message": f"Removed {thing_id}{spam_note}"
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def ban_user_tool(subreddit: str, username: str, reason: str, duration_days: int = 0) -> str:
    """
    Ban a user from a subreddit.

    Bans prevent users from posting and commenting. Permanent bans (duration_days=0)
    last until manually revoked. Temporary bans automatically expire.

    Args:
        subreddit: Name of the subreddit (without r/ prefix)
        username: Username to ban (without u/ prefix)
        reason: Ban reason for mod notes
        duration_days: Ban duration in days (0=permanent, >0=temporary)

    Returns:
        str: Success message or error details.

    Examples:
        >>> ban_user_tool("testsub", "spam_user", "Spamming")
        >>> ban_user_tool("testsub", "troll", "Harassment", duration_days=7)
    """
    from src.modtools import ban_user

    try:
        ban_user(subreddit, username, reason, duration_days)
        if duration_days == 0:
            duration_desc = "permanently"
        else:
            duration_desc = f"for {duration_days} days"
        return json.dumps({
            "success": True,
            "message": f"Banned u/{username} from r/{subreddit} {duration_desc}"
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_user_history_tool(username: str, subreddit: str, limit: int = 100) -> str:
    """
    Fetch user's post and comment history in a subreddit.

    Useful for detecting repeat offenders by reviewing their previous
    posts and comments that were flagged or removed.

    Args:
        username: Reddit username (without u/ prefix)
        subreddit: Subreddit name (without r/ prefix)
        limit: Maximum number of items to fetch (default: 100)

    Returns:
        str: JSON string of user's history items with removed flag.

    Examples:
        >>> get_user_history_tool("spam_user", "testsub")
        >>> get_user_history_tool("troll", "testsub", limit=50)
    """
    from src.modtools import get_user_history, sanitize_moderation_error

    try:
        history = get_user_history(username, subreddit, limit)
        return json.dumps(history, indent=2)
    except Exception as e:
        return f"Error fetching user history: {sanitize_moderation_error(e)}"


# =============================================================================
# Server Export
# =============================================================================

# The mcp instance is exported for use in main.py
# Do NOT call mcp.run() in this file - that happens in main.py
