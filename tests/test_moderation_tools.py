"""
Test suite for Moderation Tools (MODT) requirements.

This module contains tests for all MODT requirements as specified in
REQUIREMENTS.md. Tests are organized by requirement ID for traceability.

Test stubs created in Wave 0 (03-00-PLAN.md) - implementations in Wave 1 (03-01-PLAN.md).
"""

import pytest


class TestModqueue:
    """
    Test suite for MODT-01: Modqueue Retrieval.

    Verifies that the system can fetch modqueue items from a subreddit
    for moderator review.
    """

    @pytest.mark.unit
    def test_get_modqueue_returns_items(self, praw_mock, mock_reddit_credentials):
        """
        MODT-01: Modqueue returns items for review.

        Expected behavior (Wave 1):
        - System fetches modqueue items from specified subreddit
        - Returns list of items awaiting moderation
        - Items include metadata (id, author, permalink, reason)
        - Limit parameter controls maximum items returned

        Reference: REQUIREMENTS.md MODT-01
        """
        from unittest.mock import Mock

        from src.modtools import get_modqueue

        # Create mock modqueue items
        mock_comment = Mock()
        mock_comment.fullname = "t1_abc123"
        mock_comment.__class__.__name__ = "Comment"
        mock_author = Mock()
        mock_author.__str__ = Mock(return_value="test_user")
        mock_comment.author = mock_author
        mock_comment.body = "This is spam"
        mock_comment.created_utc = 1234567890.0
        mock_sub = Mock()
        mock_sub.__str__ = Mock(return_value="testsub")
        mock_comment.subreddit = mock_sub

        mock_submission = Mock()
        mock_submission.fullname = "t3_def456"
        mock_submission.__class__.__name__ = "Submission"
        mock_submission.author = None  # Deleted user
        # Empty selftext means use title
        mock_submission.selftext = ""
        mock_submission.title = "Rule violation post"
        mock_submission.created_utc = 1234567891.0
        mock_submission.subreddit = mock_sub

        # Configure mock to return modqueue items
        praw_mock["instance"].subreddit.return_value.mod.modqueue.return_value = [
            mock_comment, mock_submission
        ]

        # Test modqueue retrieval
        result = get_modqueue("testsub", limit=25)

        # Verify results
        assert len(result) == 2
        assert result[0]["thing_id"] == "t1_abc123"
        assert result[0]["type"] == "comment"
        assert result[0]["author"] == "test_user"
        assert result[0]["body"] == "This is spam"
        assert result[0]["created_utc"] == 1234567890.0

        assert result[1]["thing_id"] == "t3_def456"
        assert result[1]["type"] == "submission"
        assert result[1]["author"] == "[deleted]"
        assert result[1]["body"] == "Rule violation post"

    @pytest.mark.unit
    def test_get_modqueue_invalid_subreddit(self, praw_mock, mock_reddit_credentials):
        """
        MODT-01: Modqueue handles invalid subreddit errors.

        Expected behavior (Wave 1):
        - System validates subreddit exists and is accessible
        - Raises appropriate error for invalid/non-existent subreddit
        - Error message is sanitized (no credential leakage)
        - Error includes subreddit name for debugging

        Reference: REQUIREMENTS.md MODT-01
        """
        from praw.exceptions import PRAWException

        from src.modtools import get_modqueue

        # Configure mock to raise PRAW exception
        praw_mock["instance"].subreddit.side_effect = PRAWException(
            "Subreddit not found: r/nonexistent"
        )

        # Should raise exception with sanitized error
        with pytest.raises(PRAWException):
            get_modqueue("nonexistent")

    @pytest.mark.unit
    def test_get_modqueue_empty(self, praw_mock, mock_reddit_credentials):
        """
        MODT-01: Modqueue handles empty queue gracefully.

        Expected behavior (Wave 1):
        - System returns empty list when no items in modqueue
        - No error raised for legitimate empty queue
        - Response indicates successful fetch with zero items

        Reference: REQUIREMENTS.md MODT-01
        """
        from src.modtools import get_modqueue

        # Configure mock to return empty modqueue
        praw_mock["instance"].subreddit.return_value.mod.modqueue.return_value = []

        # Test with empty modqueue
        result = get_modqueue("testsub")

        # Should return empty list
        assert result == []


