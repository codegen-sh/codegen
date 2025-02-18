"""Tool for committing changes to disk."""

from typing import Any

from codegen import Codebase


def commit(codebase: Codebase) -> dict[str, Any]:
    """Commit any pending changes to disk.

    Args:
        codebase: The codebase to operate on

    Returns:
        Dict containing commit status
    """
    codebase.commit()
    return {"status": "success", "message": "Changes committed to disk"}
