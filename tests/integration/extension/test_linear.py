"""Tests for Linear tools."""

import os

import pytest

from codegen.extensions.linear.linear_client import LinearClient
from codegen.extensions.tools.linear_tools import (
    linear_comment_on_issue_tool,
    linear_get_issue_comments_tool,
    linear_get_issue_tool,
)


@pytest.fixture
def client() -> LinearClient:
    """Create a Linear client for testing."""
    token = os.getenv("LINEAR_ACCESS_TOKEN")
    if not token:
        pytest.skip("LINEAR_ACCESS_TOKEN environment variable not set")
    return LinearClient(token)


def test_linear_get_issue(client: LinearClient) -> None:
    """Test getting an issue from Linear."""
    # Link to issue: https://linear.app/codegen-sh/issue/CG-10775/read-file-and-reveal-symbol-tool-size-limits
    issue = linear_get_issue_tool(client, "CG-10775")
    assert issue["status"] == "success"
    assert issue["issue"]["id"] == "d5a7d6db-e20d-4d67-98f8-acedef6d3536"


def test_linear_get_issue_comments(client: LinearClient) -> None:
    """Test getting comments for an issue from Linear."""
    comments = linear_get_issue_comments_tool(client, "CG-10775")
    assert comments["status"] == "success"
    assert len(comments["comments"]) > 1


def test_linear_comment_on_issue(client: LinearClient) -> None:
    """Test commenting on a Linear issue."""
    test_comment = "Test comment from automated testing"
    result = linear_comment_on_issue_tool(client, "CG-10775", test_comment)
    assert result["status"] == "success"


def test_search_issues(client: LinearClient) -> None:
    """Test searching for issues in Linear."""
    issues = client.search_issues("REVEAL_SYMBOL")
    assert issues["status"] == "success"
    assert len(issues["issues"]) > 0