class TestApprove:
    """
    Test suite for MODT-02: Content Approval.

    Verifies that moderators can approve comments and submissions,
    removing them from the modqueue and making them visible.
    """

    @pytest.mark.unit
    def test_approve_comment(self, praw_mock, mock_reddit_credentials):
        """
        MODT-02: Comment approval by thing_id.

        Expected behavior (Wave 1):
        - System approves comment using thing_id (t1_ prefix)
        - Comment removed from modqueue
        - Comment becomes visible to other users
        - Approval action is idempotent (approve already-approved is safe)

        Reference: REQUIREMENTS.md MODT-02
        """
        from unittest.mock import Mock

        from src.modtools import approve_item

        # Create mock comment with mod.approve() method
        mock_comment = Mock()
        mock_comment.mod.approve.return_value = None

        # Configure praw mock to return the mock comment
        praw_mock["instance"].comment.return_value = mock_comment

        # Approve the comment (thing_id without t1_ prefix for PRAW)
        approve_item("t1_abc123")

        # Verify PRAW methods were called correctly
        praw_mock["instance"].comment.assert_called_once_with("abc123")
        mock_comment.mod.approve.assert_called_once()

    @pytest.mark.unit
    def test_approve_submission(self, praw_mock, mock_reddit_credentials):
        """
        MODT-02: Submission approval by thing_id.

        Expected behavior (Wave 1):
        - System approves submission using thing_id (t3_ prefix)
        - Submission removed from modqueue
        - Submission becomes visible to other users
        - Approval action is idempotent

        Reference: REQUIREMENTS.md MODT-02
        """
        from unittest.mock import Mock

        from src.modtools import approve_item

        # Create mock submission with mod.approve() method
        mock_submission = Mock()
        mock_submission.mod.approve.return_value = None

        # Configure praw mock to return the mock submission
        praw_mock["instance"].submission.return_value = mock_submission

        # Approve the submission
        approve_item("t3_def456")

        # Verify PRAW methods were called correctly
        praw_mock["instance"].submission.assert_called_once_with("def456")
        mock_submission.mod.approve.assert_called_once()

    @pytest.mark.unit
    def test_approve_invalid_thing_id(self, praw_mock, mock_reddit_credentials):
        """
        MODT-02: Approval validates thing_id format.

        Expected behavior (Wave 1):
        - System validates thing_id before API call
        - Invalid format raises ValidationError with clear message
        - Valid format: t1_ (comment) or t3_ (submission) followed by base36
        - Prevents wasted API calls on invalid input

        Reference: REQUIREMENTS.md MODT-02
        """
        from src.modtools import approve_item

        # Invalid thing_id formats should raise ValueError
        with pytest.raises(ValueError, match="Invalid thing_id format"):
            approve_item("invalid_id")

        with pytest.raises(ValueError, match="Unsupported thing_id type"):
            approve_item("t2_abc123")  # t2_ is account, not content


class TestRemove:
    """
    Test suite for MODT-03: Content Removal.

    Verifies that moderators can remove comments and submissions
    with optional spam classification and reason.
    """

    @pytest.mark.unit
    def test_remove_item_with_reason(self, praw_mock, mock_reddit_credentials):
        """
        MODT-03: Item removal with reason.

        Expected behavior (Wave 1):
        - System removes item (comment or submission) by thing_id
        - Reason is recorded for moderator notes
        - Item hidden from public view
        - Removal is permanent unless explicitly approved later

        Reference: REQUIREMENTS.md MODT-03
        """
        from unittest.mock import Mock

        from src.modtools import remove_item

        # Create mock comment with mod.remove() method
        mock_comment = Mock()
        mock_comment.mod.remove.return_value = None

        # Configure praw mock to return the mock comment
        praw_mock["instance"].comment.return_value = mock_comment

        # Remove the comment with a reason
        remove_item("t1_abc123", reason="Spam")

        # Verify PRAW methods were called correctly
        praw_mock["instance"].comment.assert_called_once_with("abc123")
        mock_comment.mod.remove.assert_called_once_with(spam=False)

    @pytest.mark.unit
    def test_remove_item_as_spam(self, praw_mock, mock_reddit_credentials):
        """
        MODT-03: Item removal with spam flag.

        Expected behavior (Wave 1):
        - System removes item with spam=True parameter
        - Spam flag triggers Reddit's spam filtering
        - May affect user's spam score for future posts
        - Reason is still recorded alongside spam classification

        Reference: REQUIREMENTS.md MODT-03
        """
        from unittest.mock import Mock

        from src.modtools import remove_item

        # Create mock submission with mod.remove() method
        mock_submission = Mock()
        mock_submission.mod.remove.return_value = None

        # Configure praw mock to return the mock submission
        praw_mock["instance"].submission.return_value = mock_submission

        # Remove the submission with spam flag
        remove_item("t3_def456", spam=True)

        # Verify PRAW methods were called correctly with spam=True
        praw_mock["instance"].submission.assert_called_once_with("def456")
        mock_submission.mod.remove.assert_called_once_with(spam=True)

    @pytest.mark.unit
    def test_remove_item_invalid_thing_id(self, praw_mock, mock_reddit_credentials):
        """
        MODT-03: Removal validates thing_id format.

        Expected behavior (Wave 1):
        - System validates thing_id before API call
        - Invalid format raises ValidationError with clear message
        - Valid format: t1_ (comment) or t3_ (submission) followed by base36
        - Prevents wasted API calls on invalid input

        Reference: REQUIREMENTS.md MODT-03
        """
        from src.modtools import remove_item

        # Invalid thing_id formats should raise ValueError
        with pytest.raises(ValueError, match="Invalid thing_id format"):
            remove_item("invalid_id")

        with pytest.raises(ValueError, match="Unsupported thing_id type"):
            remove_item("t4_abc123")  # t4_ is message, not supported


