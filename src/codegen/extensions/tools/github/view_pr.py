"""Tool for viewing PR contents and modified symbols."""

from typing import ClassVar

from pydantic import Field

from codegen.sdk.core.codebase import Codebase

from ..observation import Observation


class ViewPRObservation(Observation):
    """Response from viewing a PR."""

    pr_id: int = Field(
        description="ID of the PR",
    )
    patch: str = Field(
        description="The PR's patch/diff content",
    )

    str_template: ClassVar[str] = "PR #{pr_id}"


def view_pr(codebase: Codebase, pr_id: int) -> ViewPRObservation:
    """Get the diff and modified symbols of a PR.

    Args:
        codebase: The codebase to operate on
        pr_id: Number of the PR to get the contents for
    """
    try:
        modified_symbols, patch = codebase.get_modified_symbols_in_pr(pr_id)

        return ViewPRObservation(
            status="success",
            pr_id=pr_id,
            patch=patch,
        )

    except Exception as e:
        return ViewPRObservation(
            status="error",
            error=f"Failed to view PR: {e!s}",
            pr_id=pr_id,
            patch="",
        )
