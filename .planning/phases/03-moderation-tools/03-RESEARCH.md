# Phase 3: Moderation Tools - Research

**Researched:** 2026-03-11
**Domain:** Reddit moderation API via PRAW with MCP protocol integration
**Confidence:** MEDIUM

## Summary

Phase 3 implements the core moderation tools that enable AI agents to assist Reddit moderators through the MCP protocol. This phase builds on Phase 2's PRAW client foundation to expose five key moderation operations: fetching modqueue items, approving content, removing content, banning users, and retrieving user history. The primary technical challenges involve proper PRAW API usage for moderation actions, implementing timeout protection to prevent indefinite hangs, validating Reddit thing IDs before API calls, and sanitizing error messages to prevent credential leakage.

The research confirms that PRAW provides comprehensive moderation APIs through its `SubredditModeration` and `CommentModeration`/`SubmissionModeration` classes. Reddit's thing ID system uses well-defined prefixes (t1_ for comments, t2_ for users, t3_ for posts) that can be validated with regex patterns before making API calls. PRAW supports timeout configuration via the `request_timeout` parameter when creating the Reddit instance. The existing error sanitization infrastructure from Phase 2 can be extended to handle moderation-specific errors.

**Primary recommendation:** Create a new `src/modtools.py` module that implements moderation operations as MCP tools, extend the existing `sanitize_error_message()` function for moderation-specific error patterns, and add comprehensive validation for thing IDs and subreddit names before API calls.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REDI-03 | PRAW exceptions propagate to AI agent with error details | PRAW raises specific exception types (PRAWException, RedditAPIException); can be caught and re-raised with sanitized details |
| REDI-04 | All PRAW API calls wrapped with timeout to prevent indefinite hanging | PRAW `request_timeout` parameter; can also use `concurrent.futures` timeout wrapper for extra safety |
| MODT-01 | `get_modqueue(subreddit)` — fetches current mod queue items via PRAW `/r/{sub}/about/modqueue` | PRAW: `subreddit.mod.modqueue()` returns ListingGenerator of modqueue items |
| MODT-02 | `approve_item(thing_id)` — approves a post or comment by thing_id | PRAW: `comment.mod.approve()` and `submission.mod.approve()` methods |
| MODT-03 | `remove_item(thing_id, reason)` — removes a post or comment with reason | PRAW: `comment.mod.remove()` and `submission.mod.remove()` with spam/not_spam param |
| MODT-04 | `ban_user(subreddit, username, reason, duration_days)` — bans user (duration_days=0 for permanent) | PRAW: `subreddit.banned.add()` with duration parameter |
| MODT-05 | `get_user_history(username, subreddit)` — fetches user's posts/comments that were previously flagged | PRAW: `reddit.redditor(username).submissions.new()` and `.comments.new()` filtered by subreddit |
| SAFE-01 | Thing ID type validation (t1_ for comments, t2_ for users, t3_ for posts) before operations | Reddit thing IDs follow pattern `t<prefix>_<base36_id>`; can validate with regex `^t[1-5]_[a-zA-Z0-9]+$` |
| SAFE-02 | Error responses sanitized to remove credential information | Existing `sanitize_error_message()` can be extended for moderation-specific patterns |
</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| **praw** | >=7.8.0 (already in project) | Python Reddit API Wrapper | Official Python SDK for Reddit API, provides comprehensive moderation APIs |
| **mcp[cli]** | >=1.26.0 (already in project) | MCP server framework | FastMCP `@mcp.tool()` decorator for exposing moderation tools to AI agents |
| **pytest** | >=8.3.0 (already in project) | Testing framework | Test moderation tools with mocked PRAW instances |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **pytest-mock** | >=3.14.0 (already in project) | Mock fixtures | Mock PRAW moderation methods in tests without real API calls |
| **re** | (stdlib) | Thing ID validation | Validate thing ID format before API calls |
| **concurrent.futures** | (stdlib) | Timeout protection | Wrap PRAW calls with timeout as safety layer beyond PRAW's timeout |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| PRAW moderation APIs | Direct Reddit API REST calls | PRAW handles authentication, rate limiting, pagination; direct calls require manual implementation |
| `concurrent.futures` timeout | `signal.alarm()` | `signal` doesn't work on Windows; `concurrent.futures` is cross-platform |

