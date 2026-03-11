# Phase 2: Reddit Integration - Research

**Researched:** 2026-03-11
**Domain:** Reddit API integration with PRAW (Python Reddit API Wrapper)
**Confidence:** HIGH

## Summary

Phase 2 focuses on initializing the PRAW (Python Reddit API Wrapper) client with environment-based authentication. This is a foundational phase that enables all subsequent Reddit API interactions in Phase 3 (Moderation Tools). The research confirms that PRAW is the mature, well-maintained standard for Reddit API integration in Python, with native support for script app authentication (the required method) and straightforward environment variable configuration.

The existing project already has environment variable infrastructure in place (`.env.example` and `src/config.py`), so Phase 2 primarily needs to add the PRAW dependency and create a client initialization module. The key implementation detail is that PRAW's `Reddit` class constructor accepts credential parameters directly, eliminating the need for configuration files and enabling clean environment-based authentication.

**Primary recommendation:** Add `praw>=7.8.0` to project dependencies, create `src/reddit_client.py` with lazy initialization pattern, and add comprehensive error handling that sanitizes credential information in error messages.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REDI-01 | PRAW client initialized from environment variables (REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD, REDDIT_USER_AGENT) | PRAW constructor accepts direct credential parameters; existing `src/config.py` already loads these variables |
| REDI-02 | PRAW uses script app authentication (not OAuth) | PRAW's default authentication mode when `username` and `password` are provided; this is the "script" type from Reddit's app preferences |
</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| **praw** | >=7.8.0 | Python Reddit API Wrapper | Official Python SDK for Reddit API, mature (13+ years), active maintenance, excellent documentation |
| **python-dotenv** | >=1.0.0 (already in project) | Environment variable loading | Already in project dependencies; loads `.env` files for local development |
| **pytest** | >=8.3.0 (already in project) | Testing framework | Already in project; will test PRAW initialization with mocks |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **pytest-mock** | >=3.14.0 | Mock fixtures for pytest | Recommended for testing PRAW client initialization without real API calls |
| **responses** | >=0.25.0 | HTTP mocking for tests | Alternative to pytest-mock for mocking PRAW's HTTP requests to Reddit API |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| PRAW | Direct Reddit API REST calls | PRAW handles rate limiting, authentication refresh, pagination, and error handling automatically |
| PRAW | Async Reddit API libraries | PRAW is synchronous but mature; async alternatives less stable, add complexity for Phase 2 scope |

**Installation:**
```bash
# Add to pyproject.toml dependencies
uv add "praw>=7.8.0"

# Or manually add to pyproject.toml [project.dependencies]
# then run:
uv sync
```

## Architecture Patterns

### Recommended Project Structure

```
src/
├── reddit_client.py   # NEW: PRAW client initialization and singleton pattern
├── config.py          # EXISTING: Environment variable loading (no changes needed)
└── server.py          # EXISTING: FastMCP server (will use reddit_client in Phase 3)

tests/
├── test_reddit_client.py  # NEW: Tests for PRAW client initialization
└── conftest.py            # EXISTING: Will add Reddit client fixtures
```

### Pattern 1: Lazy Initialization Singleton

**What:** PRAW client is created once on first access and reused for subsequent calls.

**When to use:** Always - PRAW instances are thread-safe, maintain connection pools, and handle rate limiting internally.

**Example:**
```python
# Source: PRAW documentation - singleton pattern for Reddit client
import praw
from src.config import (
    REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET,
    REDDIT_USERNAME, REDDIT_PASSWORD, REDDIT_USER_AGENT
)

_reddit_instance = None

def get_reddit_client():
    """
    Get or create the PRAW Reddit client instance.

    Uses lazy initialization singleton pattern to ensure only one
    PRAW instance exists per application runtime. PRAW instances
    are thread-safe and handle connection pooling internally.

    Returns:
        praw.Reddit: Authenticated PRAW Reddit client instance.

    Raises:
        ValueError: If required Reddit credentials are missing.
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
        )

        # Verify authentication worked (makes a lightweight API call)
        # This raises praw.exceptions.PRAWException if auth fails
        try:
            _reddit_instance.user.me()
        except Exception as e:
            # Sanitize error to avoid leaking credentials
            raise type(e)(
                f"Reddit authentication failed: {str(e)}. "
                "Please verify your credentials in .env file."
            ) from e

    return _reddit_instance
```