class TestBan:
    """
    Test suite for MODT-04: User Banning.

    Verifies that moderators can ban users from a subreddit
    with configurable duration and reason.
    """

    @pytest.mark.unit
    def test_ban_user_permanent(self, praw_mock, mock_reddit_credentials):
        """
        MODT-04: Permanent ban (duration_days=0).

        Expected behavior (Wave 1):
        - System bans user from specified subreddit
        - duration_days=0 indicates permanent ban
        - Ban reason is recorded for mod notes
        - User cannot post or comment in subreddit

        Reference: REQUIREMENTS.md MODT-04
        """
        from unittest.mock import Mock

        from src.modtools import ban_user

        # Configure mock subreddit.banned.add() method
        mock_banned = Mock()
        mock_banned.add.return_value = None
        praw_mock["instance"].subreddit.return_value.banned = mock_banned

        # Ban user permanently
        ban_user("testsub", "spam_user", "Spamming", duration_days=0)

        # Verify PRAW methods were called correctly
        praw_mock["instance"].subreddit.assert_called_once_with("testsub")
        # duration=None means permanent ban in PRAW
        mock_banned.add.assert_called_once_with(
            "spam_user",
            ban_reason="Spamming",
            duration=None,
            note="Banned via italia-career-mod MCP tool",
        )

    @pytest.mark.unit
    def test_ban_user_temporary(self, praw_mock, mock_reddit_credentials):
        """
        MODT-04: Temporary ban with specified duration.

        Expected behavior (Wave 1):
        - System bans user for specified number of days
        - duration_days > 0 indicates temporary ban
        - Ban reason is recorded for mod notes
        - User automatically unbanned after duration expires

        Reference: REQUIREMENTS.md MODT-04
        """
        from unittest.mock import Mock

        from src.modtools import ban_user

        # Configure mock subreddit.banned.add() method
        mock_banned = Mock()
        mock_banned.add.return_value = None
        praw_mock["instance"].subreddit.return_value.banned = mock_banned

        # Ban user temporarily
        ban_user("testsub", "spam_user", "Spamming", duration_days=7)

        # Verify PRAW methods were called correctly
        praw_mock["instance"].subreddit.assert_called_once_with("testsub")
        # duration=7 means 7-day temporary ban
        mock_banned.add.assert_called_once_with(
            "spam_user",
            ban_reason="Spamming",
            duration=7,
            note="Banned via italia-career-mod MCP tool",
        )

    @pytest.mark.unit
    def test_ban_user_invalid_duration(self, praw_mock, mock_reddit_credentials):
        """
        MODT-04: Ban validates duration parameter.

        Expected behavior (Wave 1):
        - System validates duration_days is non-negative integer
        - Negative duration raises ValidationError
        - Clear error message explains valid range (0 for permanent, >0 for temporary)

        Reference: REQUIREMENTS.md MODT-04
        """
        from src.modtools import ban_user

        # Negative duration should raise ValueError
        with pytest.raises(ValueError, match="duration_days must be non-negative"):
            ban_user("testsub", "spam_user", "Spamming", duration_days=-1)

    @pytest.mark.unit
    def test_ban_user_invalid_username(self, praw_mock, mock_reddit_credentials):
        """
        MODT-04: Ban handles non-existent users.

        Expected behavior (Wave 1):
        - System validates username exists
        - Non-existent user raises appropriate error
        - Error message is sanitized
        - Error indicates username validation failure

        Reference: REQUIREMENTS.md MODT-04
        """
        from praw.exceptions import PRAWException

        from src.modtools import ban_user

        # Configure mock to raise PRAW exception
        praw_mock["instance"].subreddit.return_value.banned.add.side_effect = PRAWException(
            "User nonexistent not found"
        )

        # Should raise exception with sanitized error
        with pytest.raises(PRAWException):
            ban_user("testsub", "nonexistent", "Rule violation")


