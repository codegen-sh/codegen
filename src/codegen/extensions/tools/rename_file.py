"""Tool for renaming files and updating imports."""

from typing import ClassVar

from pydantic import Field

from codegen.sdk.core.codebase import Codebase

from .observation import Observation
from .view_file import ViewFileObservation, view_file


class RenameFileObservation(Observation):
    """Response from renaming a file."""

    old_filepath: str = Field(
        description="Original path of the file",
    )
    new_filepath: str = Field(
        description="New path of the file",
    )
    file_info: ViewFileObservation = Field(
        description="Information about the renamed file",
    )

    str_template: ClassVar[str] = "Renamed file from {old_filepath} to {new_filepath}"


def rename_file(codebase: Codebase, filepath: str, new_filepath: str) -> RenameFileObservation:
    """Rename a file and update all imports to point to the new location.

    Args:
        codebase: The codebase to operate on
        filepath: Current path of the file relative to workspace root
        new_filepath: New path for the file relative to workspace root

    Returns:
        RenameFileObservation containing rename status and new file info
    """
    try:
        file = codebase.get_file(filepath)
    except ValueError:
        return RenameFileObservation(
            status="error",
            error=f"File not found: {filepath}",
            old_filepath=filepath,
            new_filepath=new_filepath,
            file_info=ViewFileObservation(
                status="error",
                error=f"File not found: {filepath}",
                filepath=filepath,
                content="",
                line_count=0,
            ),
        )

    if codebase.has_file(new_filepath):
        return RenameFileObservation(
            status="error",
            error=f"Destination file already exists: {new_filepath}",
            old_filepath=filepath,
            new_filepath=new_filepath,
            file_info=ViewFileObservation(
                status="error",
                error=f"Destination file already exists: {new_filepath}",
                filepath=new_filepath,
                content="",
                line_count=0,
            ),
        )

    try:
        file.update_filepath(new_filepath)
        codebase.commit()

        return RenameFileObservation(
            status="success",
            old_filepath=filepath,
            new_filepath=new_filepath,
            file_info=view_file(codebase, new_filepath),
        )
    except Exception as e:
        return RenameFileObservation(
            status="error",
            error=f"Failed to rename file: {e!s}",
            old_filepath=filepath,
            new_filepath=new_filepath,
            file_info=ViewFileObservation(
                status="error",
                error=f"Failed to rename file: {e!s}",
                filepath=filepath,
                content="",
                line_count=0,
            ),
        )