### Pattern 2: Safe Error Handling with Sanitization

**What:** Catch PRAW exceptions and re-raise with credential information removed.

**When to use:** All error paths from PRAW client initialization or API calls.

**Example:**
```python
import re
from praw.exceptions import PRAWException, RedditAPIException

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
    from src.config import (
        REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET,
        REDDIT_USERNAME, REDDIT_PASSWORD
    )

    sanitized = error_message

    # Remove each credential value if present in the error message
    for cred_value in [REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD]:
        if cred_value and cred_value in sanitized:
            sanitized = sanitized.replace(cred_value, "***REDACTED***")

    # Also redact common Reddit API credential patterns
    # Reddit client_id pattern: 14-20 character alphanumeric string
    sanitized = re.sub(r'\b[a-zA-Z0-9]{14,20}\b', "***CLIENT_ID***", sanitized)

    return sanitized


# Usage in get_reddit_client():
try:
    _reddit_instance.user.me()
except Exception as e:
    sanitized_msg = sanitize_error_message(str(e))
    raise type(e)(
        f"Reddit authentication failed: {sanitized_msg}. "
        "Please verify your credentials in .env file."
    ) from e
```

### Anti-Patterns to Avoid

- **Creating multiple PRAW instances:** PRAW handles connection pooling internally; multiple instances waste resources and can trigger rate limits faster.
- **Hardcoding credentials:** Never commit credentials to git; always use environment variables.
- **Suppressing PRAW exceptions:** Let authentication failures propagate with context; don't catch and silently return None.
- **Using `read_only=True`:** We need moderation actions (approve, remove, ban), which require write access.
- **Storing PRAW instance in global mutable state:** Use the function-level singleton pattern shown above, not module-level initialization that fails on import.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Reddit API HTTP client | Custom requests to `oauth.reddit.com` | PRAW `praw.Reddit()` class | PRAW handles authentication headers, token refresh, rate limiting, pagination, error retry logic, and API changes |
| Credential validation | Manual checking of environment variables | Let PRAW constructor validate | PRAW provides specific error messages for missing/invalid credentials; combine with pre-flight checks for UX |
| Rate limit handling | Exponential backoff implementation | PRAW built-in rate limiting | PRAW tracks API rate limits automatically and waits before making requests that would exceed limits |
| Token refresh logic | Manual OAuth token refresh | PRAW automatic refresh | Script app auth uses username/password; PRAW handles token lifecycle internally |

**Key insight:** Reddit's API has complex rate limiting (60 requests/minute for OAuth apps, different for script apps), authentication that expires, and error responses that require parsing. PRAW has handled these edge cases for 13+ years across thousands of production deployments.

## Common Pitfalls

### Pitfall 1: Wrong Application Type in Reddit Preferences

**What goes wrong:** Authentication fails with `401 Unauthorized` or `invalid_grant` error even with correct credentials.

**Why it happens:** Reddit's app preferences page has three application types: "web app", "installed app" (OAuth), and "script". Script app requires username/password authentication; OAuth uses redirect flows. If you create the wrong type, credentials won't work.

**How to avoid:**
1. Go to https://www.reddit.com/prefs/apps
2. Click "create app" or "create another app"
3. Select "script" as the application type (at the bottom)
4. Fill in name and description (arbitrary)
5. Use `http://localhost:8080` or any placeholder for redirect uri (not used for script apps)
6. Copy the client_id (the string under the app name) and client_secret