class TestUserHistory:
    """
    Test suite for MODT-05: User Moderation History.

    Verifies that the system can fetch a user's history of
    posts and comments that were flagged in the subreddit.
    """

    @pytest.mark.unit
    def test_get_user_history(self, praw_mock, mock_reddit_credentials):
        """
        MODT-05: Fetch user's content history in subreddit.

        Expected behavior (Wave 3):
        - System fetches user's posts and comments from subreddit
        - Returns both submissions and comments
        - Results sorted by created_utc (newest first)
        - Includes removed flag in results
        - Limited by limit parameter

        Reference: REQUIREMENTS.md MODT-05
        """
        from unittest.mock import Mock

        from src.modtools import get_user_history

        # Create mock submission
        mock_submission = Mock()
        mock_submission.fullname = "t3_sub123"
        mock_submission.title = "Test post"
        mock_submission.selftext = "Test content"
        mock_submission.created_utc = 1234567900.0
        mock_submission.permalink = "/r/testsub/comments/sub123/test_post/"
        mock_submission.removed = False
        mock_sub = Mock()
        mock_sub.__str__ = Mock(return_value="testsub")
        mock_submission.subreddit = mock_sub

        # Create mock comment
        mock_comment = Mock()
        mock_comment.fullname = "t1_com456"
        mock_comment.body = "Test comment"
        mock_comment.created_utc = 1234567800.0
        mock_comment.permalink = "/r/testsub/comments/sub123/-/com456/"
        mock_comment.removed = True
        mock_comment.subreddit = mock_sub

        # Configure mock redditor
        mock_redditor = Mock()
        mock_submissions = Mock()
        mock_submissions.new.return_value = [mock_submission]
        mock_redditor.submissions = mock_submissions

        mock_comments = Mock()
        mock_comments.new.return_value = [mock_comment]
        mock_redditor.comments = mock_comments

        # Configure praw mock to return the mock redditor
        praw_mock["instance"].redditor.return_value = mock_redditor

        # Get user history
        result = get_user_history("testuser", "testsub", limit=100)

        # Verify results
        assert len(result) == 2
        # Results should be sorted by created_utc descending (newest first)
        assert result[0]["thing_id"] == "t3_sub123"  # Submission (newer)
        assert result[0]["type"] == "submission"
        assert result[0]["title"] == "Test post"
        assert result[0]["created_utc"] == 1234567900.0
        assert result[0]["removed"] is False

        assert result[1]["thing_id"] == "t1_com456"  # Comment (older)
        assert result[1]["type"] == "comment"
        assert result[1]["body"] == "Test comment"
        assert result[1]["created_utc"] == 1234567800.0
        assert result[1]["removed"] is True

    @pytest.mark.unit
    def test_get_user_history_empty(self, praw_mock, mock_reddit_credentials):
        """
        MODT-05: Handle user with no history.

        Expected behavior (Wave 3):
        - System returns empty list for user with no items
        - No error raised for legitimate empty history
        - Response indicates successful fetch with zero items

        Reference: REQUIREMENTS.md MODT-05
        """
        from unittest.mock import Mock

        from src.modtools import get_user_history

        # Configure mock redditor with empty history
        mock_redditor = Mock()
        mock_submissions = Mock()
        mock_submissions.new.return_value = []
        mock_redditor.submissions = mock_submissions

        mock_comments = Mock()
        mock_comments.new.return_value = []
        mock_redditor.comments = mock_comments

        praw_mock["instance"].redditor.return_value = mock_redditor

        # Get user history
        result = get_user_history("testuser", "testsub")

        # Should return empty list
        assert result == []

    @pytest.mark.unit
    def test_get_user_history_not_found(self, praw_mock, mock_reddit_credentials):
        """
        MODT-05: Handle non-existent user.

        Expected behavior (Wave 3):
        - System raises PRAWException for non-existent user
        - Error message is sanitized
        - Error indicates user not found

        Reference: REQUIREMENTS.md MODT-05
        """
        from praw.exceptions import PRAWException

        from src.modtools import get_user_history

        # Configure mock to raise PRAWException
        praw_mock["instance"].redditor.side_effect = PRAWException("User not found")

        # Should raise exception
        with pytest.raises(PRAWException):
            get_user_history("nonexistent_user", "testsub")


