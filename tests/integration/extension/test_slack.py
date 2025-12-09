"""Integration tests for Slack tools."""

from unittest.mock import MagicMock

import pytest

from codegen.extensions.tools.link_annotation import add_links_to_message
from codegen.sdk.core.codebase import Codebase


@pytest.fixture
def mock_codebase():
    """Create a mock codebase for testing."""
    codebase = MagicMock(spec=Codebase)

    # Mock the symbol lookup functionality
    def mock_get_symbol(symbol_name):
        if symbol_name in ["test_function", "TestClass"]:
            mock_symbol = MagicMock()
            mock_symbol.filepath = f"src/{symbol_name.lower()}.py"
            return mock_symbol
        return None

    codebase.get_symbol.side_effect = mock_get_symbol

    # Mock the file exists functionality
    def mock_file_exists(filepath):
        return filepath in ["src/file1.py", "src/file2.py", "src/test_function.py", "src/testclass.py"]

    codebase.file_exists.side_effect = mock_file_exists

    return codebase


def test_add_links_to_message(mock_codebase):
    """Test adding links to a Slack message."""
    # Test with symbol names
    message = "Check the `test_function` and `TestClass` implementations."
    result = add_links_to_message(message, mock_codebase)

    # Verify links were added for symbols
    assert "`test_function`" not in result  # Should be replaced with a link
    assert "`TestClass`" not in result  # Should be replaced with a link
    assert "src/test_function.py" in result
    assert "src/testclass.py" in result

    # Test with file paths
    message = "Look at `src/file1.py` and `src/file2.py`."
    result = add_links_to_message(message, mock_codebase)

    # Verify links were added for files
    assert "`src/file1.py`" not in result  # Should be replaced with a link
    assert "`src/file2.py`" not in result  # Should be replaced with a link
    assert "src/file1.py" in result
    assert "src/file2.py" in result

    # Test with non-existent symbols and files
    message = "Check `nonexistent_function` and `src/nonexistent.py`."
    result = add_links_to_message(message, mock_codebase)

    # Verify no links were added for non-existent items
    assert "`nonexistent_function`" in result  # Should remain as is
    assert "`src/nonexistent.py`" in result  # Should remain as is

    # Test with mixed content
    message = "Check `test_function` and regular text with `src/file1.py` and *markdown*."
    result = add_links_to_message(message, mock_codebase)

    # Verify links were added only for valid symbols and files
    assert "`test_function`" not in result
    assert "`src/file1.py`" not in result
    assert "src/test_function.py" in result
    assert "src/file1.py" in result
    assert "*markdown*" in result  # Markdown should be preserved


def test_send_slack_message():
    """Test sending a message to Slack.

    Note: This is a mock test since we can't actually send messages in the test environment.
    """
    # Create a mock say function
    mock_say = MagicMock()

    # Create a mock codebase
    mock_codebase = MagicMock(spec=Codebase)

    # Import the function directly to test
    from codegen.extensions.langchain.tools import SlackSendMessageTool

    # Create the tool
    tool = SlackSendMessageTool(codebase=mock_codebase, say=mock_say)

    # Test sending a message
    result = tool._run("Test message")

    # Verify the message was sent
    mock_say.assert_called_once()
    assert "✅ Message sent successfully" in result