**Warning signs:** Error messages mention "redirect uri" or "grant type" - indicates OAuth flow was attempted instead of script auth.

### Pitfall 2: Leaking Credentials in Error Messages or Logs

**What goes wrong:** Error messages, stack traces, or debug logs contain the actual credential values.

**Why it happens:** PRAW may include credential values in exception messages, especially for authentication failures. Python's default traceback printing includes function arguments.

**How to avoid:**
1. Use the `sanitize_error_message()` function shown in Pattern 2 above
2. Never log the `praw.Reddit()` constructor arguments
3. Never include PRAW exception messages directly in user-facing responses
4. Use Python's logging module with filters for production

**Warning signs:** Error responses contain 20-character alphanumeric strings (client_id format) or usernames in unexpected places.

### Pitfall 3: Confusion About `read_only` Mode

**What goes wrong:** `read_only=True` prevents moderation actions (approve, remove, ban).

**Why it happens:** PRAW defaults to `read_only=True` for safety, but Phase 3 needs write access for moderation actions.

**How to avoid:** Always explicitly pass `read_only=False` when creating the PRAW instance for this project.

**Warning signs:** `praw.exceptions.Forbidden` or "403 Forbidden" when trying to access modqueue or perform actions.

### Pitfall 4: Authentication Not Validated Until First API Call

**What goes wrong:** PRAW constructor succeeds even with invalid credentials; errors only appear on first API call.

**Why it happens:** PRAW uses lazy authentication - it doesn't validate credentials until you actually make an API request.

**How to avoid:** Make a lightweight validation call immediately after creating the instance, as shown in Pattern 1: `_reddit_instance.user.me()` fetches the authenticated user's profile.

**Warning signs:** Tests pass when they shouldn't because they create a PRAW instance without validating it works.

### Pitfall 5: User Agent Format

**What goes wrong:** Reddit API returns `403 Forbidden` or rate limits immediately.

**Why it happens:** Reddit requires user agent strings to follow the format: `<platform>:<app ID>:<version string> (by /u/<Reddit username>)`. Missing or malformed user agents trigger anti-bot protections.

**How to avoid:** Use the format shown in `.env.example`:
```
python:italia-career-mod:0.1.0 (by /u/your_username)
```

The existing `src/config.py` already constructs this correctly with:
```python
REDDIT_USER_AGENT = os.getenv(
    "REDDIT_USER_AGENT",
    f"italia-career-mod/{SERVER_VERSION} by {REDDIT_USERNAME or 'unknown'}"
)
```

**Warning signs:** `429 Too Many Requests` immediately on first API call, or `403 Forbidden` with "incorrect user agent" in response.

## Code Examples

Verified patterns from official sources:

### PRAW Client Initialization with Script Auth

```python
# Source: https://praw.readthedocs.io/en/stable/getting_started/quick_start.html
# Verified: PRAW 7.8.0 documentation

import praw

# Script app authentication (username/password)
reddit = praw.Reddit(
    client_id="CLIENT_ID",
    client_secret="CLIENT_SECRET",
    password="PASSWORD",
    user_agent="USERAGENT",
    username="USERNAME",
)

# Verify authentication
print(reddit.user.me())  # Prints authenticated user's username
```

### Environment Variable Loading (Already Implemented)

```python
# Source: Existing src/config.py in project (lines 35-42)
# Already implements required environment variable loading

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD")
REDDIT_USER_AGENT = os.getenv(
    "REDDIT_USER_AGENT",
    f"italia-career-mod/{SERVER_VERSION} by {REDDIT_USERNAME or 'unknown'}"
)
```

### Testing PRAW Client with Mocks

