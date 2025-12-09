"""Integration tests for the reflection tool."""

from unittest.mock import MagicMock

import pytest

from codegen.extensions.tools.reflection import perform_reflection
from codegen.sdk.core.codebase import Codebase


@pytest.fixture
def mock_codebase():
    """Create a mock codebase for testing."""
    return MagicMock(spec=Codebase)


def test_perform_reflection(mock_codebase):
    """Test the reflection tool."""
    # Test with basic inputs
    result = perform_reflection(
        context_summary="Testing the reflection tool",
        findings_so_far="Found some interesting patterns",
        current_challenges="Need to improve test coverage",
        reflection_focus=None,
        codebase=mock_codebase,
    )

    # Verify the result structure
    assert result.status == "success"
    assert "reflection" in result.content
    assert "Testing the reflection tool" in result.content
    assert "Found some interesting patterns" in result.content
    assert "Need to improve test coverage" in result.content

    # Test with a specific reflection focus
    result = perform_reflection(
        context_summary="Testing the reflection tool",
        findings_so_far="Found some interesting patterns",
        current_challenges="Need to improve test coverage",
        reflection_focus="architecture",
        codebase=mock_codebase,
    )

    # Verify the result includes the focus
    assert result.status == "success"
    assert "reflection" in result.content
    assert "architecture" in result.content

    # Test with minimal inputs
    result = perform_reflection(
        context_summary="Minimal test",
        findings_so_far="Minimal findings",
        codebase=mock_codebase,
    )

    # Verify the result with minimal inputs
    assert result.status == "success"
    assert "reflection" in result.content
    assert "Minimal test" in result.content
    assert "Minimal findings" in result.content
