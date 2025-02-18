"""Tool for viewing PR contents and modified symbols."""

from typing import Any

from codegen import Codebase


def view_pr(codebase: Codebase, pr_id: int) -> dict[str, Any]:
    """Get the diff and modified symbols of a PR.

    Args:
        codebase: The codebase to operate on
        pr_id: Number of the PR to get the contents for

    Returns:
        Dict containing modified symbols and patch
    """
    modified_symbols, patch = codebase.get_modified_symbols_in_pr(pr_id)

    # Convert modified_symbols set to list for JSON serialization
    return {"status": "success", "patch": patch}
