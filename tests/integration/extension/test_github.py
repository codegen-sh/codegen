"""Tests for Linear tools."""

import os

import pytest

from codegen import Codebase
from codegen.extensions.linear.linear_client import LinearClient
from codegen.extensions.tools.github import view_pr


@pytest.fixture
def client() -> LinearClient:
    """Create a Linear client for testing."""
    token = os.getenv("CODEGEN_SECRETS__GITHUB_TOKEN")
    if not token:
        pytest.skip("CODEGEN_SECRETS__GITHUB_TOKEN environment variable not set")
    codebase = Codebase.from_repo("codegen-sh/Kevin-s-Adventure-Game")
    return codebase


def test_github_view_pr(client: LinearClient) -> None:
    """Test getting an issue from Linear."""
    # Link to PR: https://github.com/codegen-sh/Kevin-s-Adventure-Game/pull/419
    pr = view_pr(client, 419)
    print(pr)
