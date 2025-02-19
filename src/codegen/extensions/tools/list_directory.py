"""Tool for listing directory contents."""

from typing import ClassVar, Union

from pydantic import BaseModel, Field

from codegen import Codebase
from codegen.sdk.core.directory import Directory

from .observation import Observation


class DirectoryInfo(BaseModel):
    """Information about a directory."""

    name: str = Field(description="Name of the directory")
    path: str = Field(description="Full path to the directory")
    files: list[str] = Field(description="List of files in this directory")
    subdirectories: list[Union[str, "DirectoryInfo"]] = Field(
        description="List of subdirectories (either names or full DirectoryInfo objects depending on depth)",
    )


class ListDirectoryObservation(Observation):
    """Response from listing directory contents."""

    path: str = Field(description="Path to the listed directory")
    directory_info: DirectoryInfo = Field(description="Information about the directory and its contents")
    depth: int = Field(description="How deep the directory traversal went")

    str_template: ClassVar[str] = "Listed contents of {path} (depth={depth})"


def list_directory(codebase: Codebase, dirpath: str = "./", depth: int = 1) -> ListDirectoryObservation:
    """List contents of a directory.

    Args:
        codebase: The codebase to operate on
        dirpath: Path to directory relative to workspace root
        depth: How deep to traverse the directory tree. Default is 1 (immediate children only).
               Use -1 for unlimited depth.

    Returns:
        ListDirectoryObservation containing directory contents and metadata
    """
    try:
        directory = codebase.get_directory(dirpath)
    except ValueError:
        return ListDirectoryObservation(
            status="error",
            error=f"Directory not found: {dirpath}",
            path=dirpath,
            directory_info=DirectoryInfo(
                name="",
                path=dirpath,
                files=[],
                subdirectories=[],
            ),
            depth=depth,
        )

    if not directory:
        return ListDirectoryObservation(
            status="error",
            error=f"Directory not found: {dirpath}",
            path=dirpath,
            directory_info=DirectoryInfo(
                name="",
                path=dirpath,
                files=[],
                subdirectories=[],
            ),
            depth=depth,
        )

    def get_directory_info(dir_obj: Directory, current_depth: int) -> DirectoryInfo:
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

        return DirectoryInfo(
            name=dir_obj.name,
            path=dir_obj.dirpath,
            files=all_files,
            subdirectories=subdirs,
        )

    try:
        directory_info = get_directory_info(directory, depth)
        return ListDirectoryObservation(
            status="success",
            path=dirpath,
            directory_info=directory_info,
            depth=depth,
        )
    except Exception as e:
        return ListDirectoryObservation(
            status="error",
            error=f"Failed to list directory: {e!s}",
            path=dirpath,
            directory_info=DirectoryInfo(
                name="",
                path=dirpath,
                files=[],
                subdirectories=[],
            ),
            depth=depth,
        )
