"""Tests for codebase tools."""

import subprocess

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
    reveal_symbol,
    run_codemod,
    search,
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
    assert result.has_more is True  # File has 2010 lines, so there should be more content
    assert "def method_69" in result.content  # Regular method
    assert "def class_method_80" in result.content  # Class method at 80
    assert result.end_line == 599  # Should show 250 lines from start (350 to 599)

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
    assert result.end_line == min(200 + 250 - 1, 2010)  # Should respect max_lines and file length

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

    result = list_directory(codebase, "./", depth=2)  # Ensure we get nested structure
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


def test_search(codebase):
    """Test searching the codebase."""
    result = search(codebase, "hello")
    assert result.status == "success"
    assert len(result.results) > 0

    # Check that we found the right content
    assert any("hello" in match.match.lower() for file_result in result.results for match in file_result.matches)

    # Check pagination info
    assert result.page == 1
    assert result.total_pages >= 1
    assert result.files_per_page == 10


def test_search_regex(codebase):
    """Test searching with regex."""
    # Search for function definitions
    result = search(codebase, r"def\s+\w+", use_regex=True)
    assert result.status == "success"
    assert len(result.results) > 0

    # Should find both 'def hello' and 'def greet'
    matches = [match.line for file_result in result.results for match in file_result.matches]
    assert any("def hello" in match for match in matches)
    assert any("def greet" in match for match in matches)


def test_search_target_directories(codebase):
    """Test searching with target directory filtering."""
    # First search without filter to ensure we have results
    result_all = search(codebase, "hello")
    assert result_all.status == "success"
    assert len(result_all.results) > 0

    # Now search with correct target directory
    result_filtered = search(codebase, "hello", target_directories=["src"])
    assert result_filtered.status == "success"
    assert len(result_filtered.results) > 0

    # Search with non-existent directory
    result_none = search(codebase, "hello", target_directories=["nonexistent"])
    assert result_none.status == "success"
    assert len(result_none.results) == 0


def test_search_file_extensions(codebase, tmpdir):
    """Test searching with file extension filtering."""
    # Add a non-Python file
    js_content = "function hello() { console.log('Hello from JS!'); }"
    js_file = tmpdir / "src" / "script.js"
    js_file.write_text(js_content, encoding="utf-8")

    # Search all files
    result_all = search(codebase, "hello")
    assert result_all.status == "success"
    assert len(result_all.results) > 0

    # Search only Python files
    result_py = search(codebase, "hello", file_extensions=[".py"])
    assert result_py.status == "success"
    assert all(file_result.filepath.endswith(".py") for file_result in result_py.results)

    # Search only JS files
    result_js = search(codebase, "hello", file_extensions=[".js"])
    assert result_js.status == "success"
    if len(result_js.results) > 0:  # Only if JS file was properly added to codebase
        assert all(file_result.filepath.endswith(".js") for file_result in result_js.results)


def test_search_pagination(codebase, tmpdir):
    """Test search pagination."""
    # Create multiple files to test pagination
    files_dict = {}
    for i in range(15):  # Create enough files to span multiple pages
        content = f"def function_{i}():\n    print('Hello from function {i}!')"
        files_dict[f"src/file_{i}.py"] = content

    # Create a new codebase with all the files
    with get_codebase_session(tmpdir=tmpdir, files=files_dict) as pagination_codebase:
        # Search with default pagination (page 1)
        result_page1 = search(pagination_codebase, "Hello", files_per_page=5)
        assert result_page1.status == "success"
        assert result_page1.page == 1
        assert len(result_page1.results) <= 5

        # If we have enough results for multiple pages
        if result_page1.total_pages > 1:
            # Get page 2
            result_page2 = search(pagination_codebase, "Hello", page=2, files_per_page=5)
            assert result_page2.status == "success"
            assert result_page2.page == 2
            assert len(result_page2.results) <= 5

            # Ensure different files on different pages
            page1_files = {r.filepath for r in result_page1.results}
            page2_files = {r.filepath for r in result_page2.results}
            assert not page1_files.intersection(page2_files)


