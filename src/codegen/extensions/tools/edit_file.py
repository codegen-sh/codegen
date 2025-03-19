"""Tool for editing file contents."""

from typing import TYPE_CHECKING, ClassVar, Optional

from langchain_core.messages import ToolMessage
from pydantic import Field

from codegen.sdk.core.codebase import Codebase

from .observation import Observation
from .replacement_edit import generate_diff

if TYPE_CHECKING:
    from .tool_output_types import EditFileArtifacts


class EditFileObservation(Observation):
    """Response from editing a file."""

    filepath: str = Field(
        description="Path to the edited file",
    )
    diff: Optional[str] = Field(
        default=None,
        description="Unified diff showing the changes made",
    )

    str_template: ClassVar[str] = "Edited file {filepath}"

    def render(self, tool_call_id: str) -> ToolMessage:
        """Render edit results in a clean format."""
        if self.status == "error":
            artifacts_error: EditFileArtifacts = {"filepath": self.filepath, "error": self.error}
            return ToolMessage(
                content=f"[ERROR EDITING FILE]: {self.filepath}: {self.error}",
                status=self.status,
                name="edit_file",
                artifact=artifacts_error,
                tool_call_id=tool_call_id,
            )

        artifacts_success: EditFileArtifacts = {"filepath": self.filepath, "diff": self.diff}

        return ToolMessage(
            content=f"""[EDIT FILE]: {self.filepath}\n\n{self.diff}""",
            status=self.status,
            name="edit_file",
            artifact=artifacts_success,
            tool_call_id=tool_call_id,
        )


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
