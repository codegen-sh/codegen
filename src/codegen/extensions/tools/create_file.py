"""Tool for creating new files."""

from typing import Any

from codegen import Codebase

from .view_file import view_file


def create_file(codebase: Codebase, filepath: str, content: str = "") -> dict[str, Any]:
    """Create a new file.

    Args:
        codebase: The codebase to operate on
        filepath: Path where to create the file
        content: Initial file content

    Returns:
        Dict containing new file state, or error information if file already exists
    """
    if codebase.has_file(filepath):
        return {"error": f"File already exists: {filepath}"}
    file = codebase.create_file(filepath, content=content)
    codebase.commit()
    return view_file(codebase, filepath)