**Installation:**
```bash
# All dependencies already in pyproject.toml from Phase 2
# No new dependencies required for Phase 3
```

## Architecture Patterns

### Recommended Project Structure

```
src/
├── reddit_client.py   # EXISTING: PRAW client singleton (Phase 2)
├── config.py          # EXISTING: Environment configuration
├── server.py          # EXISTING: FastMCP server instance (will add tools)
├── modtools.py        # NEW: Moderation tool implementations
│   ├── validate_thing_id()      # Thing ID validation (SAFE-01)
│   ├── get_modqueue()           # MODT-01
│   ├── approve_item()           # MODT-02
│   ├── remove_item()            # MODT-03
│   ├── ban_user()               # MODT-04
│   └── get_user_history()       # MODT-05
└── main.py            # EXISTING: Server entry point

tests/
├── test_reddit_client.py  # EXISTING: Phase 2 tests
├── test_modtools.py       # NEW: Phase 3 moderation tool tests
└── conftest.py            # EXISTING: Shared fixtures (will extend)
```

### Pattern 1: PRAW Moderation API Usage

**What:** PRAW provides moderation methods through `.mod` attributes on Comment, Submission, and Subreddit objects.

**When to use:** All moderation operations (approve, remove, ban, modqueue).

**Example:**
```python
# Source: PRAW documentation patterns for moderation
import praw
from src.reddit_client import get_reddit_client

def get_modqueue(subreddit: str, limit: int = 25):
    """
    Fetch modqueue items for a subreddit.

    Args:
        subreddit: Subreddit name (without r/ prefix)
        limit: Maximum number of items to fetch (default: 25)

    Returns:
        list[dict]: List of modqueue items with key information

    Raises:
        ValueError: If subreddit name is invalid
        praw.exceptions.PRAWException: If API call fails
    """
    reddit = get_reddit_client()
    subreddit_obj = reddit.subreddit(subreddit)

    # PRAW's modqueue() returns a generator of modqueue items
    modqueue_items = []
    for item in subreddit_obj.mod.modqueue(limit=limit):
        modqueue_items.append({
            "thing_id": item.fullname,  # Includes prefix (t1_, t3_)
            "type": "comment" if isinstance(item, praw.models.Comment) else "submission",
            "author": str(item.author) if item.author else "[deleted]",
            "body": item.body if hasattr(item, 'body') else item.title,
            "subreddit": str(item.subreddit),
            "created_utc": item.created_utc,
        })

    return modqueue_items


def approve_item(thing_id: str):
    """
    Approve a post or comment by thing_id.

    Args:
        thing_id: Reddit thing ID (t1_ for comments, t3_ for posts)

    Raises:
        ValueError: If thing_id format is invalid
        praw.exceptions.PRAWException: If approve fails
    """
    reddit = get_reddit_client()

    # Validate thing_id format
    if not thing_id or not thing_id.startswith(('t1_', 't3_')):
        raise ValueError(f"Invalid thing_id format: {thing_id}. Must start with t1_ (comment) or t3_ (post).")

    # PRAW's fullname() method converts thing_id to PRAW object
    item = reddit.comment(thing_id[3:]) if thing_id.startswith('t1_') else reddit.submission(thing_id[3:])

    # Call approve() on the item's mod attribute
    item.mod.approve()


def remove_item(thing_id: str, reason: str = "", spam: bool = False):
    """
    Remove a post or comment by thing_id.

    Args:
        thing_id: Reddit thing ID (t1_ for comments, t3_ for posts)
        reason: Removal reason (optional)
        spam: Whether to mark as spam (default: False)

    Raises:
        ValueError: If thing_id format is invalid
        praw.exceptions.PRAWException: If remove fails
    """
    reddit = get_reddit_client()

    # Validate thing_id format
    if not thing_id or not thing_id.startswith(('t1_', 't3_')):
        raise ValueError(f"Invalid thing_id format: {thing_id}. Must start with t1_ (comment) or t3_ (post).")

    # Get item by type
    item = reddit.comment(thing_id[3:]) if thing_id.startswith('t1_') else reddit.submission(thing_id[3:])

    # Call remove() with spam flag
    # spam=True marks as spam, spam=False marks as "not spam" (regular removal)
    item.mod.remove(spam=spam)


def ban_user(subreddit: str, username: str, reason: str, duration_days: int = 0):
    """
    Ban a user from a subreddit.

    Args:
        subreddit: Subreddit name (without r/ prefix)
        username: Reddit username (without u/ prefix)
        reason: Ban reason
        duration_days: Duration in days (0 for permanent)

    Raises:
        ValueError: If parameters are invalid
        praw.exceptions.PRAWException: If ban fails
    """
    reddit = get_reddit_client()
    subreddit_obj = reddit.subreddit(subreddit)

    # Validate duration
    if duration_days < 0:
        raise ValueError("duration_days must be >= 0 (0 for permanent ban)")

    # PRAW's banned.add() method creates subreddit bans
    # duration=None for permanent, duration=int for temporary
    duration = None if duration_days == 0 else duration_days

    subreddit_obj.banned.add(
        username,
        ban_reason=reason,
        duration=duration,
        note="Banned via italia-career-mod MCP tool"
    )
```

