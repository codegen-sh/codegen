"""Tool for deleting files."""

from typing import ClassVar

from pydantic import Field

from codegen.sdk.core.codebase import Codebase

from .observation import Observation


class DeleteFileObservation(Observation):
    """Response from deleting a file."""

    filepath: str = Field(
        description="Path to the deleted file",
    )

    str_template: ClassVar[str] = "Deleted file {filepath}"


def delete_file(codebase: Codebase, filepath: str) -> DeleteFileObservation:
    """Delete a file.

    Args:
        codebase: The codebase to operate on
        filepath: Path to the file to delete

    Returns:
        DeleteFileObservation containing deletion status, or error if file not found
    """
    try:
        file = codebase.get_file(filepath)
    except ValueError:
        return DeleteFileObservation(
            status="error",
            error=f"File not found: {filepath}",
            filepath=filepath,
        )

    if file is None:
        return DeleteFileObservation(
            status="error",
            error=f"File not found: {filepath}",
            filepath=filepath,
        )

    try:
        file.remove()
        codebase.commit()
        return DeleteFileObservation(
            status="success",
            filepath=filepath,
        )
    except Exception as e:
        return DeleteFileObservation(
            status="error",
            error=f"Failed to delete file: {e!s}",
            filepath=filepath,
        )
