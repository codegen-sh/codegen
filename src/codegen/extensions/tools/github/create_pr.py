"""Tool for creating pull requests."""

import re
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
    changes_summary: str = Field(
        description="Summary of changes included in the PR",
        default="",
    )

    str_template: ClassVar[str] = "Created PR #{number}: {title}\n\nChanges Summary:\n{changes_summary}"


def generate_changes_summary(diff_text: str) -> str:
    """Generate a human-readable summary of changes from a git diff.

    Args:
        diff_text: The git diff text

    Returns:
        A formatted summary of the changes
    """
    if not diff_text:
        return "No changes detected."

    # Parse the diff to extract file information
    file_pattern = re.compile(r"diff --git a/(.*?) b/(.*?)\n")
    file_matches = file_pattern.findall(diff_text)

    # Count additions and deletions
    addition_pattern = re.compile(r"^\+[^+]", re.MULTILINE)
    deletion_pattern = re.compile(r"^-[^-]", re.MULTILINE)

    additions = len(addition_pattern.findall(diff_text))
    deletions = len(deletion_pattern.findall(diff_text))

    # Get unique files changed
    files_changed = set()
    for match in file_matches:
        # Use the second part of the match (b/file) as it represents the new file
        files_changed.add(match[1])

    # Group files by extension
    file_extensions: dict[str, list[str]] = {}
    for file in files_changed:
        ext = file.split(".")[-1] if "." in file else "other"
        if ext not in file_extensions:
            file_extensions[ext] = []
        file_extensions[ext].append(file)

    # Build the summary
    summary = []
    summary.append(f"**Files Changed:** {len(files_changed)}")
    summary.append(f"**Lines Added:** {additions}")
    summary.append(f"**Lines Deleted:** {deletions}")

    # Add file details grouped by extension
    if file_extensions:
        summary.append("\n**Modified Files:**")
        for ext, files in file_extensions.items():
            summary.append(f"\n*{ext.upper()} Files:*")
            for file in sorted(files):
                summary.append(f"- {file}")

    return "\n".join(summary)


def create_pr(codebase: Codebase, title: str, body: str) -> CreatePRObservation:
    """Create a PR for the current branch.

    Args:
        codebase: The codebase to operate on
        title: The title of the PR
        body: The body/description of the PR
    """
    try:
        # Check for uncommitted changes and commit them
        diff_text = codebase.get_diff()
        if len(diff_text) == 0:
            return CreatePRObservation(
                status="error",
                error="No changes to create a PR.",
                url="",
                number=0,
                title=title,
                changes_summary="",
            )

        # Generate a summary of changes
        changes_summary = generate_changes_summary(diff_text)

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
                changes_summary="",
            )

        return CreatePRObservation(
            status="success",
            url=pr.html_url,
            number=pr.number,
            title=pr.title,
            changes_summary=changes_summary,
        )

    except Exception as e:
        return CreatePRObservation(
            status="error",
            error=f"Failed to create PR: {e!s}",
            url="",
            number=0,
            title=title,
            changes_summary="",
        )
