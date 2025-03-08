"""Tool for creating PR review comments."""

import json

from pydantic import Field

from codegen.sdk.core.codebase import Codebase

from ..observation import Observation


class PRCheckObservation(Observation):
    """Response from retrieving PR checks."""

    pr_number: int = Field(
        description="PR number that was viewed",
    )
    head_sha: str | None = Field(
        description="SHA of the head commit",
    )
    summary: str | None = Field(
        description="Summary of the checks",
    )


def view_pr_checks(codebase: Codebase, pr_number: int) -> PRCheckObservation:
    """Retrieve check information from a Github PR .

    Args:
        codebase: The codebase to operate on
        pr_number: The PR number to view checks on
    """
    try:
        pr = codebase.op.remote_git_repo.get_pull_safe(pr_number)
        if not pr:
            return PRCheckObservation(
                pr_number=pr_number,
                head_sha=None,
                summary=None,
            )
        commit = codebase.op.remote_git_repo.get_commit_safe(pr.head.sha)
        all_check_suites = commit.get_check_suites()
        return PRCheckObservation(
            pr_number=pr_number,
            head_sha=pr.head.sha,
            summary="\n".join([json.dumps(check_suite.raw_data) for check_suite in all_check_suites]),
        )

    except Exception as e:
        return PRCheckObservation(
            pr_number=pr_number,
            head_sha=None,
            summary=None,
        )