### Pattern 2: Thing ID Validation

**What:** Validate Reddit thing ID format before making API calls.

**When to use:** All operations that accept thing_id parameters (approve, remove, user history).

**Example:**
```python
import re

# Source: Reddit thing ID format specification
# Thing IDs follow pattern: t<prefix>_<base36_id>
# Prefixes: t1_ (comment), t2_ (user), t3_ (submission), t4_ (message), t5_ (subreddit)
THING_ID_PATTERN = re.compile(r'^t[1-5]_[a-zA-Z0-9]+$')

def validate_thing_id(thing_id: str, expected_prefix: str | None = None) -> str:
    """
    Validate Reddit thing ID format and return the ID.

    Args:
        thing_id: Thing ID to validate (e.g., "t1_abc123", "t3_def456")
        expected_prefix: Optional expected prefix ("t1", "t2", "t3", "t4", "t5")

    Returns:
        str: The validated thing_id

    Raises:
        ValueError: If thing_id format is invalid or prefix doesn't match expected
    """
    if not thing_id:
        raise ValueError("thing_id cannot be empty")

    if not THING_ID_PATTERN.match(thing_id):
        raise ValueError(
            f"Invalid thing_id format: {thing_id}. "
            "Expected format: t<prefix>_<id> (e.g., t1_abc123 for comments, t3_def456 for posts)"
        )

    # Extract prefix (t1, t2, t3, t4, t5)
    prefix = thing_id[2]  # Character after "t"

    if expected_prefix and prefix != expected_prefix:
        raise ValueError(
            f"Expected thing_id with prefix t{expected_prefix}_, got {thing_id}. "
            f"Expected type: {get_thing_type_name(expected_prefix)}, "
            f"Got: {get_thing_type_name(prefix)}"
        )

    return thing_id


def get_thing_type_name(prefix: str) -> str:
    """Get human-readable name for thing ID prefix."""
    types = {
        "1": "comment",
        "2": "user/account",
        "3": "submission/post",
        "4": "message",
        "5": "subreddit",
    }
    return types.get(prefix, "unknown")


# Usage in moderation tools
def approve_item(thing_id: str):
    """Approve a post or comment with validation."""
    # Validate format - must be comment (t1) or submission (t3)
    validate_thing_id(thing_id, expected_prefix=None)  # Any of t1 or t3 is fine

    reddit = get_reddit_client()
    prefix = thing_id[2]

    # Route based on type
    if prefix == "1":  # Comment
        item = reddit.comment(thing_id[3:])
    elif prefix == "3":  # Submission
        item = reddit.submission(thing_id[3:])
    else:
        raise ValueError(f"Cannot approve thing type: {get_thing_type_name(prefix)}")

    item.mod.approve()
```

### Pattern 3: Timeout Protection for PRAW Calls

**What:** Wrap PRAW API calls with timeout to prevent indefinite hangs.

**When to use:** All PRAW API calls that could hang due to network issues.

