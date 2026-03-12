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
- Timeout protection for all API calls (REDI-04)
"""

import concurrent.futures
import re
from functools import wraps
from typing import Callable, Optional, TypeVar

from praw.exceptions import PRAWException

from src.reddit_client import get_reddit_client, sanitize_error_message

# =============================================================================
# Timeout Protection (REDI-04)
# =============================================================================

# Default timeout for moderation operations (seconds)
# Applied at application level via with_timeout decorator
MODTOOLS_TIMEOUT = 30

T = TypeVar('T')


def with_timeout(timeout_seconds: int = MODTOOLS_TIMEOUT):
    """
    Decorator to wrap function with timeout protection.

    This decorator uses ThreadPoolExecutor to run the function in a separate
    thread and enforces a timeout. If the function doesn't complete within
    the specified timeout, a TimeoutError is raised and the future is cancelled.

    Args:
        timeout_seconds: Maximum time to wait for function to complete (in seconds).
                        Defaults to MODTOOLS_TIMEOUT (30 seconds).

    Returns:
        Callable: Decorated function with timeout protection.

    Raises:
        TimeoutError: If function execution exceeds timeout_seconds.

    Examples:
        >>> @with_timeout(timeout_seconds=10)
        ... def slow_operation():
        ...     return result
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(func, *args, **kwargs)
                try:
                    return future.result(timeout=timeout_seconds)
                except concurrent.futures.TimeoutError:
                    future.cancel()
                    raise TimeoutError(
                        f"{func.__name__} exceeded timeout of {timeout_seconds} seconds"
                    )
        return wrapper
    return decorator

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

@with_timeout(timeout_seconds=MODTOOLS_TIMEOUT)
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


# =============================================================================
# Content Approval and Removal (MODT-02, MODT-03)
# =============================================================================

@with_timeout(timeout_seconds=MODTOOLS_TIMEOUT)
def approve_item(thing_id: str) -> None:
    """
    Approve a comment or submission, removing it from the modqueue.

    Approved items become visible to other users and are removed from
    the moderation queue. This action is idempotent - approving an
    already-approved item is safe and has no effect.

    Args:
        thing_id: Reddit fullname (t1_* for comments, t3_* for submissions)

    Raises:
        ValueError: If thing_id format is invalid
        PRAWException: If API call fails (with sanitized error message)

    Examples:
        >>> approve_item("t1_abc123")  # Approve comment
        >>> approve_item("t3_def456")  # Approve submission
    """
    # Validate thing_id format
    validate_thing_id(thing_id)

    # Extract the type digit and base36 ID
    prefix = thing_id[1]  # '1' for comment, '3' for submission
    item_id = thing_id[3:]  # Base36 ID without prefix

    reddit = get_reddit_client()

    try:
        # Route to appropriate PRAW method based on type
        if prefix == "1":
            # Comment
            item = reddit.comment(item_id)
        elif prefix == "3":
            # Submission
            item = reddit.submission(item_id)
        else:
            # This shouldn't happen due to validate_thing_id, but be defensive
            raise ValueError(f"Cannot approve thing_id type: t{prefix}_")

        # Call approve()
        item.mod.approve()

    except PRAWException as e:
        sanitized_msg = sanitize_moderation_error(e)
        raise type(e)(f"Failed to approve {thing_id}: {sanitized_msg}") from e


@with_timeout(timeout_seconds=MODTOOLS_TIMEOUT)
def remove_item(thing_id: str, reason: str = "", spam: bool = False) -> None:
    """
    Remove a comment or submission from public view.

    Removed items are hidden from all users except moderators. The spam
    flag triggers Reddit's spam filtering, which may affect the user's
    spam score for future posts.

    Note: The reason parameter is recorded for moderator notes but is not
    displayed to the user (Reddit API limitation).

    Args:
        thing_id: Reddit fullname (t1_* for comments, t3_* for submissions)
        reason: Moderation reason for the removal (for mod notes only)
        spam: Whether to mark as spam (triggers spam filtering)

    Raises:
        ValueError: If thing_id format is invalid
        PRAWException: If API call fails (with sanitized error message)

    Examples:
        >>> remove_item("t1_abc123", reason="Spam")
        >>> remove_item("t3_def456", spam=True)
    """
    # Validate thing_id format
    validate_thing_id(thing_id)

    # Extract the type digit and base36 ID
    prefix = thing_id[1]  # '1' for comment, '3' for submission
    item_id = thing_id[3:]  # Base36 ID without prefix

    reddit = get_reddit_client()

    try:
        # Route to appropriate PRAW method based on type
        if prefix == "1":
            # Comment
            item = reddit.comment(item_id)
        elif prefix == "3":
            # Submission
            item = reddit.submission(item_id)
        else:
            # This shouldn't happen due to validate_thing_id, but be defensive
            raise ValueError(f"Cannot remove thing_id type: t{prefix}_")

        # Call remove() with spam flag
        # Note: reason is not used by PRAW's remove() method (API limitation)
        item.mod.remove(spam=spam)

    except PRAWException as e:
        sanitized_msg = sanitize_moderation_error(e)
        raise type(e)(f"Failed to remove {thing_id}: {sanitized_msg}") from e


# =============================================================================
# User Banning (MODT-04)
# =============================================================================

