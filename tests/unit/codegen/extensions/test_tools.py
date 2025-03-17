"""Tests for codebase tools."""

import pytest

from codegen.extensions.tools import (
    create_file,
    create_pr,
    create_pr_comment,
    create_pr_review_comment,
    delete_file,
    edit_file,
    list_directory,
    move_symbol,
    rename_file,
    replacement_edit,
    replacement_edit_global,
    reveal_symbol,
    run_codemod,
    search_files_by_name,
    semantic_edit,
    semantic_search,
    view_file,
    view_pr,
)
from codegen.sdk.codebase.factory.get_session import get_codebase_session


@pytest.fixture
def codebase(tmpdir):
    """Create a simple codebase for testing."""
    # language=python
    content = """
def hello():
    print("Hello, world!")

class Greeter:
    def greet(self):
        hello()
"""
    with get_codebase_session(tmpdir=tmpdir, files={"src/main.py": content}) as codebase:
        yield codebase


@pytest.fixture
def large_codebase(tmpdir):
    """Create a codebase with a large file for pagination testing."""
    # Create a large file with predictable content
    large_file_lines = []
    # Add imports at the top
    large_file_lines.extend(
        [
            "from __future__ import annotations",
            "import sys",
            "import os",
            "from typing import List, Optional, Dict",
            "",
            "# Constants",
            "MAX_ITEMS = 100",
            "DEBUG = False",
            "",
            "# Main class definition",
            "class LargeClass:",
        ]
    )

    # Add methods with incrementing numbers
    for i in range(1, 401):  # This will create a 400+ line file
        if i % 20 == 0:
            # Add some class methods periodically
            large_file_lines.extend(["    @classmethod", f"    def class_method_{i}(cls) -> None:", f"        print('Class method {i}')", "        return None", ""])
        else:
            # Add regular methods
            large_file_lines.extend(
                [
                    f"    def method_{i}(self, param_{i}: int) -> str:",
                    f"        # Method {i} does something interesting",
                    f"        value = param_{i} * {i}",
                    f"        return f'Method {i} computed: {{value}}'",
                    "",
                ]
            )

    large_file_content = "\n".join(large_file_lines)

    files = {
        "src/main.py": """
def hello():
    print("Hello, world!")
""",
        "src/large_file.py": large_file_content,
    }

    with get_codebase_session(tmpdir=tmpdir, files=files) as codebase:
        yield codebase


def test_view_file(codebase):
    """Test viewing a file."""
    # Test basic file viewing
    result = view_file(codebase, "src/main.py")
    assert result.status == "success"
    assert result.filepath == "src/main.py"
    assert "hello()" in result.content
    # For small files, pagination fields should not be present
    assert result.start_line is None
    assert result.end_line is None
    assert result.has_more is None
    assert result.max_lines_per_page is None


def test_view_file_pagination(large_codebase):
    """Test viewing a file with pagination."""
    # Test default pagination (should show first max_lines lines)
    result = view_file(large_codebase, "src/large_file.py")
    assert result.status == "success"
    assert result.start_line == 1
    assert result.end_line == 250  # Default max_lines
    assert result.has_more is True
    assert result.max_lines_per_page == 250
    assert "from __future__ import annotations" in result.content  # First line
    assert "def method_1" in result.content  # Early method
    assert "def method_251" not in result.content  # Method after page 1

    # Test custom pagination range
    result = view_file(large_codebase, "src/large_file.py", start_line=200, end_line=250)
    assert result.status == "success"
    assert result.start_line == 200
    assert result.end_line == 250
    assert result.has_more is True
    assert "def method_39" in result.content  # Regular method before class method
    assert "def class_method_40" in result.content  # Class method at 40
    assert "def method_41" in result.content  # Regular method after class method
    assert "from __future__ import annotations" not in result.content  # Before range
    assert "def method_251" not in result.content  # After range

    # Test viewing end of file
    result = view_file(large_codebase, "src/large_file.py", start_line=350)
    assert result.status == "success"
    assert result.start_line == 350
    # File has 2010 lines, so there should be more content
    assert result.has_more is True
    assert "def method_69" in result.content  # Regular method
    assert "def class_method_80" in result.content  # Class method at 80
    # Should show 250 lines from start (350 to 599)
    assert result.end_line == 599

    # Test custom max_lines
    result = view_file(large_codebase, "src/large_file.py", max_lines=100)
    assert result.status == "success"
    assert result.start_line == 1
    assert result.end_line == 100
    assert result.has_more is True
    assert result.max_lines_per_page == 100
    assert "from __future__ import annotations" in result.content
    assert len(result.content.splitlines()) <= 100

    # Test line numbers display
    result = view_file(large_codebase, "src/large_file.py", start_line=198, end_line=202, line_numbers=True)
    assert result.status == "success"
    assert "198|" in result.content
    assert "199|" in result.content
    assert "200|" in result.content
    assert "201|" in result.content
    assert "202|" in result.content

    # Test without line numbers
    result = view_file(large_codebase, "src/large_file.py", start_line=198, end_line=202, line_numbers=False)
    assert result.status == "success"
    assert "198|" not in result.content
    assert "199|" not in result.content


