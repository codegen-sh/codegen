"""Tests for web browsing tools."""

import pytest
import responses

from codegen.extensions.tools.web import web_search_tool, web_view_page_tool


@pytest.fixture
def mock_responses():
    """Set up mock responses for testing."""
    with responses.RequestsMock() as rsps:
        # Mock a web page response
        rsps.add(
            responses.GET,
            "https://example.com",
            body="<html><head><title>Example Domain</title></head><body><h1>Example Domain</h1><p>This is a test page.</p></body></html>",
            status=200,
            content_type="text/html",
        )
        yield rsps


def test_web_search_tool():
    """Test the web search tool."""
    # Since this is a mock implementation, we just test the basic functionality
    result = web_search_tool("test query", num_results=3)

    assert result.status == "success"
    assert result.query == "test query"
    assert len(result.results) == 3

    # Check that the results have the expected structure
    for i, item in enumerate(result.results):
        assert item["title"] == f"Result {i + 1} for test query"
        assert item["url"] == f"https://example.com/result{i + 1}"
        assert "snippet" in item


def test_web_view_page_tool(mock_responses):
    """Test the web view page tool."""
    result = web_view_page_tool("https://example.com")

    assert result.status == "success"
    assert result.url == "https://example.com"
    assert result.title == "Example Domain"
    assert "Example Domain" in result.content
    assert "This is a test page." in result.content


def test_web_view_page_tool_error():
    """Test the web view page tool with an error."""
    result = web_view_page_tool("https://nonexistent-domain-that-should-fail.com")

    assert result.status == "error"
    assert "error" in result
    assert result.url == "https://nonexistent-domain-that-should-fail.com"
    assert result.title == ""
    assert result.content == ""