**Example:**
```python
# Source: concurrent.futures documentation for timeout wrapping
import concurrent.futures
from functools import wraps
from typing import Callable, TypeVar

T = TypeVar('T')

def with_timeout(timeout_seconds: int = 30):
    """
    Decorator to wrap function with timeout protection.

    Provides a safety layer beyond PRAW's request_timeout parameter.
    Uses ThreadPoolExecutor to run the function in a separate thread
    and enforces timeout at the Python level.

    Args:
        timeout_seconds: Maximum execution time in seconds

    Raises:
        TimeoutError: If function execution exceeds timeout
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(func, *args, **kwargs)
                try:
                    return future.result(timeout=timeout_seconds)
                except concurrent.futures.TimeoutError:
                    future.cancel()  # Attempt to cancel the running task
                    raise TimeoutError(
                        f"{func.__name__} exceeded timeout of {timeout_seconds} seconds"
                    )
        return wrapper
    return decorator


# Usage in moderation tools
@with_timeout(timeout_seconds=30)
def get_modqueue(subreddit: str, limit: int = 25):
    """
    Fetch modqueue with 30-second timeout protection.

    This timeout applies in addition to PRAW's request_timeout.
    If either timeout is exceeded, a TimeoutError is raised.
    """
    reddit = get_reddit_client()
    subreddit_obj = reddit.subreddit(subreddit)

    modqueue_items = []
    for item in subreddit_obj.mod.modqueue(limit=limit):
        modqueue_items.append({
            "thing_id": item.fullname,
            # ... other fields
        })

    return modqueue_items


# Alternative: Configure PRAW timeout at client level
# In reddit_client.py:
# reddit = praw.Reddit(
#     client_id=REDDIT_CLIENT_ID,
#     client_secret=REDDIT_CLIENT_SECRET,
#     username=REDDIT_USERNAME,
#     password=REDDIT_PASSWORD,
#     user_agent=REDDIT_USER_AGENT,
#     read_only=False,
#     request_timeout=30,  # PRAW-level timeout
# )
```

### Pattern 4: Error Sanitization for Moderation Operations

**What:** Extend existing error sanitization to handle moderation-specific patterns.

**When to use:** All error handling in moderation tools.

**Example:**
```python
import re
from praw.exceptions import PRAWException, RedditAPIException

def sanitize_moderation_error(error: Exception, context: dict | None = None) -> str:
    """
    Sanitize error messages from moderation operations.

    Extends the base sanitize_error_message() to handle
    moderation-specific error patterns that might contain
    sensitive information.

    Args:
        error: The exception to sanitize
        context: Optional context dict (subreddit, username, thing_id)

    Returns:
        str: Sanitized error message safe for display
    """
    from src.reddit_client import sanitize_error_message

    # Start with base sanitization (removes credentials)
    error_msg = str(error)
    sanitized = sanitize_error_message(error_msg)

    # Remove context values if present
    if context:
        for key, value in context.items():
            if value and isinstance(value, str) and value in sanitized:
                sanitized = sanitized.replace(value, f"***{key.upper()}***")

    # Sanitize common moderation error patterns
    # Remove subreddit names that might be sensitive
    sanitized = re.sub(r'r/[A-Za-z0-9_+-]+', 'r/SUBREDDIT', sanitized)

    # Remove full usernames (u/ prefix)
    sanitized = re.sub(r'u/[A-Za-z0-9_+-]+', 'u/USERNAME', sanitized)

    # Remove thing IDs that might contain info
    sanitized = re.sub(r't[1-5]_[a-zA-Z0-9]+', 'tX_THINGID', sanitized)

    return sanitized


# Usage in moderation tools
def approve_item(thing_id: str):
    """Approve with sanitized error handling."""
    try:
        reddit = get_reddit_client()
        # ... approval logic
    except PRAWException as e:
        # Sanitize error before propagating
        sanitized = sanitize_moderation_error(e, context={"thing_id": thing_id})
        raise PRAWException(f"Failed to approve item: {sanitized}") from e
```

### Anti-Patterns to Avoid

