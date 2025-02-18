"""Tool for creating pull requests."""

import uuid
from typing import Any

from github import GithubException

from codegen import Codebase


def create_pr(codebase: Codebase, title: str, body: str) -> dict[str, Any]:
    """Create a PR for the current branch.

    Args:
        codebase: The codebase to operate on
        title: The title of the PR
        body: The body/description of the PR

    Returns:
        Dict containing PR info, or error information if operation fails
    """
    try:
        # Check for uncommitted changes and commit them
        if len(codebase.get_diff()) == 0:
            return {"error": "No changes to create a PR."}

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
            print(e)
            return {"error": "Failed to create PR. Check if the PR already exists."}
        return {
            "status": "success",
            "url": pr.html_url,
            "number": pr.number,
            "title": pr.title,
        }
    except Exception as e:
        return {"error": f"Failed to create PR: {e!s}"}