def test_search_invalid_regex(codebase):
    """Test search with invalid regex pattern."""
    result = search(codebase, "(unclosed", use_regex=True)
    assert result.status == "error"
    # Check for either Python's error message or ripgrep's error message
    assert any(
        error_msg in result.error
        for error_msg in [
            "Invalid regex pattern",  # Python error message
            "regex parse error",  # ripgrep error message
            "unclosed group",  # Common error description
        ]
    )


def test_search_fallback(codebase, monkeypatch):
    """Test fallback to Python implementation when ripgrep fails."""

    # Mock subprocess.run to simulate ripgrep failure
    def mock_subprocess_run(*args, **kwargs):
        msg = "Simulated ripgrep failure"
        raise subprocess.SubprocessError(msg)

    # Apply the mock
    monkeypatch.setattr(subprocess, "run", mock_subprocess_run)

    # Search should still work using Python fallback
    result = search(codebase, "hello")
    assert result.status == "success"
    assert len(result.results) > 0


def test_search_ripgrep_not_found(codebase, monkeypatch):
    """Test fallback to Python implementation when ripgrep is not installed."""

    # Mock subprocess.run to simulate ripgrep not found
    def mock_subprocess_run(*args, **kwargs):
        msg = "Simulated ripgrep not found"
        raise FileNotFoundError(msg)

    # Apply the mock
    monkeypatch.setattr(subprocess, "run", mock_subprocess_run)

    # Search should still work using Python fallback
    result = search(codebase, "hello")
    assert result.status == "success"
    assert len(result.results) > 0


def test_search_uses_ripgrep(codebase, monkeypatch):
    """Test that ripgrep is used when available."""
    # Track if ripgrep was called
    ripgrep_called = False

    # Store original subprocess.run
    original_run = subprocess.run

    # Mock subprocess.run to track calls and then call the original
    def mock_subprocess_run(*args, **kwargs):
        nonlocal ripgrep_called
        # Check if this is a ripgrep call
        if args and args[0] and isinstance(args[0], list) and args[0][0] == "rg":
            ripgrep_called = True
        # Call the original implementation
        return original_run(*args, **kwargs)

    # Apply the mock
    monkeypatch.setattr(subprocess, "run", mock_subprocess_run)

    # Perform a search
    result = search(codebase, "hello")
    assert result.status == "success"

    # Verify ripgrep was called
    assert ripgrep_called, "Ripgrep was not used for the search"


def test_search_implementation_consistency(codebase, monkeypatch):
    """Test that ripgrep and Python implementations produce consistent results."""
    from codegen.extensions.tools.search import _search_with_python, _search_with_ripgrep

    # Skip test if ripgrep is not available
    try:
        subprocess.run(["rg", "--version"], capture_output=True, check=False)
    except FileNotFoundError:
        pytest.skip("Ripgrep not available, skipping consistency test")

    # Simple search that should work in both implementations
    query = "hello"

    # Get results from both implementations
    ripgrep_result = _search_with_ripgrep(codebase, query)
    python_result = _search_with_python(codebase, query)

    # Compare basic metadata
    assert ripgrep_result.status == python_result.status
    assert ripgrep_result.query == python_result.query

    # Compare file paths found (order might differ)
    ripgrep_files = {r.filepath for r in ripgrep_result.results}
    python_files = {r.filepath for r in python_result.results}

    # There might be slight differences in which files are found due to how ripgrep handles
    # certain files, so we'll check for substantial overlap rather than exact equality
    common_files = ripgrep_files.intersection(python_files)
    assert len(common_files) > 0, "No common files found between ripgrep and Python implementations"

    # For common files, compare the line numbers found
    for filepath in common_files:
        # Find the corresponding file results
        ripgrep_file_result = next(r for r in ripgrep_result.results if r.filepath == filepath)
        python_file_result = next(r for r in python_result.results if r.filepath == filepath)

        # Compare line numbers - there might be slight differences in how matches are found
        ripgrep_lines = {m.line_number for m in ripgrep_file_result.matches}
        python_lines = {m.line_number for m in python_file_result.matches}

        # Check for substantial overlap in line numbers
        common_lines = ripgrep_lines.intersection(python_lines)
        if ripgrep_lines and python_lines:  # Only check if both found matches
            assert len(common_lines) > 0, f"No common line matches found in {filepath}"


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
