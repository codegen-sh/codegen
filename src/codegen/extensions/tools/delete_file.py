"""Tool for deleting files."""

from typing import Any

from codegen import Codebase


def delete_file(codebase: Codebase, filepath: str) -> dict[str, Any]:
    """Delete a file.

    Args:
        codebase: The codebase to operate on
        filepath: Path to the file to delete

    Returns:
        Dict containing deletion status, or error information if file not found
    """
    try:
        file = codebase.get_file(filepath)
    except ValueError:
        return {"error": f"File not found: {filepath}"}
    if file is None:
        return {"error": f"File not found: {filepath}"}

    file.remove()
    codebase.commit()
    return {"status": "success", "deleted_file": filepath}
