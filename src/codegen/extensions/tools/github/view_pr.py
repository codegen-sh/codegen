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
    repo_name: str = Field(
        description="Name of the repository containing the PR",
    )
    pr_url: str = Field(
        description="URL of the PR",
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

    str_template: ClassVar[str] = "PR #{pr_id} in {repo_name}"


def view_pr(codebase: Codebase, pr_id: int) -> ViewPRObservation:
    """Get the diff and modified symbols of a PR.

    Args:
        codebase: The codebase to operate on
        pr_id: Number of the PR to get the contents for
    """
    try:
        patch, file_commit_sha, modified_symbols = codebase.get_modified_symbols_in_pr(pr_id)

        # Get the PR object to extract URL and repository name
        pr = codebase.op.remote_git_repo.get_pull(pr_id)
        repo_name = codebase.op.remote_git_repo.repo.full_name
        pr_url = pr.html_url

        return ViewPRObservation(
            status="success",
            pr_id=pr_id,
            repo_name=repo_name,
            pr_url=pr_url,
            patch=patch,
            file_commit_sha=file_commit_sha,
            modified_symbols=modified_symbols,
        )

    except Exception as e:
        return ViewPRObservation(
            status="error",
            error=f"Failed to view PR: {e!s}",
            pr_id=pr_id,
            repo_name="",
            pr_url="",
            patch="",
            file_commit_sha={},
            modified_symbols=[],
        )