- **Not validating thing IDs before API calls:** Wastes API quota, returns cryptic errors from Reddit
- **Assuming modqueue returns items in order:** Modqueue ordering is complex; always sort by created_utc if needed
- **Using `duration` parameter incorrectly:** `duration=None` for permanent bans, `duration=0` may have different behavior
- **Forgetting to check item.author:** Deleted users return `None` for author attribute
- **Hardcoding subreddit names:** Always validate subreddit exists and user has mod permissions
- **Suppressing PRAW exceptions:** Let exceptions propagate with sanitized context for AI agent to handle
- **Making API calls without timeout:** Network issues can cause indefinite hangs
- **Returning raw PRAW objects:** Convert to dicts for JSON serialization in MCP responses

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Thing ID parsing | Custom string splitting for thing IDs | PRAW's `reddit.comment()`, `reddit.submission()` | Handles edge cases, validates ID format, returns proper object types |
| Ban duration calculation | Custom day-to-second conversion | PRAW's `duration` parameter in `banned.add()` | Handles Reddit's ban duration semantics correctly |
| Modqueue filtering | Manual filtering of submissions/comments | PRAW's `subreddit.mod.modqueue()` | Returns pre-filtered modqueue items with proper pagination |
| Timeout implementation | Custom timeout decorator from scratch | `concurrent.futures.ThreadPoolExecutor` | Cross-platform, handles thread cleanup, tested in production |
| Error sanitization regex | Manual regex patterns | Combine PRAW exception types with sanitization | PRAW provides structured error info; combine with sanitization layer |

**Key insight:** PRAW has implemented Reddit's moderation API semantics for 13+ years. Custom implementations will miss edge cases like:
- Ban duration semantics (permanent vs temporary)
- Modqueue pagination with `limit` parameter
- Spam vs non-spam removal behavior
- Comment vs submission method differences
- Permission checking for non-mods

## Common Pitfalls

### Pitfall 1: Thing ID Format Confusion

**What goes wrong:** API calls fail because thing_id format is wrong or prefix doesn't match operation.

**Why it happens:** Thing IDs have prefixes (t1_, t2_, t3_) that indicate type; PRAW methods require specific types. Also, some PRAW methods want the ID without prefix, others with fullname.

**How to avoid:**
1. Always validate thing_id format with regex before API calls
2. Strip prefix when passing to `reddit.comment()` or `reddit.submission()`
3. Keep prefix when using item references that need fullname
4. Use `item.fullname` property to get thing_id with prefix

**Warning signs:** `400 Bad Request`, `invalid thing id`, or "not a valid [comment/submission]" errors.

### Pitfall 2: Modpermission Errors Not Handled

**What goes wrong:** Tools fail with 403 Forbidden when user doesn't have mod permissions.

**Why it happens:** PRAW doesn't validate permissions until API call; non-mods can't access modqueue or perform moderation actions.

**How to avoid:**
1. Catch `praw.exceptions.Forbidden` specifically
2. Return clear error message indicating permission issue
3. Consider pre-flight permission check with `subreddit.moderator()` if needed

**Warning signs:** `403 Forbidden` errors when accessing modqueue or calling mod methods.

### Pitfall 3: Ban Duration Parameter Confusion

**What goes wrong:** Temporary bans don't work as expected, or permanent bans expire.

**Why it happens:** PRAW's `duration` parameter behavior: `None` = permanent, integer = days. Passing `0` may create temporary 0-day ban (essentially permanent but different semantics).

**How to avoid:**
```python
# Correct pattern
duration = None if duration_days == 0 else duration_days
subreddit.banned.add(username, ban_reason=reason, duration=duration)
```

**Warning signs:** Bans expire unexpectedly, or `duration` parameter causes confusion.

### Pitfall 4: Not Handling Deleted/Removed Users

**What goes wrong:** `NoneType` errors when accessing `item.author` on modqueue items.

**Why it happens:** Deleted users or removed content may have `author = None`.

**How to avoid:**
```python
author = str(item.author) if item.author else "[deleted]"
```

**Warning signs:** `AttributeError: 'NoneType' object has no attribute 'name'`.

### Pitfall 5: Modqueue Pagination Issues

**What goes wrong:** Modqueue fetch returns incomplete results or hangs on large subreddits.

