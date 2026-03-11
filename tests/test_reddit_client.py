"""
Test suite for Reddit Client (REDI) requirements.

This module contains tests for all REDI requirements as specified in
REQUIREMENTS.md. Tests are organized by requirement ID for traceability.

Test stubs created in Wave 0 (02-00-PLAN.md) - implementations in Wave 1 (02-01-PLAN.md).
"""

from unittest.mock import Mock, patch

import pytest


class TestRedditClientInitialization:
    """
    Test suite for REDI-01: Reddit Client Initialization.

    Verifies that the Reddit client initializes correctly from environment
    variables using PRAW (Python Reddit API Wrapper).
    """

    @pytest.mark.unit
    def test_client_initializes_from_env(self, mock_reddit_credentials, praw_mock):
        """
        REDI-01: Reddit client initializes from environment variables.

        Expected behavior (Wave 1):
        - Client reads REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET from environment
        - Client reads REDDIT_USERNAME, REDDIT_PASSWORD from environment
        - Client reads REDDIT_USER_AGENT from environment
        - PRAW Reddit instance is created successfully
        - Client is authenticated and ready to use

        Reference: REQUIREMENTS.md REDI-01
        """
        from src.reddit_client import get_reddit_client

        # First call should create and return client
        client = get_reddit_client()

        # Verify PRAW was called with correct parameters
        mock_reddit_class = praw_mock['class']
        assert mock_reddit_class.called
        call_kwargs = mock_reddit_class.call_args[1]
        assert call_kwargs['client_id'] == 'test_client_id'
        assert call_kwargs['client_secret'] == 'test_secret'
        assert call_kwargs['username'] == 'test_user'
        assert call_kwargs['password'] == 'test_password'
        assert call_kwargs['user_agent'] == 'test_agent'
        assert call_kwargs['read_only'] is False

        # Verify authentication was checked
        client.user.me.assert_called_once()

    @pytest.mark.unit
    def test_script_app_auth(self, mock_reddit_credentials, praw_mock):
        """
        REDI-01: Client uses script application type authentication.

        Expected behavior (Wave 1):
        - PRAW configured with script application type
        - Appropriate scopes for bot/moderator access
        - User agent string identifies the application
        - Authentication persists for session duration

        Reference: REQUIREMENTS.md REDI-01
        """
        from src.reddit_client import get_reddit_client

        get_reddit_client()

        # Verify script app auth (username/password provided)
        mock_reddit_class = praw_mock['class']
        call_kwargs = mock_reddit_class.call_args[1]
        assert 'username' in call_kwargs
        assert 'password' in call_kwargs
        # read_only=False enables write access for moderation
        assert call_kwargs['read_only'] is False

    @pytest.mark.unit
    def test_client_returns_singleton(self, mock_reddit_credentials, praw_mock):
        """
        REDI-01: Client implements lazy singleton pattern.

        Expected behavior (Wave 1):
        - First call creates PRAW instance
        - Second call returns same instance (identity check)
        - PRAW constructor called only once

        Reference: REQUIREMENTS.md REDI-01
        """
        from src.reddit_client import get_reddit_client

        # First call
        client1 = get_reddit_client()

        # Second call should return same instance
        client2 = get_reddit_client()

        # Verify same instance returned (identity check)
        assert client1 is client2

        # Verify PRAW constructor only called once
        mock_reddit_class = praw_mock['class']
        assert mock_reddit_class.call_count == 1


class TestRedditClientErrors:
    """
    Test suite for REDI-02: Reddit Client Error Handling.

    Verifies that the Reddit client handles errors safely without
    exposing sensitive credentials in error messages or logs.
    """

    @pytest.mark.unit
    def test_invalid_credentials_safe_error(self, mock_reddit_credentials):
        """
        REDI-02: Invalid credentials return safe error messages.

        Expected behavior (Wave 1):
        - Authentication failures return structured errors
        - Error messages do NOT contain actual credentials
        - Error codes indicate specific failure reason
        - Error types distinguish between auth, network, and API errors

        Reference: REQUIREMENTS.md REDI-02
        """
        # Mock PRAW to raise exception with credential in message
        mock_praw = Mock()
        mock_instance = Mock()
        # Simulate error that includes credential value
        mock_instance.user.me.side_effect = Exception("Invalid credentials for test_user")
        mock_praw.Reddit.return_value = mock_instance

        with patch('praw.Reddit', mock_praw.Reddit):
            from src.reddit_client import get_reddit_client

            # Should raise exception but sanitized
            with pytest.raises(Exception) as exc_info:
                get_reddit_client()

            # Error message should NOT contain the actual credential value
            error_msg = str(exc_info.value)
            assert 'test_secret' not in error_msg
            assert 'REDACTED' in error_msg or '***' in error_msg

    @pytest.mark.unit
    def test_error_message_no_credential_leak(self, mock_reddit_credentials):
        """
        REDI-02: Error handling prevents credential leakage.

        Expected behavior (Wave 1):
        - All exceptions caught and sanitized
        - Stack traces do not expose environment variables
        - Log entries do not contain secrets
        - Error responses are safe to display in UI

        Reference: REQUIREMENTS.md REDI-02
        """
        from src.reddit_client import sanitize_error_message

        # Create error message containing actual credentials
        error_msg = (
            "Authentication failed for user test_user "
            "with client_id test_client_id and secret test_secret"
        )

        sanitized = sanitize_error_message(error_msg)

        # Credential values should be removed/replaced
        assert 'test_secret' not in sanitized
        assert 'test_client_id' not in sanitized
        assert 'test_user' not in sanitized
        assert 'REDACTED' in sanitized or '***' in sanitized

    @pytest.mark.unit
    def test_missing_credentials_raise_value_error(self):
        """
        REDI-02: Missing credentials raise ValueError with clear message.

        Expected behavior (Wave 1):
        - Missing environment variables detected
        - Error message lists missing variable names
        - Error is actionable (tells user what to fix)

        Reference: REQUIREMENTS.md REDI-02
        """
        # Clear all Reddit credentials from environment
        import os

        reddit_vars = [
            'REDDIT_CLIENT_ID',
            'REDDIT_CLIENT_SECRET',
            'REDDIT_USERNAME',
            'REDDIT_PASSWORD',
        ]
        original_values = {var: os.getenv(var) for var in reddit_vars}

        # Delete environment variables
        for var in reddit_vars:
            if var in os.environ:
                del os.environ[var]

        try:
            from src.reddit_client import get_reddit_client

            # Should raise ValueError
            with pytest.raises(ValueError) as exc_info:
                get_reddit_client()

            # Error should list missing variables
            error_msg = str(exc_info.value)
            assert 'Missing' in error_msg or 'missing' in error_msg
            assert 'credentials' in error_msg
        finally:
            # Restore original values
            for var, val in original_values.items():
                if val is not None:
                    os.environ[var] = val
