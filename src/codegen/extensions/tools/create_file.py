"""Tool for creating new files."""

from typing import ClassVar

from pydantic import Field

from codegen.sdk.core.codebase import Codebase

from .observation import Observation
from .view_file import ViewFileObservation, view_file


class CreateFileObservation(Observation):
    """Response from creating a new file."""

    filepath: str = Field(
        description="Path to the created file",
    )
    file_info: ViewFileObservation = Field(
        description="Information about the created file",
    )

    str_template: ClassVar[str] = "Created file {filepath}"


def create_file(codebase: Codebase, filepath: str, content: str) -> CreateFileObservation:
    """Create a new file.

    Args:
        codebase: The codebase to operate on
        filepath: Path where to create the file
        content: Content for the new file (required)

    Returns:
        CreateFileObservation containing new file state, or error if file exists
    """
    if codebase.has_file(filepath):
        return CreateFileObservation(
            status="error",
            error=f"File already exists: {filepath}, please use view_file to see the file content or realace_edit to edit it directly",
            filepath=filepath,
            file_info=ViewFileObservation(
                status="error",
                error=f"File already exists: {filepath}",
                filepath=filepath,
                content="",
                line_count=0,
            ),
        )

    try:
        file = codebase.create_file(filepath, content=content)
        codebase.commit()

        # Get file info using view_file
        file_info = view_file(codebase, filepath)

        return CreateFileObservation(
            status="success",
            filepath=filepath,
            file_info=file_info,
        )

    except Exception as e:
        return CreateFileObservation(
            status="error",
            error=f"Failed to create file: {e!s}",
            filepath=filepath,
            file_info=ViewFileObservation(
                status="error",
                error=f"Failed to create file: {e!s}",
                filepath=filepath,
                content="",
                line_count=0,
            ),
        )