```python
# Source: pytest documentation with PRAW patterns
# Tests PRAW initialization without real API calls

import pytest
from unittest.mock import Mock, patch
from src.reddit_client import get_reddit_client

class TestRedditClientInitialization:
    """Test suite for REDI-01: PRAW client initialization."""

    @pytest.mark.anyio
    async def test_client_creates_with_valid_credentials(self):
        """REDI-01: Client initializes with environment variables."""
        # Mock environment variables
        mock_env = {
            "REDDIT_CLIENT_ID": "test_client_id",
            "REDDIT_CLIENT_SECRET": "test_secret",
            "REDDIT_USERNAME": "test_user",
            "REDDIT_PASSWORD": "test_password",
            "REDDIT_USER_AGENT": "test_agent"
        }

        with patch.dict("os.environ", mock_env):
            # Mock the PRAW constructor and validation call
            with patch("src.reddit_client.praw.Reddit") as mock_reddit_class:
                mock_instance = Mock()
                mock_instance.user.me.return_value = Mock(name="test_user")
                mock_reddit_class.return_value = mock_instance

                # First call should create client
                client = get_reddit_client()

                # Verify PRAW was called with correct parameters
                mock_reddit_class.assert_called_once_with(
                    client_id="test_client_id",
                    client_secret="test_secret",
                    username="test_user",
                    password="test_password",
                    user_agent="test_agent",
                    read_only=False,
                )

                # Verify authentication check was made
                mock_instance.user.me.assert_called_once()

    @pytest.mark.anyio
    async def test_missing_credentials_raise_value_error(self):
        """REDI-01: Missing credentials produce clear error messages."""
        # Mock missing client_id
        mock_env = {
            "REDDIT_CLIENT_SECRET": "test_secret",
            "REDDIT_USERNAME": "test_user",
            "REDDIT_PASSWORD": "test_password",
        }

        with patch.dict("os.environ", mock_env, clear=False):
            with pytest.raises(ValueError) as exc_info:
                get_reddit_client()

            # Verify error message mentions missing credential
            assert "REDDIT_CLIENT_ID" in str(exc_info.value)
            assert "Missing required Reddit credentials" in str(exc_info.value)

    @pytest.mark.anyio
    async def test_authentication_failure_sanitized(self):
        """REDI-02: Authentication errors don't expose credentials."""
        mock_env = {
            "REDDIT_CLIENT_ID": "bad_client_id",
            "REDDIT_CLIENT_SECRET": "bad_secret",
            "REDDIT_USERNAME": "bad_user",
            "REDDIT_PASSWORD": "bad_password",
            "REDDIT_USER_AGENT": "test_agent"
        }

        with patch.dict("os.environ", mock_env):
            with patch("src.reddit_client.praw.Reddit") as mock_reddit_class:
                mock_instance = Mock()
                # Simulate authentication failure
                mock_instance.user.me.side_effect = Exception(
                    "HTTPError 401: Unauthorized with bad_client_id"
                )
                mock_reddit_class.return_value = mock_instance

                with pytest.raises(Exception) as exc_info:
                    get_reddit_client()

                # Verify credential is redacted in error message
                error_msg = str(exc_info.value)
                assert "bad_client_id" not in error_msg
                assert "REDACTED" in error_msg or "***" in error_msg
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `praw.ini` configuration file | Environment variables + constructor parameters | PRAW 7.0+ (2020) | Container-friendly, no config file needed, easier Docker deployment |
| OAuth-only authentication | Script app auth for simple bots | Always available, but OAuth preferred for third-party apps | Script auth is simpler for personal bots, no redirect flow needed |
| Synchronous-only PRAW | Async support via `asyncpraw` package | PRAW 7.0+ | For Phase 2 scope, synchronous PRAW is sufficient; async adds complexity |

**Deprecated/outdated:**
- **`praw.ini` / `reddit.ini` files:** Still supported but not recommended for containerized apps. Use environment variables instead.
- **`praw.read_only = True` default:** For moderation bots, always use `read_only=False` explicitly.
- **Password authentication via URL parameters:** Security risk; always use constructor parameters.

## Open Questions

1. **Should we use `asyncpraw` for async PRAW operations?**
   - What we know: `asyncpraw` package provides async/await interface for PRAW.
   - What's unclear: Whether FastMCP tool execution benefits from async Reddit operations vs thread pool.
   - Recommendation: Use synchronous PRAW for Phase 2. FastMCP tools can be async functions that call synchronous PRAW in a thread pool executor. This adds complexity only if Phase 3 experiences performance issues.

2. **What timeout value should we use for PRAW API calls?**
   - What we know: REDI-04 requires timeout protection; PRAW has a `timeout_seconds` parameter.
   - What's unclear: Appropriate timeout value for modqueue operations (could be slow with large modqueues).
   - Recommendation: Default to 30 seconds for Phase 2, make configurable in Phase 3 when implementing actual API calls.

3. **Should we implement connection pooling health checks?**
   - What we know: PRAW manages connections internally; stale connections can cause failures.
   - What's unclear: Whether long-running MCP server needs periodic re-authentication or connection health checks.
   - Recommendation: Skip for Phase 2; Phase 3 will reveal if connection staleness is an issue during modqueue polling.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3.0 + pytest-anyio |
| Config file | pyproject.toml (already configured) |
| Quick run command | `pytest tests/test_reddit_client.py -v` |
| Full suite command | `pytest tests/ -v --cov=src` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REDI-01 | PRAW client initializes from environment variables | unit | `pytest tests/test_reddit_client.py::TestRedditClientInitialization::test_client_creates_with_valid_credentials -x` | ❌ Wave 0 |
| REDI-01 | Missing credentials raise ValueError | unit | `pytest tests/test_reddit_client.py::TestRedditClientInitialization::test_missing_credentials_raise_value_error -x` | ❌ Wave 0 |
| REDI-02 | Script app authentication (not OAuth) | unit | `pytest tests/test_reddit_client.py::TestRedditClientInitialization::test_script_auth_not_oauth -x` | ❌ Wave 0 |
| REDI-02 | Invalid credentials produce sanitized errors | unit | `pytest tests/test_reddit_client.py::TestRedditClientInitialization::test_authentication_failure_sanitized -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_reddit_client.py -v`
- **Per wave merge:** `pytest tests/ -v --cov=src/reddit_client.py`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_reddit_client.py` — covers REDI-01, REDI-02 with unit tests
- [ ] `tests/conftest.py` — add `mock_reddit_credentials()` fixture for test isolation
- [ ] `src/reddit_client.py` — PRAW client module (implementation in Wave 1)
- [ ] Framework install: `uv add "praw>=7.8.0"` — add PRAW dependency

