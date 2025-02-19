"""Tool for creating PR review comments."""

from typing import Any, Optional

from codegen import Codebase


def create_pr_review_comment(
    codebase: Codebase,
    pr_number: int,
    body: str,
    commit_sha: str,
    path: str,
    line: Optional[int] = None,
    side: Optional[str] = None,
    start_line: Optional[int] = None,
) -> dict[str, Any]:
    """Create an inline review comment on a specific line in a pull request.

    Args:
        codebase: The codebase to operate on
        pr_number: The PR number to comment on
        body: The comment text
        commit_sha: The commit SHA to attach the comment to
        path: The file path to comment on
        line: The line number to comment on
        side: Which version of the file to comment on ('LEFT' or 'RIGHT')
        start_line: For multi-line comments, the starting line

    Returns:
        Dict containing comment status
    """
    try:
        codebase.create_pr_review_comment(
            pr_number=pr_number,
            body=body,
            commit_sha=commit_sha,
            path=path,
            line=line,
            side=side,
            start_line=start_line,
        )
        return {
            "status": "success",
            "message": "Review comment created successfully",
            "pr_number": pr_number,
            "path": path,
            "line": line,
        }
    except Exception as e:
        return {"error": f"Failed to create PR review comment: {e!s}"}
