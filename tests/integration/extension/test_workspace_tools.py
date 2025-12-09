"""Integration tests for workspace tools."""

import tempfile
from pathlib import Path

import pytest

from codegen.extensions.tools import (
    create_file,
    delete_file,
    edit_file,
    list_directory,
    rename_file,
    view_file,
)
from codegen.extensions.tools.replacement_edit import replacement_edit
from codegen.extensions.tools.search import search
from codegen.sdk.core.codebase import Codebase


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a simple file structure for testing
        base_dir = Path(temp_dir)

        # Create a simple Python file
        test_file = base_dir / "test_file.py"
        test_file.write_text("def hello_world():\n    return 'Hello, World!'\n")

        # Create a directory with files
        test_dir = base_dir / "test_dir"
        test_dir.mkdir()
        (test_dir / "file1.txt").write_text("File 1 content")
        (test_dir / "file2.txt").write_text("File 2 content")

        # Create a nested directory
        nested_dir = test_dir / "nested"
        nested_dir.mkdir()
        (nested_dir / "nested_file.txt").write_text("Nested file content")

        # Create a codebase from the temp directory
        codebase = Codebase.from_directory(str(base_dir))

        yield codebase


def test_view_file(temp_workspace):
    """Test viewing a file."""
    # Test viewing a file that exists
    result = view_file(temp_workspace, "test_file.py")
    assert result.status == "success"
    assert "def hello_world()" in result.content

    # Test viewing a file with line numbers
    result = view_file(temp_workspace, "test_file.py", line_numbers=True)
    assert result.status == "success"
    assert "1|def hello_world()" in result.content

    # Test viewing a file with line range
    result = view_file(temp_workspace, "test_file.py", start_line=1, end_line=1)
    assert result.status == "success"
    assert "def hello_world()" in result.content
    assert "return 'Hello, World!'" not in result.content

    # Test viewing a file that doesn't exist
    result = view_file(temp_workspace, "nonexistent_file.py")
    assert result.status == "error"
    assert "not found" in result.error


def test_list_directory(temp_workspace):
    """Test listing directory contents."""
    # Test listing the root directory
    result = list_directory(temp_workspace, "./")
    assert result.status == "success"
    assert "test_file.py" in result.content
    assert "test_dir" in result.content

    # Test listing a subdirectory
    result = list_directory(temp_workspace, "test_dir")
    assert result.status == "success"
    assert "file1.txt" in result.content
    assert "file2.txt" in result.content
    assert "nested" in result.content

    # Test listing with depth
    result = list_directory(temp_workspace, "./", depth=2)
    assert result.status == "success"
    assert "test_file.py" in result.content
    assert "test_dir" in result.content
    assert "file1.txt" in result.content
    assert "file2.txt" in result.content
    assert "nested" in result.content

    # Test listing a directory that doesn't exist
    result = list_directory(temp_workspace, "nonexistent_dir")
    assert result.status == "error"
    assert "not found" in result.error


def test_create_file(temp_workspace):
    """Test creating a file."""
    # Test creating a new file
    result = create_file(temp_workspace, "new_file.py", "print('New file')")
    assert result.status == "success"

    # Verify the file was created
    result = view_file(temp_workspace, "new_file.py")
    assert result.status == "success"
    assert "print('New file')" in result.content

    # Test creating a file that already exists
    result = create_file(temp_workspace, "test_file.py", "# Overwrite")
    assert result.status == "error"
    assert "already exists" in result.error

    # Test creating a file in a directory that doesn't exist
    result = create_file(temp_workspace, "nonexistent_dir/file.py", "# Content")
    assert result.status == "error"
    assert "directory does not exist" in result.error


def test_edit_file(temp_workspace):
    """Test editing a file."""
    # Test editing an existing file
    result = edit_file(temp_workspace, "test_file.py", "# Modified file\ndef hello_world():\n    return 'Modified!'")
    assert result.status == "success"

    # Verify the file was modified
    result = view_file(temp_workspace, "test_file.py")
    assert result.status == "success"
    assert "# Modified file" in result.content
    assert "return 'Modified!'" in result.content

    # Test editing a file that doesn't exist
    result = edit_file(temp_workspace, "nonexistent_file.py", "# Content")
    assert result.status == "error"
    assert "not found" in result.error


