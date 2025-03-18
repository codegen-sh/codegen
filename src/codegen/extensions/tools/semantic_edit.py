"""Tool for making semantic edits to files using a small, fast LLM."""

import difflib
import re
from typing import ClassVar, Optional

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import Field

from codegen.extensions.langchain.llm import LLM
from codegen.sdk.core.codebase import Codebase

from .observation import Observation
from .semantic_edit_prompts import _HUMAN_PROMPT_DRAFT_EDITOR, COMMANDER_SYSTEM_PROMPT
from .view_file import add_line_numbers


class SemanticEditObservation(Observation):
    """Response from making semantic edits to a file."""

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
    line_count: Optional[int] = Field(
        default=None,
        description="Total number of lines in file",
    )

    str_template: ClassVar[str] = "Edited file {filepath}"


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


def _extract_code_block(llm_response: str) -> str:
    """Extract code from markdown code block in LLM response.

    Args:
        llm_response: Raw response from LLM

    Returns:
        Extracted code content exactly as it appears in the block

    Raises:
        ValueError: If response is not properly formatted with code blocks
    """
    # Find content between ``` markers, allowing for any language identifier
    pattern = r"```[^`\n]*\n?(.*?)```"
    matches = re.findall(pattern, llm_response.strip(), re.DOTALL)

    if not matches:
        msg = "LLM response must contain code wrapped in ``` blocks. Got response: " + llm_response[:200] + "..."
        raise ValueError(msg)

    # Return the last code block exactly as is
    return matches[-1]


def get_llm_edit(original_file_section: str, edit_content: str) -> str:
    """Get edited content from LLM.

    Args:
        original_file_section: Original content to edit
        edit_content: Edit specification/instructions

    Returns:
        LLM response with edited content
    """
    system_message = COMMANDER_SYSTEM_PROMPT
    human_message = _HUMAN_PROMPT_DRAFT_EDITOR
    prompt = ChatPromptTemplate.from_messages([system_message, human_message])

    llm = LLM(model_provider="anthropic", model_name="claude-3-5-sonnet-latest", temperature=0, max_tokens=5000)

    chain = prompt | llm | StrOutputParser()
    response = chain.invoke({"original_file_section": original_file_section, "edit_content": edit_content})

    return response


def _validate_edit_boundaries(original_lines: list[str], modified_lines: list[str], start_idx: int, end_idx: int) -> None:
    """Validate` that the edit only modified lines within the specified boundaries.

    Args:
        original_lines: Original file lines
        modified_lines: Modified file lines
        start_idx: Starting line index (0-indexed)
        end_idx: Ending line index (0-indexed)

    Raises:
        ValueError: If changes were made outside the specified range
    """
    # Check lines before start_idx
    for i in range(min(start_idx, len(original_lines), len(modified_lines))):
        if original_lines[i] != modified_lines[i]:
            msg = f"Edit modified line {i + 1} which is before the specified start line {start_idx + 1}"
            raise ValueError(msg)

    # Check lines after end_idx
    remaining_lines = len(original_lines) - (end_idx + 1)
    if remaining_lines > 0:
        orig_suffix = original_lines[-remaining_lines:]
        if len(modified_lines) >= remaining_lines:
            mod_suffix = modified_lines[-remaining_lines:]
            if orig_suffix != mod_suffix:
                msg = f"Edit modified content after the specified end line {end_idx + 1}"
                raise ValueError(msg)


def extract_file_window(file_content: str, start: int = 1, end: int = -1) -> tuple[str, int, int]:
    """Extract a window of content from a file.

    Args:
        file_content: Content of the file
        start: Start line (1-indexed, default: 1)
        end: End line (1-indexed or -1 for end of file, default: -1)

    Returns:
        Tuple of (extracted_content, start_idx, end_idx)
    """
    # Split into lines and handle line numbers
    lines = file_content.split("\n")
    total_lines = len(lines)

    # Convert to 0-indexed
    start_idx = start - 1
    end_idx = end - 1 if end != -1 else total_lines - 1

    # Get the content window
    window_lines = lines[start_idx : end_idx + 1]
    window_content = "\n".join(window_lines)

    return window_content, start_idx, end_idx


def apply_semantic_edit(codebase: Codebase, filepath: str, edited_content: str, start: int = 1, end: int = -1) -> tuple[str, str]:
    """Apply a semantic edit to a section of content.

    Args:
        codebase: Codebase object
        filepath: Path to the file to edit
        edited_content: New content for the specified range
        start: Start line (1-indexed, default: 1)
        end: End line (1-indexed or -1 for end of file, default: -1)

    Returns:
        Tuple of (new_content, diff)
    """
    # Get the original content
    file = codebase.get_file(filepath)
    original_content = file.content

    # Handle append mode
    if start == -1 and end == -1:
        new_content = original_content + "\n" + edited_content
        diff = generate_diff(original_content, new_content)
        file.edit(new_content)
        codebase.commit()
        return new_content, diff

    # Split content into lines
    original_lines = original_content.splitlines()
    edited_lines = edited_content.splitlines()

    # Convert to 0-indexed
    start_idx = start - 1
    end_idx = end - 1 if end != -1 else len(original_lines) - 1

    # Splice together: prefix + edited content + suffix
    new_lines = (
        original_lines[:start_idx]  # Prefix
        + edited_lines  # Edited section
        + original_lines[end_idx + 1 :]  # Suffix
    )

    # Preserve original file's newline if it had one
    new_content = "\n".join(new_lines) + ("\n" if original_content.endswith("\n") else "")
    # Validate the edit boundaries
    _validate_edit_boundaries(original_lines, new_lines, start_idx, end_idx)

    # Apply the edit
    file.edit(new_content)
    codebase.commit()
    with open(file.path, "w") as f:
        f.write(new_content)

    # Generate diff from the original section to the edited section
    original_section, _, _ = extract_file_window(original_content, start, end)
    diff = generate_diff(original_section, edited_content)

    return new_content, diff


def semantic_edit(codebase: Codebase, filepath: str, edit_content: str, start: int = 1, end: int = -1) -> SemanticEditObservation:
    """Edit a file using semantic editing with line range support."""
    try:
        file = codebase.get_file(filepath)
    except ValueError:
        msg = f"File not found: {filepath}"
        raise FileNotFoundError(msg)

    # Get the original content
    original_content = file.content
    original_lines = original_content.split("\n")

    # Check if file is too large for full edit
    MAX_LINES = 300
    if len(original_lines) > MAX_LINES and start == 1 and end == -1:
        return SemanticEditObservation(
            status="error",
            error=(
                f"File is {len(original_lines)} lines long. For files longer than {MAX_LINES} lines, "
                "please specify a line range using start and end parameters. "
                "You may need to make multiple targeted edits."
            ),
            filepath=filepath,
            line_count=len(original_lines),
        )

    # Extract the window of content to edit
    original_file_section, start_idx, end_idx = extract_file_window(original_content, start, end)

    # Get edited content from LLM
    try:
        modified_segment = _extract_code_block(get_llm_edit(original_file_section, edit_content))
    except ValueError as e:
        return SemanticEditObservation(
            status="error",
            error=f"Failed to parse LLM response: {e!s}",
            filepath=filepath,
        )

    # Apply the semantic edit
    try:
        new_content, diff = apply_semantic_edit(codebase, filepath, modified_segment, start, end)
    except ValueError as e:
        return SemanticEditObservation(
            status="error",
            error=str(e),
            filepath=filepath,
        )

    return SemanticEditObservation(
        status="success",
        filepath=filepath,
        diff=diff,
        new_content=add_line_numbers(new_content),
    )
