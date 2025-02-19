"""Tool for viewing file contents and metadata."""

from typing import ClassVar, Optional

from pydantic import Field

from codegen import Codebase

from .observation import Observation


class ViewFileObservation(Observation):
    """Response from viewing a file."""

    filepath: str = Field(
        description="Path to the file",
    )
    content: str = Field(
        description="Content of the file",
    )
    line_count: Optional[int] = Field(
        default=None,
        description="Number of lines in the file",
    )

    str_template: ClassVar[str] = "File {filepath} ({line_count} lines)"


def add_line_numbers(content: str) -> str:
    """Add line numbers to content.

    Args:
        content: The text content to add line numbers to

    Returns:
        Content with line numbers prefixed (1-indexed)
    """
    lines = content.split("\n")
    width = len(str(len(lines)))
    return "\n".join(f"{i + 1:>{width}}|{line}" for i, line in enumerate(lines))


def view_file(codebase: Codebase, filepath: str, line_numbers: bool = True) -> ViewFileObservation:
    """View the contents and metadata of a file.

    Args:
        codebase: The codebase to operate on
        filepath: Path to the file relative to workspace root
        line_numbers: If True, add line numbers to the content (1-indexed)
    """
    try:
        file = codebase.get_file(filepath)
    except ValueError:
        return ViewFileObservation(
            status="error",
            error=f"File not found: {filepath}. Please use full filepath relative to workspace root.",
            filepath=filepath,
            content="",
            line_count=0,
        )

    content = file.content
    if line_numbers:
        content = add_line_numbers(content)

    return ViewFileObservation(
        status="success",
        filepath=file.filepath,
        content=content,
        line_count=len(content.splitlines()),
    )