def test_delete_file(temp_workspace):
    """Test deleting a file."""
    # Test deleting an existing file
    result = delete_file(temp_workspace, "test_dir/file1.txt")
    assert result.status == "success"

    # Verify the file was deleted
    result = list_directory(temp_workspace, "test_dir")
    assert result.status == "success"
    assert "file1.txt" not in result.content
    assert "file2.txt" in result.content

    # Test deleting a file that doesn't exist
    result = delete_file(temp_workspace, "nonexistent_file.py")
    assert result.status == "error"
    assert "not found" in result.error


def test_rename_file(temp_workspace):
    """Test renaming a file."""
    # Test renaming an existing file
    result = rename_file(temp_workspace, "test_file.py", "renamed_file.py")
    assert result.status == "success"

    # Verify the file was renamed
    result = list_directory(temp_workspace, "./")
    assert result.status == "success"
    assert "test_file.py" not in result.content
    assert "renamed_file.py" in result.content

    # Test renaming a file that doesn't exist
    result = rename_file(temp_workspace, "nonexistent_file.py", "new_name.py")
    assert result.status == "error"
    assert "not found" in result.error

    # Test renaming to a file that already exists
    # First create a file
    create_file(temp_workspace, "target_file.py", "# Target file")
    result = rename_file(temp_workspace, "renamed_file.py", "target_file.py")
    assert result.status == "error"
    assert "already exists" in result.error


def test_search(temp_workspace):
    """Test searching the codebase."""
    # Test searching for text
    result = search(temp_workspace, "Hello, World!")
    assert result.status == "success"
    assert len(result.matches) > 0
    assert "test_file.py" in result.matches[0]["filepath"]

    # Test searching with regex
    result = search(temp_workspace, "def.*world", use_regex=True)
    assert result.status == "success"
    assert len(result.matches) > 0

    # Test searching with file extensions
    result = search(temp_workspace, "content", file_extensions=[".txt"])
    assert result.status == "success"
    assert len(result.matches) > 0
    assert all(".txt" in match["filepath"] for match in result.matches)

    # Test searching with no matches
    result = search(temp_workspace, "nonexistent_text")
    assert result.status == "success"
    assert len(result.matches) == 0


def test_replacement_edit(temp_workspace):
    """Test replacement edit."""
    # Test replacing text in a file
    result = replacement_edit(
        temp_workspace,
        filepath="test_file.py",
        pattern="Hello, World!",
        replacement="Goodbye, World!",
    )
    assert result.status == "success"

    # Verify the replacement was made
    result = view_file(temp_workspace, "test_file.py")
    assert result.status == "success"
    assert "Goodbye, World!" in result.content
    assert "Hello, World!" not in result.content

    # Test replacing with regex groups
    result = replacement_edit(
        temp_workspace,
        filepath="test_file.py",
        pattern=r"def (hello_world)\(\):",
        replacement=r"def \1_function():",
    )
    assert result.status == "success"

    # Verify the regex replacement was made
    result = view_file(temp_workspace, "test_file.py")
    assert result.status == "success"
    assert "def hello_world_function():" in result.content

    # Test replacing with line range
    # First create a multi-line file
    content = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5"
    create_file(temp_workspace, "lines.txt", content)

    result = replacement_edit(
        temp_workspace,
        filepath="lines.txt",
        pattern="Line",
        replacement="Modified",
        start=2,
        end=4,
    )
    assert result.status == "success"

    # Verify only lines in the range were modified
    result = view_file(temp_workspace, "lines.txt")
    assert result.status == "success"
    assert "Line 1" in result.content
    assert "Modified 2" in result.content
    assert "Modified 3" in result.content
    assert "Modified 4" in result.content
    assert "Line 5" in result.content

    # Test replacing with count
    create_file(temp_workspace, "count.txt", "Replace Replace Replace Replace")

    result = replacement_edit(
        temp_workspace,
        filepath="count.txt",
        pattern="Replace",
        replacement="Changed",
        count=2,
    )
    assert result.status == "success"

    # Verify only the specified number of replacements were made
    result = view_file(temp_workspace, "count.txt")
    assert result.status == "success"
    assert "Changed Changed Replace Replace" in result.content

    # Test replacing in a file that doesn't exist
    result = replacement_edit(
        temp_workspace,
        filepath="nonexistent_file.py",
        pattern="pattern",
        replacement="replacement",
    )
    assert result.status == "error"
    assert "not found" in result.error
