"""Tool for making regex-based replacements in files."""

import difflib
import re
from typing import ClassVar, Optional

from pydantic import Field

from codegen.sdk.core.codebase import Codebase

from .observation import Observation
from .view_file import add_line_numbers


class ReplacementEditObservation(Observation):
    """Response from making regex-based replacements in a file."""

    filepath: str = Field(
        description="Path to the edited file",
    )
    diff: Optional[str] = Field(
        default=None,
        description="Unified diff showing the changes made",
    )
    new_content: Optional[str] = Field(
        default=None,
        description="New content with line numbers",
    )
    message: Optional[str] = Field(
        default=None,
        description="Message describing the result",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if an error occurred",
    )
    error_pattern: Optional[str] = Field(
        default=None,
        description="Regex pattern that failed to compile",
    )

    str_template: ClassVar[str] = "{message}" if "{message}" else "Edited file {filepath}"


def generate_diff(original: str, modified: str) -> str:
    """Generate a unified diff between two strings.

    Args:
        original: Original content
        modified: Modified content

    Returns:
        Unified diff as a string
    """
    original_lines = original.splitlines(keepends=True)
    modified_lines = modified.splitlines(keepends=True)

    diff = difflib.unified_diff(
        original_lines,
        modified_lines,
        fromfile="original",
        tofile="modified",
        lineterm="",
    )

    return "".join(diff)


def _merge_content(original_content: str, edited_content: str, start: int, end: int) -> str:
    """Merge edited content with original content, preserving content outside the edit range.

    Args:
        original_content: Original file content
        edited_content: New content for the specified range
        start: Start line (1-indexed)
        end: End line (1-indexed or -1 for end of file)

    Returns:
        Merged content
    """
    original_lines = original_content.split("\n")
    edited_lines = edited_content.split("\n")

    if start == -1 and end == -1:  # Append mode
        return original_content + "\n" + edited_content

    # Convert to 0-indexed
    start_idx = start - 1
    end_idx = end - 1 if end != -1 else len(original_lines)

    # Merge the content
    result_lines = original_lines[:start_idx] + edited_lines + original_lines[end_idx + 1 :]

    return "\n".join(result_lines)


def replacement_edit(
    codebase: Codebase,
    filepath: str,
    pattern: str,
    replacement: str,
    start: int = 1,
    end: int = -1,
    count: Optional[int] = None,
    flags: re.RegexFlag = re.MULTILINE,
) -> ReplacementEditObservation:
    """Replace text in a file using regex pattern matching.

    Args:
        codebase: The codebase to operate on
        filepath: Path to the file to edit
        pattern: Regex pattern to match
        replacement: Replacement text (can include regex groups)
        start: Start line (1-indexed, default: 1)
        end: End line (1-indexed, -1 for end of file)
        count: Maximum number of replacements (None for all)
        flags: Regex flags (default: re.MULTILINE)

    Returns:
        ReplacementEditObservation containing edit results and status

    Raises:
        FileNotFoundError: If file not found
        ValueError: If invalid line range or regex pattern
    """
    try:
        file = codebase.get_file(filepath)
    except ValueError:
        msg = f"File not found: {filepath}"
        raise FileNotFoundError(msg)

    # Get the original content
    original_content = file.content
    original_lines = original_content.split("\n")

    # Get the section to edit
    total_lines = len(original_lines)
    start_idx = start - 1
    end_idx = end - 1 if end != -1 else total_lines

    # Get the content to edit
    section_lines = original_lines[start_idx : end_idx + 1]
    section_content = "\n".join(section_lines)

    try:
        # Compile pattern for better error messages
        regex = re.compile(pattern, flags)
    except re.error as e:
        return ReplacementEditObservation(
            status="error",
            error=f"Invalid regex pattern: {e!s}",
            error_pattern=pattern,
            filepath=filepath,
            message="Invalid regex pattern",
        )

    # Perform the replacement
    if count is None:
        new_section = regex.sub(replacement, section_content)
    else:
        new_section = regex.sub(replacement, section_content, count=count)

    # If no changes were made, return early
    if new_section == section_content:
        return ReplacementEditObservation(
            status="unchanged",
            message="No matches found for the given pattern",
            filepath=filepath,
        )

    # Merge the edited content with the original
    new_content = _merge_content(original_content, new_section, start, end)

    # Generate diff
    diff = generate_diff(original_content, new_content)

    # Apply the edit
    file.edit(new_content)
    codebase.commit()

    return ReplacementEditObservation(
        status="success",
        filepath=filepath,
        diff=diff,
        new_content=add_line_numbers(new_content),
    )
