"""Tool for creating PR comments."""

from typing import Any

from codegen import Codebase


def create_pr_comment(codebase: Codebase, pr_number: int, body: str) -> dict[str, Any]:
    """Create a general comment on a pull request.

    Args:
        codebase: The codebase to operate on
        pr_number: The PR number to comment on
        body: The comment text

    Returns:
        Dict containing comment status
    """
    try:
        codebase.create_pr_comment(pr_number=pr_number, body=body)
        return {
            "status": "success",
            "message": "Comment created successfully",
            "pr_number": pr_number,
        }
    except Exception as e:
        return {"error": f"Failed to create PR comment: {e!s}"}
