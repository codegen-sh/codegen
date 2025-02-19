"""Tool for renaming files and updating imports."""

from typing import Any

from codegen import Codebase

from .view_file import view_file


def rename_file(codebase: Codebase, filepath: str, new_filepath: str) -> dict[str, Any]:
    """Rename a file and update all imports to point to the new location.

    Args:
        codebase: The codebase to operate on
        filepath: Current path of the file relative to workspace root
        new_filepath: New path for the file relative to workspace root

    Returns:
        Dict containing rename status and new file info, or error information if file not found
    """
    try:
        file = codebase.get_file(filepath)
    except ValueError:
        return {"error": f"File not found: {filepath}"}
    if file is None:
        return {"error": f"File not found: {filepath}"}

    if codebase.has_file(new_filepath):
        return {"error": f"Destination file already exists: {new_filepath}"}

    try:
        file.update_filepath(new_filepath)
        codebase.commit()
        return {"status": "success", "old_filepath": filepath, "new_filepath": new_filepath, "file_info": view_file(codebase, new_filepath)}
    except Exception as e:
        return {"error": f"Failed to rename file: {e!s}"}
