"""Tool for editing file contents."""

from typing import ClassVar

from pydantic import Field

from codegen.sdk.core.codebase import Codebase

from .observation import Observation
from .replacement_edit import generate_diff


class EditFileObservation(Observation):
    """Response from editing a file."""

    filepath: str = Field(
        description="Path to the edited file",
    )
    diff: str = Field(
        description="Unified diff showing the changes made",
    )

    str_template: ClassVar[str] = "Edited file {filepath}"

    def render(self) -> str:
        """Render edit results in a clean format."""
        return f"""[EDIT FILE]: {self.filepath}

{self.diff}"""


def edit_file(codebase: Codebase, filepath: str, new_content: str) -> EditFileObservation:
    """Edit the contents of a file.

    Args:
        codebase: The codebase to operate on
        filepath: Path to the file relative to workspace root
        new_content: New content for the file
    """
    try:
        file = codebase.get_file(filepath)
    except ValueError:
        return EditFileObservation(
            status="error",
            error=f"File not found: {filepath}",
            filepath=filepath,
            diff="",
        )

    # Generate diff before making changes
    diff = generate_diff(file.content, new_content)

    # Apply the edit
    file.edit(new_content)
    codebase.commit()

    return EditFileObservation(
        status="success",
        filepath=filepath,
        diff=diff,
    )
