"""Tests for Slack utility functions."""

from unittest.mock import MagicMock

import pytest
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from codegen.extensions.slack.utils import safe_add_reaction


def test_safe_add_reaction_success():
    """Test that safe_add_reaction works correctly when the API call succeeds."""
    mock_client = MagicMock(spec=WebClient)
    mock_client.reactions_add.return_value = {"ok": True}

    result = safe_add_reaction(client=mock_client, channel="C12345", timestamp="1234567890.123456", name="thumbsup")

    assert result == {"ok": True}
    mock_client.reactions_add.assert_called_once_with(channel="C12345", timestamp="1234567890.123456", name="thumbsup")


def test_safe_add_reaction_already_reacted():
    """Test that safe_add_reaction handles the 'already_reacted' error correctly."""
    mock_client = MagicMock(spec=WebClient)

    # Create a mock SlackApiError with the 'already_reacted' error
    mock_response = {"ok": False, "error": "already_reacted"}
    mock_error = SlackApiError(message="already_reacted", response=mock_response)
    mock_client.reactions_add.side_effect = mock_error

    result = safe_add_reaction(client=mock_client, channel="C12345", timestamp="1234567890.123456", name="thumbsup")

    # Should return a success response with already_exists=True
    assert result == {"ok": True, "already_exists": True}
    mock_client.reactions_add.assert_called_once_with(channel="C12345", timestamp="1234567890.123456", name="thumbsup")


def test_safe_add_reaction_other_error():
    """Test that safe_add_reaction re-raises other errors."""
    mock_client = MagicMock(spec=WebClient)

    # Create a mock SlackApiError with a different error
    mock_response = {"ok": False, "error": "invalid_auth"}
    mock_error = SlackApiError(message="invalid_auth", response=mock_response)
    mock_client.reactions_add.side_effect = mock_error

    with pytest.raises(SlackApiError):
        safe_add_reaction(client=mock_client, channel="C12345", timestamp="1234567890.123456", name="thumbsup")

    mock_client.reactions_add.assert_called_once_with(channel="C12345", timestamp="1234567890.123456", name="thumbsup")
