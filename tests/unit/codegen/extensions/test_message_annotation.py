"""Tests for message annotation functionality."""

import pytest

from codegen.extensions.tools.link_annotation import (
    MessageChannel,
    add_links_to_message,
    extract_code_snippets,
    format_link,
    is_likely_filepath,
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

def hello_duplicate():
    pass

def hello_duplicate():
    pass

class Greeter_duplicate:
    pass
"""
    # Create multiple files to test file linking
    files = {
        "src/main.py": content,
        "src/utils/helpers.py": "# Helper functions",
        "src/utils/more/nested.py": "# Nested module",
        "docs/README.md": "# Documentation",
        "tsconfig.json": "{}",
    }
    with get_codebase_session(tmpdir=tmpdir, files=files) as codebase:
        yield codebase


def test_format_link_linear():
    """Test linear link formatting."""
    assert format_link("test", "http://example.com", MessageChannel.LINEAR) == "[test](http://example.com)"


def test_format_link_markdown():
    """Test markdown link formatting."""
    assert format_link("test", "http://example.com", MessageChannel.MARKDOWN) == "[test](http://example.com)"


def test_format_link_html():
    """Test HTML link formatting."""
    assert format_link("test", "http://example.com", MessageChannel.HTML) == "<a href='http://example.com'>test</a>"


def test_format_link_slack():
    """Test Slack link formatting."""
    assert format_link("test", "http://example.com", MessageChannel.SLACK) == "<http://example.com|test>"


def test_extract_code_snippets():
    """Test extracting code snippets from messages."""
    message = "Here is some `code` and `more code` and ```a code block``` and `final code`"
    snippets = extract_code_snippets(message)
    assert snippets == ["code", "more code", "final code"]


def test_is_likely_filepath():
    """Test filepath detection."""
    # Should detect paths with slashes
    assert is_likely_filepath("src/file.py")
    assert is_likely_filepath("path/to/file")

    # Should detect common extensions
    assert is_likely_filepath("file.py")
    assert is_likely_filepath("component.tsx")
    assert is_likely_filepath("config.json")
    assert is_likely_filepath("README.md")

    # Should not detect regular words
    assert not is_likely_filepath("hello")
    assert not is_likely_filepath("Greeter")
    assert not is_likely_filepath("function")


def test_add_links_single_symbol(codebase):
    """Test adding links for a single symbol."""
    message = "Here is the `hello` function"
    result = add_links_to_message(message, codebase, channel=MessageChannel.SLACK)
    assert "|hello>" in result


def test_add_links_class(codebase):
    """Test adding links for a class."""
    message = "The `Greeter` class"
    result = add_links_to_message(message, codebase)
    assert "Greeter" in result
    assert result.count("<") == 1  # One link should be created


def test_add_links_filepath(codebase):
    """Test adding links for filepaths."""
    message = "Check out `src/main.py` and `src/utils/helpers.py`"
    result = add_links_to_message(message, codebase)
    assert "|src/main.py>" in result
    assert "|src/utils/helpers.py>" in result


def test_add_links_directory(codebase):
    """Test adding links for directories."""
    message = "Look in the `src/utils` directory and `src/utils/more`"
    result = add_links_to_message(message, codebase)
    assert "|src/utils>" in result
    assert "|src/utils/more>" in result


def test_add_links_filepath_with_extension(codebase):
    """Test adding links for files with common extensions."""
    message = "See `tsconfig.json` and `docs/README.md`"
    result = add_links_to_message(message, codebase)
    assert "|tsconfig.json>" in result
    assert "|docs/README.md>" in result


def test_nonexistent_filepath(codebase):
    """Test handling of nonexistent filepaths."""
    message = "This `src/nonexistent.py` should not be linked"
    result = add_links_to_message(message, codebase)
    assert result == message  # Message should remain unchanged


def test_nonexistent_directory(codebase):
    """Test handling of nonexistent directories."""
    message = "This `src/nonexistent/dir` should not be linked"
    result = add_links_to_message(message, codebase)
    assert result == message  # Message should remain unchanged


def test_ignore_code_blocks(codebase):
    """Test that code blocks are ignored."""
    message = """Here's a code block:
```python
def hello():
    print("Hello!")
```
And here's an inline `hello` reference."""

    result = add_links_to_message(message, codebase)
    # The inline reference should be linked
    assert "<" in result
    # But the code block should remain unchanged
    assert "```python" in result
    assert "def hello():" in result


def test_nonexistent_symbol(codebase):
    """Test handling of nonexistent symbols."""
    message = "This `nonexistent_function` should not be linked"
    result = add_links_to_message(message, codebase)
    assert result == message  # Message should remain unchanged


def test_duplicate_symbols(codebase):
    """Test handling of duplicate symbols."""
    message = "This `hello_duplicate` should not be linked"
    result = add_links_to_message(message, codebase)
    assert result == message  # Message should remain unchanged


def test_mixed_content(codebase):
    """Test message with mixed content types."""
    message = """Here's a complex message:
- Valid symbol: `hello`
- Valid file: `src/main.py`
- Valid directory: `src/utils`
- Invalid symbol: `nonexistent`
- Invalid file: `src/nonexistent.py`
- Invalid directory: `src/nonexistent/dir`
- Code block:
```python
def hello():
    pass
```
- Duplicate symbol: `hello_duplicate`
- Another valid symbol: `Greeter`
- Another valid file: `docs/README.md`
"""
    result = add_links_to_message(message, codebase)

    # Valid symbols should be linked
    assert "|hello>" in result
    assert "|Greeter>" in result

    # Valid files should be linked
    assert "|src/main.py>" in result
    assert "|docs/README.md>" in result

    # Valid directories should be linked
    assert "|src/utils>" in result

    # Invalid symbols and files should remain as-is
    assert "`nonexistent`" in result
    assert "`src/nonexistent.py`" in result
    assert "`src/nonexistent/dir`" in result
    assert "`hello_duplicate`" in result

    # Code block should be preserved
    assert "```python" in result
    assert "def hello():" in result
