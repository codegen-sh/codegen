"""Tool for viewing file contents and metadata."""

from typing import Any

from codegen import Codebase


def view_file(codebase: Codebase, filepath: str) -> dict[str, Any]:
    """View the contents and metadata of a file.

    Args:
        codebase: The codebase to operate on
        filepath: Path to the file relative to workspace root

    Returns:
        Dict containing file contents and metadata, or error information if file not found
    """
    file = None

    try:
        file = codebase.get_file(filepath)
    except ValueError:
        pass

    if not file:
        return {"error": f"File not found: {filepath}. Please use full filepath relative to workspace root."}

    return {
        "filepath": file.filepath,
        "content": file.content,
    }
