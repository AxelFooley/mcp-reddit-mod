"""
Pytest configuration and shared fixtures for MCP server testing.

This module provides common fixtures and configuration for testing
the italia-career-mod MCP server implementation.
"""

import asyncio

import pytest

# Enable anyio for async test support
pytest_plugins = ["anyio"]


@pytest.fixture
def event_loop():
    """
    Create an event loop for async tests.

    This fixture ensures that each test gets its own event loop,
    preventing state leakage between tests.
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mcp_server_instance():
    """
    Fixture providing the MCP server instance for testing.

    This fixture will be implemented in Wave 1 (01-01-PLAN.md)
    once the FastMCP server is created.

    Yields:
        The FastMCP server instance configured for testing
    """
    # Wave 0 stub - implementation in 01-01
    pytest.skip("Wave 0 stub - server implementation in 01-01-PLAN.md")


@pytest.fixture
async def mcp_client():
    """
    Fixture providing an async MCP client for testing.

    This fixture will be implemented in Wave 1 (01-01-PLAN.md)
    once the FastMCP server transport is configured.

    Yields:
        An async client capable of making MCP protocol requests
    """
    # Wave 0 stub - implementation in 01-01
    pytest.skip("Wave 0 stub - client implementation in 01-01-PLAN.md")


@pytest.fixture
def sample_reddit_config():
    """
    Fixture providing sample Reddit configuration for testing.

    Returns:
        dict: Sample Reddit API credentials and configuration
    """
    return {
        "client_id": "test_client_id",
        "client_secret": "test_client_secret",
        "username": "test_user",
        "password": "test_password",
        "user_agent": "italia-career-mod/0.1.0 by test_user"
    }


@pytest.fixture
def mock_reddit_credentials(monkeypatch):
    """
    Mock Reddit credentials for testing (REDI-01, REDI-02).

    This fixture sets up test environment variables for Reddit API
    credentials, allowing tests to run without exposing real credentials.
    It also patches both config and reddit_client modules to ensure
    values are available regardless of import order.

    Args:
        monkeypatch: Pytest monkeypatch fixture for environment modification

    Returns:
        dict: Dictionary of mock environment variables
    """
    mock_env = {
        "REDDIT_CLIENT_ID": "test_client_id",
        "REDDIT_CLIENT_SECRET": "test_secret",
        "REDDIT_USERNAME": "test_user",
        "REDDIT_PASSWORD": "test_password",
        "REDDIT_USER_AGENT": "test_agent",
    }
    # Set environment variables
    for key, value in mock_env.items():
        monkeypatch.setenv(key, value)

    # Patch config module
    try:
        import src.config
        monkeypatch.setattr(src.config, "REDDIT_CLIENT_ID", "test_client_id")
        monkeypatch.setattr(src.config, "REDDIT_CLIENT_SECRET", "test_secret")
        monkeypatch.setattr(src.config, "REDDIT_USERNAME", "test_user")
        monkeypatch.setattr(src.config, "REDDIT_PASSWORD", "test_password")
        monkeypatch.setattr(src.config, "REDDIT_USER_AGENT", "test_agent")
    except ImportError:
        pass  # Config module not imported yet

    # Also patch reddit_client module directly (it imports these from config)
    try:
        import src.reddit_client
        monkeypatch.setattr(src.reddit_client, "REDDIT_CLIENT_ID", "test_client_id")
        monkeypatch.setattr(src.reddit_client, "REDDIT_CLIENT_SECRET", "test_secret")
        monkeypatch.setattr(src.reddit_client, "REDDIT_USERNAME", "test_user")
        monkeypatch.setattr(src.reddit_client, "REDDIT_PASSWORD", "test_password")
        monkeypatch.setattr(src.reddit_client, "REDDIT_USER_AGENT", "test_agent")
    except (ImportError, AttributeError):
        pass  # Reddit_client module not imported yet

    return mock_env


@pytest.fixture
def praw_mock(monkeypatch):
    """
    Mock PRAW Reddit class for testing.

    This fixture patches the praw.Reddit class to return a mock instance,
    allowing tests to verify Reddit client behavior without making actual API calls.

    Args:
        monkeypatch: Pytest monkeypatch fixture for patching

    Yields:
        Mock: Mocked PRAW Reddit instance
    """
    from unittest.mock import Mock
    mock_instance = Mock()
    mock_instance.user.me.return_value = Mock(name="test_user")
    mock_reddit_class = Mock(return_value=mock_instance)
    with monkeypatch.context() as m:
        m.setattr("praw.Reddit", mock_reddit_class)
        yield {"instance": mock_instance, "class": mock_reddit_class}


@pytest.fixture(autouse=True)
def reset_reddit_client_singleton():
    """
    Reset the Reddit client singleton between tests.

    This fixture ensures that each test gets a fresh Reddit client instance
    by resetting the module-level _reddit_instance variable before each test.

    Note: Does NOT reload config module as that would interfere with
    mock_reddit_credentials fixture patching.

    Auto-use ensures this runs for every test without explicit request.
    """
    # Reset before test (if module exists)
    try:
        import src.reddit_client
        src.reddit_client._reddit_instance = None
    except (ImportError, AttributeError):
        pass  # Module doesn't exist yet or no _reddit_instance

    yield

    # Reset after test (if module exists)
    try:
        import src.reddit_client
        src.reddit_client._reddit_instance = None
    except (ImportError, AttributeError):
        pass  # Module doesn't exist yet or no _reddit_instance


@pytest.fixture
def mock_subreddit_mod(monkeypatch):
    """
    Mock PRAW subreddit moderation API for testing.

    This fixture provides a mock object that simulates PRAW's subreddit.modqueue()
    method for testing modqueue retrieval functionality (MODT-01).

    Args:
        monkeypatch: Pytest monkeypatch fixture for patching

    Yields:
        Mock: Mocked subreddit object with modqueue() method
    """
    from unittest.mock import Mock

    mock_subreddit = Mock()
    # Mock modqueue() to return empty list by default
    mock_subreddit.modqueue.return_value = []
    # Mock the limit parameter handling
    mock_subreddit.modqueue.__name__ = "modqueue"

    with monkeypatch.context() as m:
        # Patch the subreddit object that would be returned by reddit.subreddit()
        m.setattr("praw.models.Subreddit", Mock(return_value=mock_subreddit))
        yield mock_subreddit


@pytest.fixture
def mock_comment_mod(monkeypatch):
    """
    Mock PRAW comment moderation API for testing.

    This fixture provides a mock object that simulates PRAW's comment.mod.approve()
    and comment.mod.remove() methods for testing content approval and removal (MODT-02, MODT-03).

    Args:
        monkeypatch: Pytest monkeypatch fixture for patching

    Yields:
        Mock: Mocked comment object with mod attribute having approve/remove methods
    """
    from unittest.mock import Mock

    mock_comment = Mock()
    # Create mock.mod interface
    mock_mod = Mock()
    mock_mod.approve.return_value = None  # Void method
    mock_mod.remove.return_value = None  # Void method
    mock_comment.mod = mock_mod

    with monkeypatch.context() as m:
        # Patch the Comment model
        m.setattr("praw.models.Comment", Mock(return_value=mock_comment))
        yield mock_comment


@pytest.fixture
def mock_submission_mod(monkeypatch):
    """
    Mock PRAW submission moderation API for testing.

    This fixture provides a mock object that simulates PRAW's submission.mod.approve()
    and submission.mod.remove() methods for testing content approval and removal (MODT-02, MODT-03).

    Args:
        monkeypatch: Pytest monkeypatch fixture for patching

    Yields:
        Mock: Mocked submission object with mod attribute having approve/remove methods
    """
    from unittest.mock import Mock

    mock_submission = Mock()
    # Create mock.mod interface (same as comment)
    mock_mod = Mock()
    mock_mod.approve.return_value = None  # Void method
    mock_mod.remove.return_value = None  # Void method
    mock_submission.mod = mock_mod

    with monkeypatch.context() as m:
        # Patch the Submission model
        m.setattr("praw.models.Submission", Mock(return_value=mock_submission))
        yield mock_submission


@pytest.fixture
def mock_redditor(monkeypatch):
    """
    Mock PRAW redditor API for testing.

    This fixture provides a mock object that simulates PRAW's redditor.submissions.new()
    and redditor.comments.new() methods for testing user history fetching (MODT-05).

    Args:
        monkeypatch: Pytest monkeypatch fixture for patching

    Yields:
        Mock: Mocked redditor object with submissions and comments attributes
    """
    from unittest.mock import Mock

    mock_redditor_instance = Mock()
    # Mock submissions.new() to return empty list by default
    mock_submissions = Mock()
    mock_submissions.new.return_value = []
    mock_redditor_instance.submissions = mock_submissions

    # Mock comments.new() to return empty list by default
    mock_comments = Mock()
    mock_comments.new.return_value = []
    mock_redditor_instance.comments = mock_comments

    with monkeypatch.context() as m:
        # Patch the Redditor model
        m.setattr("praw.models.Redditor", Mock(return_value=mock_redditor_instance))
        yield mock_redditor_instance


# Test configuration markers
def pytest_configure(config):
    """
    Configure pytest with custom markers.

    This function sets up custom markers that can be used
    to categorize tests (e.g., slow, integration, etc.).
    """
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