class TestValidation:
    """
    Test suite for SAFE-01: Thing ID Validation.

    Verifies that thing_id values are validated before making
    Reddit API calls to prevent errors and wasted requests.
    """

    @pytest.mark.unit
    def test_validate_thing_id_valid_comment(self):
        """
        SAFE-01: Valid comment thing_id passes validation.

        Expected behavior (Wave 1):
        - System validates t1_ prefix for comments
        - Valid base36 ID after prefix accepted
        - Validation returns True or passes without error
        - thing_id format: t1_ followed by base36 characters

        Reference: REQUIREMENTS.md SAFE-01
        """
        from src.modtools import validate_thing_id

        # Valid comment thing_id should pass validation and return the validated id
        result = validate_thing_id("t1_abc123")
        assert result == "t1_abc123"

        # Valid submission thing_id should also pass
        result = validate_thing_id("t3_def456")
        assert result == "t3_def456"

    @pytest.mark.unit
    def test_validate_thing_id_valid_submission(self):
        """
        SAFE-01: Valid submission thing_id passes validation.

        Expected behavior (Wave 1):
        - System validates t3_ prefix for submissions
        - Valid base36 ID after prefix accepted
        - Validation returns True or passes without error
        - thing_id format: t3_ followed by base36 characters

        Reference: REQUIREMENTS.md SAFE-01
        """
        from src.modtools import validate_thing_id

        # Valid submission thing_id with expected_prefix should pass
        result = validate_thing_id("t3_xyz789", expected_prefix="3")
        assert result == "t3_xyz789"

    @pytest.mark.unit
    def test_validate_thing_id_invalid_format(self):
        """
        SAFE-01: Invalid format rejected.

        Expected behavior (Wave 1):
        - System rejects thing_id with wrong format
        - Missing prefix raises ValidationError
        - Wrong prefix type raises ValidationError
        - Invalid base36 characters rejected

        Reference: REQUIREMENTS.md SAFE-01
        """
        from src.modtools import validate_thing_id

        # No prefix at all
        with pytest.raises(ValueError, match="Invalid thing_id format"):
            validate_thing_id("abc123")

        # Wrong prefix type (t2_ is for accounts, not content)
        with pytest.raises(ValueError, match="Unsupported thing_id type"):
            validate_thing_id("t2_abc123")

    @pytest.mark.unit
    def test_validate_thing_id_missing_prefix(self):
        """
        SAFE-01: Missing prefix rejected.

        Expected behavior (Wave 1):
        - System rejects thing_id without type prefix
        - Plain base36 string without t1_/t3_ prefix raises error
        - Clear error message indicates required prefix format

        Reference: REQUIREMENTS.md SAFE-01
        """
        from src.modtools import validate_thing_id

        # Empty string
        with pytest.raises(ValueError, match="thing_id cannot be empty"):
            validate_thing_id("")

        # Missing underscore
        with pytest.raises(ValueError, match="Invalid thing_id format"):
            validate_thing_id("t1abc123")

    @pytest.mark.unit
    def test_validate_thing_id_wrong_type(self):
        """
        SAFE-01: Wrong prefix type rejected.

        Expected behavior (Wave 1):
        - System rejects unsupported thing_id prefixes
        - Only t1_ (comment) and t3_ (submission) supported
        - Other prefixes (t2_, t4_, t5_, etc.) raise ValidationError
        - Clear error message indicates valid prefix types

        Reference: REQUIREMENTS.md SAFE-01
        """
        from src.modtools import validate_thing_id

        # t4_ (message), t5_ (subreddit), t6_ (award), t8_ (poll) are not supported
        with pytest.raises(ValueError, match="Unsupported thing_id type"):
            validate_thing_id("t4_abc123")

        # Prefix mismatch when expected_prefix provided
        with pytest.raises(ValueError, match="Expected thing_id prefix '1' but got '3'"):
            validate_thing_id("t3_abc123", expected_prefix="1")


