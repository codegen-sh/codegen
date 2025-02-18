"""Tool for editing file contents."""

from typing import Any

from codegen import Codebase

from .view_file import view_file


def edit_file(codebase: Codebase, filepath: str, content: str) -> dict[str, Any]:
    """Edit a file by replacing its entire content.

    Args:
        codebase: The codebase to operate on
        filepath: Path to the file to edit
        content: New content for the file

    Returns:
        Dict containing updated file state, or error information if file not found
    """
    try:
        file = codebase.get_file(filepath)
    except ValueError:
        return {"error": f"File not found: {filepath}"}
    if file is None:
        return {"error": f"File not found: {filepath}"}

    file.edit(content)
    codebase.commit()
    return view_file(codebase, filepath)