def test_view_file_pagination_edge_cases(large_codebase):
    """Test edge cases for file pagination."""
    # Test start_line > end_line (should respect provided end_line)
    result = view_file(large_codebase, "src/large_file.py", start_line=200, end_line=100)
    assert result.status == "success"
    assert result.start_line == 200
    assert result.end_line == 100  # Should respect provided end_line
    assert result.content == ""  # No content since end_line < start_line

    # Test start_line > file length (should adjust to valid range)
    result = view_file(large_codebase, "src/large_file.py", start_line=2000)
    assert result.status == "success"
    assert result.start_line == 2000  # Should use provided start_line
    assert result.end_line == 2010  # Should adjust to total lines
    assert result.has_more is False

    # Test end_line > file length (should truncate to file length)
    result = view_file(large_codebase, "src/large_file.py", start_line=200, end_line=2000)
    assert result.status == "success"
    assert result.start_line == 200
    # Should respect max_lines and file length
    assert result.end_line == min(200 + 250 - 1, 2010)

    # Test negative start_line (should default to 1)
    result = view_file(large_codebase, "src/large_file.py", start_line=-10)
    assert result.status == "success"
    assert result.start_line == 1
    assert result.end_line == 250


def test_list_directory(codebase):
    """Test listing directory contents."""
    # Create a nested directory structure for testing
    create_file(codebase, "src/core/__init__.py", "")
    create_file(codebase, "src/core/models.py", "")
    create_file(codebase, "src/utils.py", "")

    # Ensure we get nested structure
    result = list_directory(codebase, "./", depth=2)
    assert result.status == "success"

    # Check directory structure
    dir_info = result.directory_info

    # Check that src exists and has proper structure
    src_dir = next(d for d in dir_info.subdirectories)
    assert src_dir.name == "src"
    assert "main.py" in src_dir.files
    assert "utils.py" in src_dir.files

    # Check nested core directory exists in subdirectories
    assert any(d.name == "core" for d in src_dir.subdirectories)
    core_dir = next(d for d in src_dir.subdirectories if d.name == "core")

    # Verify rendered output has proper tree structure
    rendered = result.render()
    print(rendered)
    expected_tree = """
└── src/
    ├── main.py
    ├── utils.py
    └── core/"""
    assert expected_tree in rendered.strip()


def test_edit_file(codebase):
    """Test editing a file."""
    result = edit_file(codebase, "src/main.py", "print('edited')")
    assert result.status == "success"
    assert result.filepath == "src/main.py"
    assert "+print('edited')" in result.diff
    assert "-def hello():" in result.diff  # Check that old content is shown in diff


def test_create_file(codebase):
    """Test creating a file."""
    result = create_file(codebase, "src/new.py", "print('new')")
    assert result.status == "success"
    assert result.filepath == "src/new.py"
    assert result.file_info.content == "1|print('new')"


def test_delete_file(codebase):
    """Test deleting a file."""
    result = delete_file(codebase, "src/main.py")
    assert result.status == "success"
    assert result.filepath == "src/main.py"


def test_rename_file(codebase):
    """Test renaming a file."""
    result = rename_file(codebase, "src/main.py", "src/renamed.py")
    assert result.status == "success"
    assert result.old_filepath == "src/main.py"
    assert result.new_filepath == "src/renamed.py"


def test_move_symbol(codebase):
    """Test moving a symbol between files."""
    # Create target file first
    create_file(codebase, "src/target.py", "")

    result = move_symbol(
        codebase,
        source_file="src/main.py",
        symbol_name="hello",
        target_file="src/target.py",
    )
    assert result.status == "success"
    assert result.symbol_name == "hello"
    assert result.source_file == "src/main.py"
    assert result.target_file == "src/target.py"


def test_search_files_by_name(codebase):
    """Test searching files by name."""
    create_file(codebase, "src/main.py", "print('hello')")
    create_file(codebase, "src/target.py", "print('world')")
    result = search_files_by_name(codebase, "*.py")
    assert result.status == "success"
    assert len(result.files) == 2
    assert "src/main.py" in result.files
    assert "src/target.py" in result.files
    result = search_files_by_name(codebase, "main.py")
    assert result.status == "success"
    assert len(result.files) == 1
    assert "src/main.py" in result.files


def test_reveal_symbol(codebase):
    """Test revealing symbol relationships."""
    result = reveal_symbol(
        codebase,
        symbol_name="hello",
        max_depth=1,
    )
    assert result.status == "success"
    assert not result.truncated


@pytest.mark.skip("TODO")
def test_semantic_edit(codebase):
    """Test semantic editing."""
    edit_spec = """
# ... existing code ...
def hello():
    print("Hello from semantic edit!")
# ... existing code ...
"""
    result = semantic_edit(codebase, "src/main.py", edit_spec)
    assert result.status == "success"
    assert "Hello from semantic edit!" in result.new_content