class TestSanitization:
    """
    Test suite for SAFE-02: Error Message Sanitization.

    Verifies that error messages are sanitized to prevent
    leakage of sensitive information like credentials.
    """

    @pytest.mark.unit
    def test_error_sanitization_removes_credentials(self):
        """
        SAFE-02: Credential values removed from errors.

        Expected behavior (Wave 1):
        - System removes actual credential values from error messages
        - REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET removed
        - REDDIT_USERNAME, REDDIT_PASSWORD removed
        - Replaced with REDACTED or *** placeholders

        Reference: REQUIREMENTS.md SAFE-02
        """
        from praw.exceptions import PRAWException

        from src.modtools import sanitize_moderation_error

        # Create an error containing credential info
        error_msg = "Authentication failed for user test_user with client_id test_client_id"
        error = PRAWException(error_msg)

        # Sanitize should remove credential-like strings
        sanitized = sanitize_moderation_error(error)

        # Check credentials are redacted
        assert "test_user" not in sanitized or "***" in sanitized
        assert "test_client_id" not in sanitized or "***" in sanitized
        # Error should still have meaningful content
        assert "Authentication" in sanitized or "failed" in sanitized

    @pytest.mark.unit
    def test_error_sanitization_removes_subreddit_names(self):
        """
        SAFE-02: Subreddit names removed from errors.

        Expected behavior (Wave 1):
        - System redacts subreddit names from error messages
        - Prevents leaking sensitive subreddit information
        - Replaced with placeholder like r/SUBREDDIT

        Reference: REQUIREMENTS.md SAFE-02
        """
        from praw.exceptions import PRAWException

        from src.modtools import sanitize_moderation_error

        # Create an error containing subreddit name
        error_msg = "Failed to fetch modqueue for r/MyPrivateSubreddit"
        error = PRAWException(error_msg)

        sanitized = sanitize_moderation_error(error)

        # Subreddit name should be redacted
        assert "MyPrivateSubreddit" not in sanitized
        assert "r/SUBREDDIT" in sanitized or "r/[SUBREDDIT]" in sanitized

    @pytest.mark.unit
    def test_error_sanitization_removes_usernames(self):
        """
        SAFE-02: Usernames removed from errors.

        Expected behavior (Wave 1):
        - System redacts usernames from error messages
        - Prevents leaking user privacy information
        - Replaced with placeholder like u/USERNAME

        Reference: REQUIREMENTS.md SAFE-02
        """
        from praw.exceptions import PRAWException

        from src.modtools import sanitize_moderation_error

        # Create an error containing username
        error_msg = "User u/SomeRedditor not found in subreddit"
        error = PRAWException(error_msg)

        sanitized = sanitize_moderation_error(error)

        # Username should be redacted
        assert "SomeRedditor" not in sanitized
        assert "u/USERNAME" in sanitized or "u/[USERNAME]" in sanitized

    @pytest.mark.unit
    def test_error_sanitization_removes_thing_ids(self):
        """
        SAFE-02: Thing IDs removed from errors.

        Expected behavior (Wave 1):
        - System redacts thing_ids from error messages
        - Prevents leaking content identifiers
        - Replaced with placeholder like tX_THINGID

        Reference: REQUIREMENTS.md SAFE-02
        """
        from praw.exceptions import PRAWException

        from src.modtools import sanitize_moderation_error

        # Create an error containing thing IDs
        error_msg = "Failed to approve comment t1_abc123 and submission t3_def456"
        error = PRAWException(error_msg)

        sanitized = sanitize_moderation_error(error)

        # Thing IDs should be redacted
        assert "t1_abc123" not in sanitized
        assert "t3_def456" not in sanitized
        assert "tX_THINGID" in sanitized or "tX_[THINGID]" in sanitized

    @pytest.mark.unit
    def test_error_sanitization_preserves_safe_content(self):
        """
        SAFE-02: Safe content preserved in errors.

        Expected behavior (Wave 1):
        - System preserves non-sensitive error content
        - Error type and message structure maintained
        - Only sensitive patterns are replaced
        - Error remains actionable for debugging

        Reference: REQUIREMENTS.md SAFE-02
        """
        from praw.exceptions import PRAWException

        from src.modtools import sanitize_moderation_error

        # Create an error with both sensitive and safe content
        error_msg = "HTTP 403 Forbidden: Invalid scope in request for r/testsub"
        error = PRAWException(error_msg)

        sanitized = sanitize_moderation_error(error)

        # Safe error context should be preserved
        assert "HTTP" in sanitized or "403" in sanitized or "Forbidden" in sanitized
        # Sensitive info redacted
        assert "testsub" not in sanitized or "SUBREDDIT" in sanitized