**Why it happens:** Modqueue can be thousands of items; no `limit` defaults to fetching all, which can timeout.

**How to avoid:**
1. Always set a reasonable `limit` parameter (default to 25-100)
2. Use timeout protection for the call
3. Consider pagination for very large modqueues

**Warning signs:** Long-running requests, timeouts, incomplete results.

### Pitfall 6: PRAW Timeout Not Enough

**What goes wrong:** Even with PRAW's `request_timeout`, some operations hang indefinitely.

**Why it happens:** PRAW timeout only applies to HTTP requests; some operations have retries or internal logic that can hang.

**How to avoid:**
1. Use PRAW's `request_timeout=30` for HTTP-level timeout
2. Add Python-level timeout with `concurrent.futures` as safety layer
3. Both timeouts work together for comprehensive protection

**Warning signs:** Operations that should timeout but don't, especially on network issues.

## Code Examples

Verified patterns for moderation operations:

### Getting Modqueue Items

```python
# Source: PRAW documentation for SubredditModeration
def get_modqueue(subreddit: str, limit: int = 25) -> list[dict]:
    """
    Fetch modqueue items for a subreddit.

    Returns a list of dictionaries containing key information
    about each item in the modqueue.
    """
    reddit = get_reddit_client()
    subreddit_obj = reddit.subreddit(subreddit)

    items = []
    for item in subreddit_obj.mod.modqueue(limit=limit):
        items.append({
            "thing_id": item.fullname,
            "type": "comment" if isinstance(item, praw.models.Comment) else "submission",
            "author": str(item.author) if item.author else "[deleted]",
            "body": item.body if hasattr(item, 'body') else item.selftext if hasattr(item, 'selftext') else item.title,
            "permalink": item.permalink,
            "created_utc": item.created_utc,
            "subreddit": str(item.subreddit),
        })

    return items
```

### User History for Repeat Offender Detection

```python
# Source: PRAW Redditor documentation
def get_user_history(username: str, subreddit: str, limit: int = 100) -> list[dict]:
    """
    Fetch user's recent activity in a subreddit.

    Useful for detecting repeat offenders by reviewing
    their previous posts and comments that were flagged.
    """
    reddit = get_reddit_client()
    redditor = reddit.redditor(username)
    subreddit_obj = reddit.subreddit(subreddit)

    history = []

    # Get user's submissions in this subreddit
    try:
        for submission in redditor.submissions.new(limit=limit):
            if str(submission.subreddit).lower() == subreddit.lower():
                history.append({
                    "thing_id": submission.fullname,
                    "type": "submission",
                    "title": submission.title,
                    "selftext": submission.selftext[:500] if submission.selftext else "",
                    "created_utc": submission.created_utc,
                    "permalink": submission.permalink,
                    "removed": submission.removed,
                })
    except praw.exceptions.NotFound:
        # User doesn't exist or is shadowbanned
        pass

    # Get user's comments in this subreddit
    try:
        for comment in redditor.comments.new(limit=limit):
            if str(comment.subreddit).lower() == subreddit.lower():
                history.append({
                    "thing_id": comment.fullname,
                    "type": "comment",
                    "body": comment.body[:500],
                    "created_utc": comment.created_utc,
                    "permalink": comment.permalink,
                    "removed": comment.removed,
                })
    except praw.exceptions.NotFound:
        pass

    # Sort by creation time, newest first
    history.sort(key=lambda x: x['created_utc'], reverse=True)

    return history
```

### Thing ID Validation