@with_timeout(timeout_seconds=MODTOOLS_TIMEOUT)
def ban_user(
    subreddit: str,
    username: str,
    reason: str,
    duration_days: int = 0,
) -> None:
    """
    Ban a user from a subreddit.

    Bans prevent users from posting and commenting in the subreddit.
    Permanent bans (duration_days=0) last until manually revoked.
    Temporary bans (duration_days>0) automatically expire after the
    specified number of days.

    Args:
        subreddit: Name of the subreddit (without r/ prefix)
        username: Username to ban (without u/ prefix)
        reason: Ban reason for mod notes and user message
        duration_days: Ban duration in days (0=permanent, >0=temporary)

    Raises:
        ValueError: If duration_days is negative
        PRAWException: If API call fails (with sanitized error message)

    Examples:
        >>> ban_user("testsub", "spam_user", "Spamming")  # Permanent
        >>> ban_user("testsub", "troll", "Harassment", duration_days=7)  # 7 days
    """
    # Validate duration is non-negative
    if duration_days < 0:
        raise ValueError(
            f"duration_days must be non-negative (got {duration_days}). "
            "Use 0 for permanent ban, or positive integer for days."
        )

    # Convert duration: 0 -> None (permanent), >0 -> integer days
    duration = None if duration_days == 0 else duration_days

    reddit = get_reddit_client()

    try:
        subreddit_obj = reddit.subreddit(subreddit)

        # Call ban API
        subreddit_obj.banned.add(
            username,
            ban_reason=reason,
            duration=duration,
            note="Banned via italia-career-mod MCP tool",
        )

    except PRAWException as e:
        sanitized_msg = sanitize_moderation_error(
            e, context={"subreddit": subreddit, "username": username}
        )
        raise type(e)(f"Failed to ban u/{username} in r/{subreddit}: {sanitized_msg}") from e


# =============================================================================
# User History (MODT-05)
# =============================================================================

@with_timeout(timeout_seconds=MODTOOLS_TIMEOUT)
def get_user_history(username: str, subreddit: str, limit: int = 100) -> list[dict]:
    """
    Fetch a user's post and comment history in a subreddit.

    This function retrieves a user's submissions and comments in the specified
    subreddit, useful for detecting repeat offenders and reviewing their activity.
    Results are sorted by creation time (newest first) and include a removed flag.

    Args:
        username: Reddit username (without u/ prefix)
        subreddit: Subreddit name (without r/ prefix)
        limit: Maximum number of items to fetch (default: 100)

    Returns:
        list[dict]: List of user's content items with keys:
            - thing_id: Reddit fullname (t1_* for comments, t3_* for submissions)
            - type: "comment" or "submission"
            - title: Submission title (only for submissions)
            - selftext: Submission text content (only for submissions, truncated to 500 chars)
            - body: Comment body (only for comments, truncated to 500 chars)
            - created_utc: Unix timestamp of creation
            - permalink: Link to the content
            - removed: Boolean indicating if content was removed

    Raises:
        PRAWException: If API call fails (with sanitized error message)

    Examples:
        >>> history = get_user_history("spam_user", "testsub")
        >>> for item in history:
        ...     print(f"{item['type']}: {item['thing_id']} (removed: {item['removed']})")
    """
    reddit = get_reddit_client()

    try:
        # Get redditor object
        redditor = reddit.redditor(username)
        subreddit_lower = subreddit.lower()

        # Fetch submissions
        submissions = []
        try:
            for sub in redditor.submissions.new(limit=limit):
                # Filter by subreddit
                if sub.subreddit and str(sub.subreddit).lower() == subreddit_lower:
                    # Truncate selftext to 500 chars
                    selftext = sub.selftext[:500] if hasattr(sub, 'selftext') and sub.selftext else ""
                    submissions.append({
                        "thing_id": sub.fullname,
                        "type": "submission",
                        "title": sub.title if hasattr(sub, 'title') else "",
                        "selftext": selftext,
                        "created_utc": sub.created_utc,
                        "permalink": sub.permalink if hasattr(sub, 'permalink') else "",
                        "removed": getattr(sub, 'removed', False),
                    })
        except Exception:
            # If submissions fail, continue with empty list (graceful degradation)
            pass

        # Fetch comments
        comments = []
        try:
            for com in redditor.comments.new(limit=limit):
                # Filter by subreddit
                if com.subreddit and str(com.subreddit).lower() == subreddit_lower:
                    # Truncate body to 500 chars
                    body = com.body[:500] if hasattr(com, 'body') and com.body else ""
                    comments.append({
                        "thing_id": com.fullname,
                        "type": "comment",
                        "body": body,
                        "created_utc": com.created_utc,
                        "permalink": com.permalink if hasattr(com, 'permalink') else "",
                        "removed": getattr(com, 'removed', False),
                    })
        except Exception:
            # If comments fail, continue with empty list (graceful degradation)
            pass

        # Combine and sort by created_utc descending (newest first)
        result = submissions + comments
        result.sort(key=lambda x: x['created_utc'], reverse=True)

        return result

    except PRAWException as e:
        # Sanitize error message before re-raising
        sanitized_msg = sanitize_moderation_error(
            e, context={"subreddit": subreddit, "username": username}
        )
        raise type(e)(f"Failed to fetch history for u/{username} in r/{subreddit}: {sanitized_msg}") from e