## Sources

### Primary (HIGH confidence)
- **PRAW Documentation (verified 2024-2025):** https://praw.readthedocs.io/en/stable/getting_started/quick_start.html - Official PRAW quick start guide
- **PRAW Authentication:** https://praw.readthedocs.io/en/stable/getting_started/authentication.html - Script app authentication method
- **Reddit App Preferences:** https://www.reddit.com/prefs/apps - Where to create script applications
- **Existing project files:** `.env.example`, `src/config.py` - Environment variable infrastructure already in place

### Secondary (MEDIUM confidence)
- **PRAW GitHub Repository:** https://github.com/praw-dev/praw - Active development, latest releases
- **PRAW 7.0 Release Notes:** https://github.com/praw-dev/praw/releases - Environment variable support improvements

### Tertiary (LOW confidence)
- **Community tutorials:** (Various) - May contain outdated PRAW patterns; verify against official docs

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - PRAW is the de facto standard for Reddit API in Python, mature library with official documentation
- Architecture: HIGH - Singleton pattern and error handling patterns are well-established for PRAW usage
- Pitfalls: HIGH - All pitfalls documented are based on common PRAW issues documented in official docs and issue tracker

**Research date:** 2026-03-11
**Valid until:** 2026-04-11 (30 days - PRAW is stable, Reddit API changes infrequently)