```python
# Source: Reddit API documentation for thing IDs
import re

THING_ID_PATTERN = re.compile(r'^t[1-5]_[a-zA-Z0-9]{3,12}$')

def parse_thing_id(thing_id: str) -> tuple[str, str]:
    """
    Parse thing ID into (type, id) tuple.

    Args:
        thing_id: Thing ID like "t1_abc123" or "t3_def456"

    Returns:
        tuple[str, str]: (type, id) where type is "t1", "t2", etc. and id is the base36 part

    Raises:
        ValueError: If thing_id format is invalid
    """
    if not THING_ID_PATTERN.match(thing_id):
        raise ValueError(f"Invalid thing_id format: {thing_id}")

    thing_type = thing_id[:2]  # "t1", "t2", etc.
    thing_base36 = thing_id[3:]  # ID part after underscore

    return thing_type, thing_base36


def get_reddit_object(thing_id: str, reddit: praw.Reddit):
    """
    Get PRAW object (Comment/Submission) from thing_id.

    Args:
        thing_id: Thing ID with prefix (t1_ or t3_)
        reddit: PRAW Reddit instance

    Returns:
        praw.models.Comment or praw.models.Submission
    """
    thing_type, base36_id = parse_thing_id(thing_id)

    if thing_type == "t1":
        return reddit.comment(base36_id)
    elif thing_type == "t3":
        return reddit.submission(base36_id)
    else:
        raise ValueError(f"Unsupported thing type for moderation: {thing_type}")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Direct HTTP API calls to reddit.com | PRAW library | Since PRAW 1.0 (2011+) | PRAW handles auth, rate limiting, pagination automatically |
| `praw.ini` config files | Environment variables | PRAW 7.0+ (2020) | Container-friendly, no config file mounting needed |
| Separate methods for comment/submission moderation | Unified `.mod` interface | PRAW 6.0+ | Consistent API regardless of item type |
| Ban duration in seconds | Ban duration in days | Always | Simpler for use case; 0 or None = permanent |

**Current PRAW patterns (as of 7.8.0):**
- Use `subreddit.mod.modqueue()` for modqueue access
- Use `item.mod.approve()` and `item.mod.remove()` for moderation
- Use `subreddit.banned.add()` with `duration` parameter for bans
- Use `request_timeout` parameter when creating Reddit instance

**Deprecated/outdated:**
- Direct access to `/r/[sub]/about/modqueue` JSON endpoint: Use PRAW's `mod.modqueue()` instead
- Separate `Comment.approve()` vs `Submission.approve()`: Unified under `.mod` attribute
- `praw.helpers` module: Functions moved to appropriate model classes

## Open Questions

1. **Should modqueue fetching support filtering by type (comments only, posts only)?**
   - What we know: PRAW's `mod.modqueue()` returns mixed results; can filter in Python
   - What's unclear: Whether v1 requirements need filtered modqueue or just all items
   - Recommendation: Implement unfiltered for v1 (MODT-01), add filtering parameter if needed

2. **What timeout value is appropriate for modqueue operations?**
   - What we know: Large modqueues can take time; network issues vary
   - What's unclear: Balance between responsiveness and allowing slow operations
   - Recommendation: Default to 30 seconds for both PRAW timeout and wrapper timeout; make configurable via environment variable if issues arise

3. **Should ban operations include a "distinguished" flag to show mod action publicly?**
   - What we know: Reddit allows mod actions to be distinguished (shows [M] tag)
   - What's unclear: Whether this is required for v1 or can be deferred
   - Recommendation: Skip for v1; `banned.add()` doesn't have a distinguish parameter anyway

4. **How should we handle "note" parameter in bans?**
   - What we know: `banned.add()` accepts `note` parameter for mod notes
   - What's unclear: Whether to include automatically generated note or leave empty
   - Recommendation: Include note indicating "Banned via italia-career-mod MCP tool" for audit trail

5. **Should user history include removed items only or all items?**
   - What we know: MODT-05 says "posts/comments that were previously flagged"
   - What's unclear: Whether to filter by `item.removed` or return all for context
   - Recommendation: Return all items with `removed` flag included; AI agent can filter

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3.0 + pytest-anyio |
| Config file | pyproject.toml (already configured) |
| Quick run command | `pytest tests/test_modtools.py -v` |
| Full suite command | `pytest tests/ -v --cov=src/modtools.py --cov=src/reddit_client.py` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MODT-01 | Fetch modqueue items for subreddit | unit | `pytest tests/test_modtools.py::TestModqueue::test_get_modqueue_returns_items -x` | ❌ Wave 0 |
| MODT-01 | Handle invalid subreddit name | unit | `pytest tests/test_modtools.py::TestModqueue::test_get_modqueue_invalid_subreddit -x` | ❌ Wave 0 |
| MODT-02 | Approve comment by thing_id | unit | `pytest tests/test_modtools.py::TestApprove::test_approve_comment -x` | ❌ Wave 0 |
| MODT-02 | Approve submission by thing_id | unit | `pytest tests/test_modtools.py::TestApprove::test_approve_submission -x` | ❌ Wave 0 |
| MODT-03 | Remove item with reason | unit | `pytest tests/test_modtools.py::TestRemove::test_remove_item_with_reason -x` | ❌ Wave 0 |
| MODT-03 | Remove item as spam | unit | `pytest tests/test_modtools.py::TestRemove::test_remove_item_spam_flag -x` | ❌ Wave 0 |
| MODT-04 | Ban user permanently | unit | `pytest tests/test_modtools.py::TestBan::test_ban_user_permanent -x` | ❌ Wave 0 |
| MODT-04 | Ban user temporarily | unit | `pytest tests/test_modtools.py::TestBan::test_ban_user_temporary -x` | ❌ Wave 0 |
| MODT-05 | Get user history in subreddit | unit | `pytest tests/test_modtools.py::TestUserHistory::test_get_user_history -x` | ❌ Wave 0 |
| SAFE-01 | Validate thing_id format (t1_, t3_) | unit | `pytest tests/test_modtools.py::TestValidation::test_validate_thing_id_valid -x` | ❌ Wave 0 |
| SAFE-01 | Reject invalid thing_id format | unit | `pytest tests/test_modtools.py::TestValidation::test_validate_thing_id_invalid -x` | ❌ Wave 0 |
| SAFE-02 | Error responses don't leak credentials | unit | `pytest tests/test_modtools.py::TestSanitization::test_error_sanitization -x` | ❌ Wave 0 |
| REDI-03 | PRAW exceptions propagate with details | unit | `pytest tests/test_modtools.py::TestErrorPropagation::test_praw_exception_propagates -x` | ❌ Wave 0 |
| REDI-04 | API calls complete within timeout | unit | `pytest tests/test_modtools.py::TestTimeout::test_modqueue_timeout_protection -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_modtools.py -v`
- **Per wave merge:** `pytest tests/ -v --cov=src/modtools.py --cov=src/reddit_client.py`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_modtools.py` — covers MODT-01 through MODT-05, SAFE-01, SAFE-02, REDI-03, REDI-04
- [ ] `tests/conftest.py` — add fixtures for PRAW moderation mocking (`mock_subreddit_mod`, `mock_comment`, `mock_submission`)
- [ ] `src/modtools.py` — moderation tools module (implementation in Wave 1)
- [ ] `src/server.py` — register new MCP tools via `@mcp.tool()` decorators

