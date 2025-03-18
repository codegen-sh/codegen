"""Tool for making regex-based replacements in files."""

import difflib
import logging
import re
from typing import ClassVar

from pydantic import Field

from codegen.extensions.tools.search_files_by_name import search_files_by_name
from codegen.sdk.core.codebase import Codebase

from .observation import Observation

logger = logging.getLogger(__name__)


class GlobalReplacementEditObservation(Observation):
    """Response from making regex-based replacements in a file."""

    diff: str | None = Field(
        default=None,
        description="Unified diff showing the changes made. Only the first 5 file's changes are shown.",
    )
    message: str | None = Field(
        default=None,
        description="Message describing the result",
    )
    error: str | None = Field(
        default=None,
        description="Error message if an error occurred",
    )
    error_pattern: str | None = Field(
        default=None,
        description="Regex pattern that failed to compile",
    )

    str_template: ClassVar[str] = "{message}" if "{message}" else "Edited file {filepath}"


def generate_diff(original: str, modified: str, path: str) -> str:
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
        fromfile=path,
        tofile=path,
        lineterm="",
    )

    return "".join(diff)


def replacement_edit_global(
    codebase: Codebase,
    file_pattern: str,
    pattern: str,
    replacement: str,
    count: int | None = None,
    flags: re.RegexFlag = re.MULTILINE,
) -> GlobalReplacementEditObservation:
    """Replace text in a file using regex pattern matching.

    Args:
        codebase: The codebase to operate on
        file_pattern: Glob pattern to match files
        pattern: Regex pattern to match
        replacement: Replacement text (can include regex groups)
        count: Maximum number of replacements (None for all)
        flags: Regex flags (default: re.MULTILINE)

    Returns:
        GlobalReplacementEditObservation containing edit results and status

    Raises:
        FileNotFoundError: If file not found
        ValueError: If invalid regex pattern
    """
    logger.info(f"Replacing text in files matching {file_pattern} using regex pattern {pattern}")

    if count == 0:
        count = None
    try:
        # Compile pattern for better error messages
        regex = re.compile(pattern, flags)
    except re.error as e:
        return GlobalReplacementEditObservation(
            status="error",
            error=f"Invalid regex pattern: {e!s}",
            error_pattern=pattern,
            message="Invalid regex pattern",
        )

    diffs = []
    for file in search_files_by_name(codebase, file_pattern).files:
        if count is not None and count <= 0:
            break
        try:
            file = codebase.get_file(file)
        except ValueError:
            msg = f"File not found: {file}"
            raise FileNotFoundError(msg)
        content = file.content
        new_content, n = regex.subn(replacement, content, count=(count or 0))
        if count is not None:
            count -= n
        if n > 0:
            file.edit(new_content)
            if new_content != content:
                diff = generate_diff(content, new_content, file.filepath)
                diffs.append(diff)
    diff = "\n".join(diffs[:5])
    codebase.commit()
    return GlobalReplacementEditObservation(
        status="success",
        diff=diff,
        message=f"Successfully replaced text in files matching {file_pattern} using regex pattern {pattern}",
    )
