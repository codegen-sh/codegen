"""Tool for listing directory contents."""

from typing import Any

from codegen import Codebase
from codegen.sdk.core.directory import Directory


def list_directory(codebase: Codebase, dirpath: str = "./", depth: int = 1) -> dict[str, Any]:
    """List contents of a directory.

    Args:
        codebase: The codebase to operate on
        dirpath: Path to directory relative to workspace root
        depth: How deep to traverse the directory tree. Default is 1 (immediate children only).
               Use -1 for unlimited depth.

    Returns:
        Dict containing directory contents and metadata in a nested structure:
        {
            "path": str,
            "name": str,
            "files": list[str],
            "subdirectories": [
                {
                    "path": str,
                    "name": str,
                    "files": list[str],
                    "subdirectories": [...],
                },
                ...
            ]
        }
    """
    try:
        directory = codebase.get_directory(dirpath)
    except ValueError:
        return {"error": f"Directory not found: {dirpath}"}

    if not directory:
        return {"error": f"Directory not found: {dirpath}"}

    def get_directory_info(dir_obj: Directory, current_depth: int) -> dict[str, Any]:
        """Helper function to get directory info recursively."""
        # Get direct files
        all_files = []
        for file in dir_obj.files:
            if file.directory == dir_obj:
                all_files.append(file.filepath.split("/")[-1])

        # Get direct subdirectories
        subdirs = []
        for subdir in dir_obj.subdirectories:
            # Only include direct descendants
            if subdir.parent == dir_obj:
                if current_depth != 1:
                    new_depth = current_depth - 1 if current_depth > 1 else -1
                    subdirs.append(get_directory_info(subdir, new_depth))
                else:
                    # At max depth, just include name
                    subdirs.append(subdir.name)
        return {
            "name": dir_obj.name,
            "path": dir_obj.dirpath,
            "files": all_files,
            "subdirectories": subdirs,
        }

    return get_directory_info(directory, depth)
