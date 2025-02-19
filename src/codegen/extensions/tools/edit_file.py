"""Tool for editing file contents."""

from typing import ClassVar

from pydantic import Field

from codegen import Codebase

from .observation import Observation
from .view_file import ViewFileObservation, view_file


class EditFileObservation(Observation):
    """Response from editing a file."""

    filepath: str = Field(
        description="Path to the edited file",
    )
    file_info: ViewFileObservation = Field(
        description="Information about the edited file",
    )

    str_template: ClassVar[str] = "Edited file {filepath}"


def edit_file(codebase: Codebase, filepath: str, content: str) -> EditFileObservation:
    """Edit a file by replacing its entire content.

    Args:
        codebase: The codebase to operate on
        filepath: Path to the file to edit
        content: New content for the file

    Returns:
        EditFileObservation containing updated file state, or error if file not found
    """
    try:
        file = codebase.get_file(filepath)
    except ValueError:
        return EditFileObservation(
            status="error",
            error=f"File not found: {filepath}",
            filepath=filepath,
            file_info=ViewFileObservation(
                status="error",
                error=f"File not found: {filepath}",
                filepath=filepath,
                content="",
                line_count=0,
            ),
        )

    if file is None:
        return EditFileObservation(
            status="error",
            error=f"File not found: {filepath}",
            filepath=filepath,
            file_info=ViewFileObservation(
                status="error",
                error=f"File not found: {filepath}",
                filepath=filepath,
                content="",
                line_count=0,
            ),
        )

    try:
        file.edit(content)
        codebase.commit()

        # Get updated file info using view_file
        file_info = view_file(codebase, filepath)

        return EditFileObservation(
            status="success",
            filepath=filepath,
            file_info=file_info,
        )

    except Exception as e:
        return EditFileObservation(
            status="error",
            error=f"Failed to edit file: {e!s}",
            filepath=filepath,
            file_info=ViewFileObservation(
                status="error",
                error=f"Failed to edit file: {e!s}",
                filepath=filepath,
                content="",
                line_count=0,
            ),
        )