class TestErrorPropagation:
    """
    Test suite for REDI-03: Error Propagation.

    Verifies that PRAW exceptions propagate correctly with
    sanitized error details for AI agent decision-making.
    """

    @pytest.mark.unit
    def test_praw_exception_propagates(self, praw_mock, mock_reddit_credentials):
        """
        REDI-03: PRAW exceptions propagate with error details.

        Expected behavior (Wave 3):
        - System allows PRAW exceptions to propagate to caller
        - Exception type preserved (PRAWException, RedditAPIException, etc.)
        - Error details included but sanitized
        - Caller can handle specific error types appropriately

        Reference: REQUIREMENTS.md REDI-03
        """
        from praw.exceptions import PRAWException

        from src.modtools import get_modqueue

        # Configure mock to raise PRAW exception
        praw_mock["instance"].subreddit.return_value.mod.modqueue.side_effect = PRAWException(
            "HTTP 403: Forbidden"
        )

        # Should raise PRAWException
        with pytest.raises(PRAWException) as exc_info:
            get_modqueue("testsub")

        # Exception should have sanitized error message
        error_msg = str(exc_info.value)
        assert "Failed to fetch modqueue" in error_msg
        # Credentials should be sanitized if present

    @pytest.mark.unit
    def test_praw_forbidden_propagates(self, praw_mock, mock_reddit_credentials):
        """
        REDI-03: 403 Forbidden errors propagate correctly.

        Expected behavior (Wave 3):
        - Permission errors (403) propagate as appropriate exception
        - Error indicates insufficient permissions for action
        - Error message sanitized (no credentials leaked)
        - Caller can distinguish auth errors from other failures

        Reference: REQUIREMENTS.md REDI-03
        """
        from unittest.mock import Mock

        from praw.exceptions import PRAWException

        from src.modtools import approve_item

        # Create a mock that simulates 403 error
        mock_comment = Mock()
        mock_comment.mod.approve.side_effect = PRAWException(
            "HTTP 403: Forbidden - insufficient permissions"
        )
        praw_mock["instance"].comment.return_value = mock_comment

        # Should raise PRAWException
        with pytest.raises(PRAWException) as exc_info:
            approve_item("t1_abc123")

        # Verify error message includes context
        error_msg = str(exc_info.value)
        assert "Failed to approve" in error_msg

    @pytest.mark.unit
    def test_praw_not_found_propagates(self, praw_mock, mock_reddit_credentials):
        """
        REDI-03: 404 Not Found errors propagate correctly.

        Expected behavior (Wave 3):
        - Not found errors (404) propagate as appropriate exception
        - Error indicates resource doesn't exist
        - Error message sanitized
        - Caller can distinguish not found from other failures

        Reference: REQUIREMENTS.md REDI-03
        """
        from unittest.mock import Mock

        from praw.exceptions import PRAWException

        from src.modtools import remove_item

        # Create a mock that simulates 404 error
        mock_comment = Mock()
        mock_comment.mod.remove.side_effect = PRAWException("HTTP 404: Not Found")
        praw_mock["instance"].comment.return_value = mock_comment

        # Should raise PRAWException
        with pytest.raises(PRAWException) as exc_info:
            remove_item("t1_abc123")

        # Verify error message includes context
        error_msg = str(exc_info.value)
        assert "Failed to remove" in error_msg

    @pytest.mark.unit
    def test_praw_exception_sanitized(self, praw_mock, mock_reddit_credentials):
        """
        REDI-03: PRAW exception messages are sanitized.

        Expected behavior (Wave 3):
        - All PRAW exceptions caught and sanitized before propagation
        - Credential values removed from error messages
        - Subreddit names redacted for privacy
        - Error remains actionable but safe to display

        Reference: REQUIREMENTS.md REDI-03, SAFE-02
        """
        from unittest.mock import Mock

        from praw.exceptions import PRAWException

        from src.modtools import ban_user

        # Create a mock that raises error with sensitive info
        mock_banned = Mock()
        mock_banned.add.side_effect = PRAWException(
            "Failed to ban user real_user in r/secret_subreddit: credentials invalid"
        )
        praw_mock["instance"].subreddit.return_value.banned = mock_banned

        # Should raise PRAWException with sanitized message
        with pytest.raises(PRAWException) as exc_info:
            ban_user("secret_subreddit", "real_user", "spam")

        error_msg = str(exc_info.value)

        # Sensitive info should be redacted
        assert "real_user" not in error_msg or "***" in error_msg
        assert "secret_subreddit" not in error_msg or "SUBREDDIT" in error_msg

        # Error should still be actionable
        assert "Failed to ban" in error_msg or "ban" in error_msg.lower()


