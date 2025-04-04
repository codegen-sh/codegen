"""Tool for viewing PR contents and modified symbols."""

from pydantic import Field

from codegen.sdk.core.codebase import Codebase

from ..observation import Observation


class CheckoutPRObservation(Observation):
    """Response from checking out a PR."""

    pr_number: int = Field(
        description="PR number",
    )
    success: bool = Field(
        description="Whether the checkout was successful",
        default=False,
    )


def checkout_pr(codebase: Codebase, pr_number: int) -> CheckoutPRObservation:
    """Checkout a PR.

    Args:
        codebase: The codebase to operate on
        pr_number: Number of the PR to get the contents for
    """
    try:
        pr = codebase.op.remote_git_repo.get_pull_safe(pr_number)
        if not pr:
            return CheckoutPRObservation(
                pr_number=pr_number,
                success=False,
            )

        codebase.checkout(branch=pr.head.ref)
        return CheckoutPRObservation(
            pr_number=pr_number,
            success=True,
        )
    except Exception as e:
        return CheckoutPRObservation(
            pr_number=pr_number,
            success=False,
            error=f"Failed to checkout PR: {e!s}",
        )
