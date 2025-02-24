"""Tool for creating PR review comments."""

from typing import ClassVar, Optional

from pydantic import Field

from codegen.sdk.core.codebase import Codebase

from ..observation import Observation


class PRReviewCommentObservation(Observation):
    """Response from creating a PR review comment."""

    pr_number: int = Field(
        description="PR number the comment was added to",
    )
    body: str = Field(
        description="Content of the comment",
    )
    commit_sha: str = Field(
        description="Commit SHA the comment was added to",
    )
    path: str = Field(
        description="File path the comment was added to",
    )
    line: int = Field(
        description="Line number the comment was added to",
    )
    str_template: ClassVar[str] = "Added review comment to PR #{pr_number} at {path}:{line}"


def create_pr_review_comment(
    codebase: Codebase,
    pr_number: int,
    body: str,
    commit_sha: str,
    path: str,
    line: int,
    start_line: Optional[int] = None,
) -> PRReviewCommentObservation:
    """Create an inline review comment on a specific line in a pull request.

    Args:
        codebase: The codebase to operate on
        pr_number: The PR number to comment on
        body: The comment text
        commit_sha: The commit SHA to attach the comment to
        path: The file path to comment on
        line: The line number to comment on
    """
    try:
        codebase.create_pr_review_comment(
            pr_number=pr_number,
            body=body,
            commit_sha=commit_sha,
            path=path,
            line=line,
            side="RIGHT",
        )
        return PRReviewCommentObservation(
            status="success",
            pr_number=pr_number,
            path=path,
            line=line,
            body=body,
            commit_sha=commit_sha,
        )
    except Exception as e:
        return PRReviewCommentObservation(
            status="error",
            error=f"Failed to create PR review comment: {e!s}",
            pr_number=pr_number,
            path=path,
            line=line,
            body=body,
            commit_sha=commit_sha,
        )