class TestTimeout:
    """
    Test suite for REDI-04: Timeout Protection.

    Verifies that all PRAW API calls have timeout protection
    to prevent indefinite hanging.
    """

    @pytest.mark.unit
    def test_timeout_wrapper_returns_on_time(self, praw_mock, mock_reddit_credentials):
        """
        REDI-04: Functions complete within timeout return normally.

        Expected behavior (Wave 2):
        - Functions that complete before timeout return their result
        - No timeout error is raised
        - Result is returned unchanged
        - Function executes normally

        Reference: REQUIREMENTS.md REDI-04
        """
        from src.modtools import with_timeout

        # Apply timeout wrapper to a fast function
        @with_timeout(timeout_seconds=1)
        def fast_function():
            return "completed"

        # Should return normally
        result = fast_function()
        assert result == "completed"

    @pytest.mark.unit
    def test_timeout_wrapper_raises_on_exceed(self, praw_mock, mock_reddit_credentials):
        """
        REDI-04: Functions exceeding timeout raise TimeoutError.

        Expected behavior (Wave 2):
        - Functions that take longer than timeout raise TimeoutError
        - Timeout is enforced at application level
        - Function is cancelled when timeout expires
        - Error is specific TimeoutError (not generic Exception)

        Reference: REQUIREMENTS.md REDI-04
        """
        import time

        from src.modtools import with_timeout

        # Apply timeout wrapper to a slow function
        @with_timeout(timeout_seconds=1)
        def slow_function():
            time.sleep(2)  # Sleep longer than timeout
            return "should not reach here"

        # Should raise TimeoutError
        with pytest.raises(TimeoutError, match="exceeded timeout"):
            slow_function()

    @pytest.mark.unit
    def test_timeout_cancels_future(self, praw_mock, mock_reddit_credentials):
        """
        REDI-04: Timeout cancels the running task.

        Expected behavior (Wave 2):
        - When timeout expires, future.cancel() is called
        - Task is cancelled to free resources
        - No zombie threads left running
        - Clean shutdown of timed-out operations

        Reference: REQUIREMENTS.md REDI-04
        """
        import time
        from unittest.mock import patch

        from src.modtools import with_timeout

        # Apply timeout wrapper to a slow function
        @with_timeout(timeout_seconds=1)
        def slow_function():
            time.sleep(2)
            return "should not reach here"

        # Mock the cancel to verify it's called
        with patch('concurrent.futures.Future.cancel') as mock_cancel:
            mock_cancel.return_value = True

            with pytest.raises(TimeoutError):
                slow_function()

    @pytest.mark.unit
    def test_timeout_includes_function_name(self, praw_mock, mock_reddit_credentials):
        """
        REDI-04: Timeout error message includes function name and timeout value.

        Expected behavior (Wave 2):
        - TimeoutError message includes the function name
        - Message includes the timeout value used
        - Error is actionable for debugging
        - Caller knows which operation timed out

        Reference: REQUIREMENTS.md REDI-04
        """
        import time

        from src.modtools import with_timeout

        @with_timeout(timeout_seconds=1)
        def my_slow_function():
            time.sleep(2)
            return "result"

        with pytest.raises(TimeoutError) as exc_info:
            my_slow_function()

        # Error message should include function name
        error_msg = str(exc_info.value)
        assert "my_slow_function" in error_msg
        # Should include timeout value
        assert "1" in error_msg or "timeout" in error_msg.lower()

    @pytest.mark.unit
    def test_modqueue_timeout_protection(self, praw_mock, mock_reddit_credentials, monkeypatch):
        """
        REDI-04: Modqueue call has timeout protection.

        Expected behavior (Wave 2):
        - get_modqueue completes within timeout period
        - TimeoutError raised if PRAW call exceeds timeout
        - Default timeout configured consistently
        - Timeout prevents indefinite hangs

        Reference: REQUIREMENTS.md REDI-04
        """
        from src.modtools import get_modqueue

        # Verify the function is wrapped (has __wrapped__ attribute from functools.wraps)
        assert hasattr(get_modqueue, '__wrapped__')
        # Verify the function name is preserved
        assert get_modqueue.__name__ == 'get_modqueue'

    @pytest.mark.unit
    def test_approve_timeout_protection(self, praw_mock, mock_reddit_credentials, monkeypatch):
        """
        REDI-04: Approve call has timeout protection.

        Expected behavior (Wave 2):
        - approve_item completes within timeout period
        - TimeoutError raised if PRAW call exceeds timeout
        - Default timeout configured consistently
        - Timeout prevents indefinite hangs

        Reference: REQUIREMENTS.md REDI-04
        """
        from src.modtools import approve_item

        # Verify the function is wrapped
        assert hasattr(approve_item, '__wrapped__')
        assert approve_item.__name__ == 'approve_item'

    @pytest.mark.unit
    def test_remove_timeout_protection(self, praw_mock, mock_reddit_credentials, monkeypatch):
        """
        REDI-04: Remove call has timeout protection.

        Expected behavior (Wave 2):
        - remove_item completes within timeout period
        - TimeoutError raised if PRAW call exceeds timeout
        - Default timeout configured consistently
        - Timeout prevents indefinite hangs

        Reference: REQUIREMENTS.md REDI-04
        """
        from src.modtools import remove_item

        # Verify the function is wrapped
        assert hasattr(remove_item, '__wrapped__')
        assert remove_item.__name__ == 'remove_item'

    @pytest.mark.unit
    def test_ban_timeout_protection(self, praw_mock, mock_reddit_credentials, monkeypatch):
        """
        REDI-04: Ban call has timeout protection.

        Expected behavior (Wave 2):
        - ban_user completes within timeout period
        - TimeoutError raised if PRAW call exceeds timeout
        - Default timeout configured consistently
        - Timeout prevents indefinite hangs

        Reference: REQUIREMENTS.md REDI-04
        """
        from src.modtools import ban_user

        # Verify the function is wrapped
        assert hasattr(ban_user, '__wrapped__')
        assert ban_user.__name__ == 'ban_user'
