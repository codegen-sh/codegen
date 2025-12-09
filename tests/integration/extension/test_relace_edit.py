"""Integration tests for the relace_edit tool."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from codegen.extensions.tools.relace_edit import relace_edit
from codegen.sdk.core.codebase import Codebase


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a simple file structure for testing
        base_dir = Path(temp_dir)

        # Create a simple Python file
        test_file = base_dir / "test_file.py"
        test_file.write_text("""
def hello_world():
    return 'Hello, World!'

def goodbye_world():
    return 'Goodbye, World!'
""")

        # Create a JavaScript file
        js_file = base_dir / "test_file.js"
        js_file.write_text("""
function helloWorld() {
    return 'Hello, World!';
}

function goodbyeWorld() {
    return 'Goodbye, World!';
}
""")

        # Create a codebase from the temp directory
        codebase = Codebase.from_directory(str(base_dir))

        yield codebase


@pytest.mark.skipif(not os.getenv("RELACE_API"), reason="RELACE_API environment variable not set")
def test_relace_edit_real_api(temp_workspace):
    """Test relace_edit with the real API.

    This test is skipped if the RELACE_API environment variable is not set.
    """
    # Test editing a Python file
    edit_snippet = """
# Keep existing imports

# Modify hello_world function
def hello_world():
    print("Starting greeting")
    return 'Hello, Modified World!'

# Keep goodbye_world function
"""

    result = relace_edit(temp_workspace, "test_file.py", edit_snippet)
    assert result.status == "success"

    # Verify the file was modified correctly
    from codegen.extensions.tools import view_file

    file_content = view_file(temp_workspace, "test_file.py")
    assert 'print("Starting greeting")' in file_content.content
    assert "Hello, Modified World!" in file_content.content
    assert "Goodbye, World!" in file_content.content  # Should be preserved


@patch("codegen.extensions.tools.relace_edit.requests.post")
def test_relace_edit_mock_api(mock_post, temp_workspace):
    """Test relace_edit with a mocked API."""
    # Mock the API response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "success",
        "result": """
def hello_world():
    print("Mocked greeting")
    return 'Hello, Mocked World!'

def goodbye_world():
    return 'Goodbye, World!'
""",
    }
    mock_post.return_value = mock_response

    # Test editing a Python file
    edit_snippet = """
# Modify hello_world function
def hello_world():
    print("Mocked greeting")
    return 'Hello, Mocked World!'

# Keep goodbye_world function
"""

    result = relace_edit(temp_workspace, "test_file.py", edit_snippet)
    assert result.status == "success"

    # Verify the API was called with the correct parameters
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert "content" in kwargs["json"]
    assert "edit_snippet" in kwargs["json"]

    # Verify the file was modified correctly
    from codegen.extensions.tools import view_file

    file_content = view_file(temp_workspace, "test_file.py")
    assert 'print("Mocked greeting")' in file_content.content
    assert "Hello, Mocked World!" in file_content.content


@patch("codegen.extensions.tools.relace_edit.requests.post")
def test_relace_edit_api_error(mock_post, temp_workspace):
    """Test relace_edit with API errors."""
    # Mock an API error response
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {"status": "error", "error": "Invalid request"}
    mock_post.return_value = mock_response

    # Test with API error
    result = relace_edit(temp_workspace, "test_file.py", "# Invalid edit")
    assert result.status == "error"
    assert "API error" in result.error

    # Mock a network error
    mock_post.side_effect = Exception("Network error")

    # Test with network error
    result = relace_edit(temp_workspace, "test_file.py", "# Invalid edit")
    assert result.status == "error"
    assert "Network error" in result.error

    # Test with non-existent file
    result = relace_edit(temp_workspace, "nonexistent_file.py", "# Edit")
    assert result.status == "error"
    assert "not found" in result.error
