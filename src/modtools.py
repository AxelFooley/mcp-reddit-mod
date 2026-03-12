"""
Moderation tools module for italia-career-mod MCP server.

This module provides core Reddit moderation functionality through PRAW,
including modqueue retrieval, content approval/removal, user banning,
and validation/error sanitization utilities.

Key features:
- Thing ID validation before API calls (SAFE-01)
- Extended error sanitization for moderation operations (SAFE-02)
- Modqueue retrieval for content review (MODT-01)
- Content approval and removal (MODT-02, MODT-03)
- User banning with configurable duration (MODT-04)
"""

import re
from typing import Optional

from praw.exceptions import PRAWException

from src.reddit_client import get_reddit_client, sanitize_error_message

# =============================================================================
# Thing ID Validation (SAFE-01)
# =============================================================================

# Reddit thing_id pattern: t[1-5]_[base36_string]
# t1_ = comment, t2_ = account, t3_ = submission, t4_ = message, t5_ = subreddit
# For moderation tools, we primarily support t1_ (comment) and t3_ (submission)
THING_ID_PATTERN = re.compile(r'^t[1-5]_[a-zA-Z0-9_-]+$')

# Supported thing types for moderation operations
SUPPORTED_THING_TYPES = {'1', '3'}  # comment, submission


def validate_thing_id(thing_id: str, expected_prefix: Optional[str] = None) -> str:
    """
    Validate a Reddit thing_id format.

    Thing IDs are Reddit's internal identifiers for content items.
    They follow the format: t[TYPE]_[BASE36_ID] where TYPE is 1-5.

    Args:
        thing_id: The thing_id to validate (e.g., "t1_abc123", "t3_def456")
        expected_prefix: Optional expected type digit (e.g., "1" for comments only)

    Returns:
        str: The validated thing_id (unchanged if valid)

    Raises:
        ValueError: If thing_id format is invalid or prefix doesn't match

    Examples:
        >>> validate_thing_id("t1_abc123")
        't1_abc123'
        >>> validate_thing_id("t3_xyz789", expected_prefix="3")
        't3_xyz789'
    """
    if not thing_id:
        raise ValueError("thing_id cannot be empty")

    # Check basic format matches thing_id pattern
    if not THING_ID_PATTERN.match(thing_id):
        raise ValueError(
            f"Invalid thing_id format: '{thing_id}'. "
            f"Expected format: t[1-5]_[base36_id]"
        )

    # Extract the type digit (tX_ where X is the type)
    prefix = thing_id[1]

    # Check if this type is supported for moderation
    if prefix not in SUPPORTED_THING_TYPES:
        raise ValueError(
            f"Unsupported thing_id type: t{prefix}_. "
            f"Supported types: t1_ (comment), t3_ (submission)"
        )

    # If expected_prefix provided, verify it matches
    if expected_prefix is not None and prefix != expected_prefix:
        raise ValueError(
            f"Expected thing_id prefix '{expected_prefix}' but got '{prefix}'"
        )

    return thing_id


# =============================================================================
# Error Sanitization (SAFE-02)
# =============================================================================

def sanitize_moderation_error(error: Exception, context: Optional[dict] = None) -> str:
    """
    Sanitize error messages from moderation operations.

    This function extends the base sanitize_error_message() to remove
    moderation-specific sensitive information like subreddit names,
    usernames, and thing IDs.

    Args:
        error: The exception to sanitize
        context: Optional dict of context values to redact (keys become ***KEY***)

    Returns:
        str: Sanitized error message safe for logging/display

    Examples:
        >>> try:
        ...     # some moderation operation
        ... except Exception as e:
        ...     sanitized = sanitize_moderation_error(e)
    """
    # Start with the raw error message
    error_msg = str(error)

    # First, do moderation-specific sanitization BEFORE general sanitization
    # This prevents subreddit/user names from being caught by other patterns

    # Remove subreddit names (r/SomeSubreddit -> r/SUBREDDIT)
    sanitized = re.sub(r'r/[A-Za-z0-9_+-]+', 'r/SUBREDDIT', error_msg)

    # Remove usernames (u/someuser -> u/USERNAME)
    sanitized = re.sub(r'u/[A-Za-z0-9_+-]+', 'u/USERNAME', sanitized)

    # Remove thing IDs (t1_abc123, t3_def456 -> tX_THINGID)
    sanitized = re.sub(r't[1-5]_[a-zA-Z0-9_-]+', 'tX_THINGID', sanitized)

    # Then apply base sanitization from reddit_client (catches credential patterns)
    sanitized = sanitize_error_message(sanitized)

    # Redact context values if provided
    if context:
        for key, value in context.items():
            if value and isinstance(value, str) and value in sanitized:
                sanitized = sanitized.replace(value, f"***{key.upper()}***")

    return sanitized


# =============================================================================
# Modqueue Retrieval (MODT-01)
# =============================================================================

def get_modqueue(subreddit: str, limit: int = 25) -> list[dict]:
    """
    Fetch modqueue items from a subreddit.

    The modqueue contains items that have been reported or caught by the
    spam filter and require moderator review.

    Args:
        subreddit: Name of the subreddit (without r/ prefix)
        limit: Maximum number of items to retrieve (default: 25)

    Returns:
        list[dict]: List of modqueue items with keys:
            - thing_id: Reddit fullname (t1_* for comments, t3_* for submissions)
            - type: "comment" or "submission"
            - author: Username or "[deleted]" if user deleted
            - body: Comment body or submission title/text
            - created_utc: Unix timestamp of creation
            - subreddit: Subreddit display name

    Raises:
        PRAWException: If API call fails (with sanitized error message)

    Examples:
        >>> items = get_modqueue("testsub", limit=10)
        >>> for item in items:
        ...     print(f"{item['type']}: {item['thing_id']}")
    """
    reddit = get_reddit_client()

    try:
        subreddit_obj = reddit.subreddit(subreddit)
        modqueue_items = subreddit_obj.mod.modqueue(limit=limit)

        result = []
        for item in modqueue_items:
            # Determine if comment or submission
            # PRAW Comment objects have __class__.__name__ == "Comment"
            item_type = "comment" if item.__class__.__name__ == "Comment" else "submission"

            # Get author (handle deleted users)
            author = str(item.author) if item.author else "[deleted]"

            # Get body text (comments have body, submissions have selftext or title)
            if item_type == "comment":
                # Comments have a body attribute
                content = item.body if hasattr(item, 'body') else ""
            else:
                # Submissions may have selftext or title
                if hasattr(item, 'selftext') and item.selftext:
                    content = item.selftext
                elif hasattr(item, 'title'):
                    content = item.title
                else:
                    content = ""

            result.append({
                "thing_id": item.fullname,
                "type": item_type,
                "author": author,
                "body": content,
                "created_utc": item.created_utc,
                "subreddit": str(item.subreddit),
            })

        return result

    except PRAWException as e:
        # Sanitize error message before re-raising
        sanitized_msg = sanitize_moderation_error(e)
        raise type(e)(f"Failed to fetch modqueue for r/{subreddit}: {sanitized_msg}") from e