@pytest.mark.skip("TODO")
def test_semantic_search(codebase):
    """Test semantic search."""
    result = semantic_search(codebase, "function that prints hello")
    assert result.status == "success"
    assert len(result.results) > 0


@pytest.mark.skip("TODO: Github tests")
def test_create_pr(codebase):
    """Test creating a PR."""
    result = create_pr(codebase, "Test PR", "This is a test PR")
    assert result.status == "success"
    assert result.title == "Test PR"


@pytest.mark.skip("TODO: Github tests")
def test_view_pr(codebase):
    """Test viewing a PR."""
    result = view_pr(codebase, 1)
    assert result.status == "success"
    assert result.pr_id == 1
    assert result.patch != ""


@pytest.mark.skip("TODO: Github tests")
def test_create_pr_comment(codebase):
    """Test creating a PR comment."""
    result = create_pr_comment(codebase, 1, "Test comment")
    assert result.status == "success"
    assert result.pr_number == 1
    assert result.body == "Test comment"


@pytest.mark.skip("TODO: Github tests")
def test_create_pr_review_comment(codebase):
    """Test creating a PR review comment."""
    result = create_pr_review_comment(
        codebase,
        pr_number=1,
        body="Test review comment",
        commit_sha="abc123",
        path="src/main.py",
        line=1,
    )
    assert result.status == "success"
    assert result.pr_number == 1
    assert result.path == "src/main.py"
    assert result.line == 1
    assert result.body == "Test review comment"


def test_replacement_edit(codebase):
    """Test regex-based replacement editing."""
    # Test basic replacement
    result = replacement_edit(
        codebase,
        filepath="src/main.py",
        pattern=r'print\("Hello, world!"\)',
        replacement='print("Goodbye, world!")',
    )
    assert result.status == "success"
    assert 'print("Goodbye, world!")' in result.new_content

    # Test with line range
    result = replacement_edit(
        codebase,
        filepath="src/main.py",
        pattern=r"Greeter",
        replacement="Welcomer",
        start=5,  # Class definition line
        end=7,
    )
    assert result.status == "success"
    assert "class Welcomer" in result.new_content

    # Test with regex groups
    result = replacement_edit(
        codebase,
        filepath="src/main.py",
        pattern=r"def (\w+)\(\):",
        replacement=r"def \1_function():",
    )
    assert result.status == "success"
    assert "def hello_function():" in result.new_content

    # Test with count limit
    result = replacement_edit(
        codebase,
        filepath="src/main.py",
        pattern=r"def",
        replacement="async def",
        count=1,  # Only replace first occurrence
    )
    assert result.status == "success"
    assert result.new_content.count("async def") == 1

    # Test no matches
    result = replacement_edit(
        codebase,
        filepath="src/main.py",
        pattern=r"nonexistent_pattern",
        replacement="replacement",
    )
    assert result.status == "unchanged"
    assert "No matches found" in str(result)


def test_replacement_edit_global(codebase):
    """Test global regex-based replacement editing."""
    # Create additional test file
    create_file(
        codebase,
        filepath="src/other.py",
        content="""
def hello():
    print("Hello, world!")

def greet():
    print("Hello!")
""",
    )
    codebase.commit()  # Commit the new file so it can be found

    # List directory to debug
    print("Directory contents:")
    print(list_directory(codebase, "src"))

    # Test basic global replacement across files
    result = replacement_edit_global(
        codebase,
        file_pattern="*.py",
        pattern=r'print\("Hello.*?"\)',
        replacement='print("Goodbye!")',
    )
    print(f"Found files: {search_files_by_name(codebase, '*.py').files}")  # Debug print
    assert result.status == "success"
    assert result.diff  # Should have modified both files
    assert 'print("Goodbye!")' in result.diff

    # Test with count limit
    result = replacement_edit_global(
        codebase,
        file_pattern="*.py",
        pattern=r"def",
        replacement="async def",
        count=1,  # Only replace first occurrence in each file
    )
    assert result.status == "success"
    assert result.diff  # Should have modified both files

    # Test invalid regex pattern
    result = replacement_edit_global(
        codebase,
        file_pattern="*.py",
        pattern=r"[invalid",  # Invalid regex pattern
        replacement="replacement",
    )
    assert result.status == "error"
    assert result.error_pattern == "[invalid"
    assert "Invalid regex pattern" in result.message

    # Test no matches
    result = replacement_edit_global(
        codebase,
        file_pattern="*.py",
        pattern=r"nonexistent_pattern",
        replacement="replacement",
    )
    assert result.status == "success"
    assert not result.diff  # Should be empty since no files were modified


def test_run_codemod(codebase):
    """Test running custom codemods."""
    # Test adding type hints
    codemod_source = """
def run(codebase: Codebase):
    for file in codebase.files:
        file.edit('# hello, world!' + file.content)
"""
    result = run_codemod(codebase, codemod_source)
    assert result["status"] == "success"
    assert "+# hello, world" in result["diff"]
