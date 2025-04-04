"""Tool for creating PR comments."""

from typing import ClassVar

from pydantic import Field

from codegen.sdk.core.codebase import Codebase

from ..observation import Observation


class PRCommentObservation(Observation):
    """Response from creating a PR comment."""

    pr_number: int = Field(
        description="PR number the comment was added to",
    )
    body: str = Field(
        description="Content of the comment",
    )

    str_template: ClassVar[str] = "Added comment to PR #{pr_number}"


def create_pr_comment(codebase: Codebase, pr_number: int, body: str) -> PRCommentObservation:
    """Create a general comment on a pull request.

    Args:
        codebase: The codebase to operate on
        pr_number: The PR number to comment on
        body: The comment text
    """
    try:
        codebase.create_pr_comment(pr_number=pr_number, body=body)
        return PRCommentObservation(
            status="success",
            pr_number=pr_number,
            body=body,
        )
    except Exception as e:
        return PRCommentObservation(
            status="error",
            error=f"Failed to create PR comment: {e!s}",
            pr_number=pr_number,
            body=body,
        )
