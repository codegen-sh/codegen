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
    file_commit_sha: dict[str, str] = Field(
        description="Commit SHAs for each file in the PR",
    )
    modified_symbols: list[str] = Field(
        description="Names of modified symbols in the PR",
    )
    pr_url: str = Field(
        description="URL of the PR",
        default="",
    )
    repo_name: str = Field(
        description="Name of the repository the PR belongs to",
        default="",
    )

    str_template: ClassVar[str] = "PR #{pr_id} in {repo_name}: {pr_url}"


def view_pr(codebase: Codebase, pr_id: int) -> ViewPRObservation:
    """Get the diff and modified symbols of a PR.

    Args:
        codebase: The codebase to operate on
        pr_id: Number of the PR to get the contents for
    """
    try:
        patch, file_commit_sha, moddified_symbols = codebase.get_modified_symbols_in_pr(pr_id)

        # Get the PR object to extract URL and repo name
        pr = codebase._op.get_pull_request(pr_id)
        pr_url = pr.html_url if pr else ""
        repo_name = codebase._op.repo_config.full_name if codebase._op.repo_config.full_name else ""

        return ViewPRObservation(
            status="success",
            pr_id=pr_id,
            patch=patch,
            file_commit_sha=file_commit_sha,
            modified_symbols=moddified_symbols,
            pr_url=pr_url,
            repo_name=repo_name,
        )

    except Exception as e:
        return ViewPRObservation(
            status="error",
            error=f"Failed to view PR: {e!s}",
            pr_id=pr_id,
            patch="",
            file_commit_sha={},
            modified_symbols=[],
            pr_url="",
            repo_name="",
        )
