"""Tool for viewing file contents and metadata."""

from typing import ClassVar, Optional

from pydantic import Field

from codegen.sdk.core.codebase import Codebase

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
    start_line: Optional[int] = Field(
        default=None,
        description="Starting line number of the content (1-indexed)",
    )
    end_line: Optional[int] = Field(
        default=None,
        description="Ending line number of the content (1-indexed)",
    )
    has_more: Optional[bool] = Field(
        default=None,
        description="Whether there are more lines after end_line",
    )
    max_lines_per_page: Optional[int] = Field(
        default=None,
        description="Maximum number of lines that can be viewed at once",
    )

    str_template: ClassVar[str] = "File {filepath} (showing lines {start_line}-{end_line} of {line_count})"

    def render(self) -> str:
        """Render the file view with pagination information if applicable."""
        header = f"[VIEW FILE]: {self.filepath}"
        if self.line_count is not None:
            header += f" ({self.line_count} lines total)"

        if self.start_line is not None and self.end_line is not None:
            header += f"\nShowing lines {self.start_line}-{self.end_line}"
            if self.has_more:
                header += f" (more lines available, max {self.max_lines_per_page} lines per page)"

        if not self.content:
            return f"{header}\n<empty content>"

        return f"{header}\n\n{self.content}"


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


def view_file(
    codebase: Codebase,
    filepath: str,
    line_numbers: bool = True,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None,
    max_lines: int = 250,
) -> ViewFileObservation:
    """View the contents and metadata of a file.

    Args:
        codebase: The codebase to operate on
        filepath: Path to the file relative to workspace root
        line_numbers: If True, add line numbers to the content (1-indexed)
        start_line: Starting line number to view (1-indexed, inclusive)
        end_line: Ending line number to view (1-indexed, inclusive)
        max_lines: Maximum number of lines to view at once, defaults to 250
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
            start_line=start_line,
            end_line=end_line,
            has_more=False,
            max_lines_per_page=max_lines,
        )

    # Split content into lines and get total line count
    lines = file.content.splitlines()
    total_lines = len(lines)

    # If no start_line specified, start from beginning
    if start_line is None:
        start_line = 1

    # Ensure start_line is within bounds
    start_line = max(1, min(start_line, total_lines))

    # If no end_line specified, show up to max_lines from start
    if end_line is None:
        end_line = min(start_line + max_lines - 1, total_lines)
    else:
        # Ensure end_line is within bounds and doesn't exceed max_lines from start
        end_line = min(end_line, total_lines, start_line + max_lines - 1)

    # Extract the requested lines (convert to 0-based indexing)
    content_lines = lines[start_line - 1 : end_line]
    content = "\n".join(content_lines)

    # Add line numbers if requested
    if line_numbers:
        # Pass the actual line numbers for proper numbering
        numbered_lines = []
        width = len(str(total_lines))  # Use total_lines for consistent width
        for i, line in enumerate(content_lines, start=start_line):
            numbered_lines.append(f"{i:>{width}}|{line}")
        content = "\n".join(numbered_lines)

    # Create base observation with common fields
    observation = ViewFileObservation(
        status="success",
        filepath=file.filepath,
        content=content,
        line_count=total_lines,
    )

    # Only include pagination fields if file exceeds max_lines
    if total_lines > max_lines:
        observation.start_line = start_line
        observation.end_line = end_line
        observation.has_more = end_line < total_lines
        observation.max_lines_per_page = max_lines

    return observation
