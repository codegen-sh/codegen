"""Tests for GitHub tools."""

import os

import pytest

from codegen.extensions.tools.github import search, view_pr
from codegen.sdk.core.codebase import Codebase


@pytest.fixture
def codebase() -> Codebase:
    """Create a Codebase instance for testing."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        pytest.skip("GITHUB_TOKEN environment variable not set")
    codebase = Codebase.from_repo("codegen-sh/Kevin-s-Adventure-Game")
    return codebase


def test_github_view_pr(codebase: Codebase) -> None:
    """Test viewing a PR from GitHub."""
    # Link to PR: https://github.com/codegen-sh/Kevin-s-Adventure-Game/pull/419
    pr = view_pr(codebase, 419)
    print(pr)


def test_github_search_issues(codebase: Codebase) -> None:
    """Test searching GitHub issues."""
    # Search for closed issues with the 'bug' label
    result = search(codebase, query="is:issue is:closed")
    assert result.status == "success"
    assert len(result.results) > 0
    assert "is:issue is:closed" in result.query

    # Verify issue structure
    if result.results:
        issue = result.results[0]
        assert "title" in issue
        assert "number" in issue
        assert "state" in issue
        assert issue["state"] == "closed"
        assert not issue["is_pr"]  # Should be an issue, not a PR


def test_github_search_prs(codebase: Codebase) -> None:
    """Test searching GitHub pull requests."""
    # Search for merged PRs
    result = search(codebase, query="is:pr is:merged")
    assert result.status == "success"
    assert len(result.results) > 0
    assert "is:pr is:merged" in result.query

    # Verify PR structure
    if result.results:
        pr = result.results[0]
        assert "title" in pr
        assert "number" in pr
        assert "state" in pr
        assert pr["state"] == "closed"
        assert pr["is_pr"]  # Should be a PR