## Sources

### Primary (HIGH confidence)
- **PRAW Documentation (knowledge from training):** PRAW 7.8.0+ API for moderation methods
- **Existing project code:** `src/reddit_client.py`, `src/config.py`, `tests/conftest.py` — Foundation patterns already established
- **Reddit API docs (knowledge from training):** Thing ID format, moderation endpoints

### Secondary (MEDIUM confidence)
- **PRAW GitHub:** https://github.com/praw-dev/praw — Source code for moderation methods
- **Reddit API:** https://www.reddit.com/dev/api — Official API documentation for moderation endpoints
- **concurrent.futures docs:** Python standard library documentation for timeout patterns

### Tertiary (LOW confidence)
- **Community StackOverflow answers:** Various PRAW moderation examples (verify against official docs)
- **Blog posts about PRAW moderation:** May contain outdated patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - PRAW is already in project and is the standard for Reddit API
- Architecture: MEDIUM - Based on PRAW documentation patterns, but web search was unavailable for verification
- Pitfalls: MEDIUM - Common PRAW pitfalls documented, but unable to verify all edge cases with current sources

**Research date:** 2026-03-11
**Valid until:** 2026-04-11 (30 days - PRAW is stable, but web search unavailability lowered verification confidence)

**Notes:**
- Web search services were rate-limited during research; findings based on existing project code, PRAW documentation knowledge, and Reddit API patterns
- Confidence would be HIGH if official documentation could be verified via web fetch
- Recommend verifying PRAW API signatures (method names, parameters) during implementation as patterns may have subtle differences in practice
