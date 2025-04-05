"""Tool for creating pull requests."""

import uuid
from typing import ClassVar

from github import GithubException
from pydantic import Field

from codegen.sdk.core.codebase import Codebase

from ..observation import Observation


class CreatePRObservation(Observation):
    """Response from creating a pull request."""

    url: str = Field(
        description="URL of the created PR",
    )
    number: int = Field(
        description="PR number",
    )
    title: str = Field(
        description="Title of the PR",
    )

    str_template: ClassVar[str] = "Created PR #{number}: {title}"


def create_pr(codebase: Codebase, title: str, body: str) -> CreatePRObservation:
    """Create a PR for the current branch.

    Args:
        codebase: The codebase to operate on
        title: The title of the PR
        body: The body/description of the PR
    """
    try:
        # Check for uncommitted changes and commit them
        if len(codebase.get_diff()) == 0:
            return CreatePRObservation(
                status="error",
                error="No changes to create a PR.",
                url="",
                number=0,
                title=title,
            )

        # TODO: this is very jank. We should ideally check out the branch before
        # making the changes, but it looks like `codebase.checkout` blows away
        # all of your changes
        codebase.git_commit(".")

        # If on default branch, create a new branch
        if codebase._op.git_cli.active_branch.name == codebase._op.default_branch:
            codebase.checkout(branch=f"{uuid.uuid4()}", create_if_missing=True)

        # Create the PR
        try:
            pr = codebase.create_pr(title=title, body=body)
        except GithubException as e:
            return CreatePRObservation(
                status="error",
                error="Failed to create PR. Check if the PR already exists.",
                url="",
                number=0,
                title=title,
            )

        return CreatePRObservation(
            status="success",
            url=pr.html_url,
            number=pr.number,
            title=pr.title,
        )

    except Exception as e:
        return CreatePRObservation(
            status="error",
            error=f"Failed to create PR: {e!s}",
            url="",
            number=0,
            title=title,
        )
