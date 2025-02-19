"""Tool for making semantic edits to files using a small, fast LLM."""

import difflib
import re

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate

from codegen import Codebase

from .semantic_edit_prompts import _HUMAN_PROMPT_DRAFT_EDITOR, COMMANDER_SYSTEM_PROMPT
from .view_file import add_line_numbers


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
        raise ValueError("LLM response must contain code wrapped in ``` blocks. Got response: " + llm_response[:200] + "...")

    # Return the last code block exactly as is
    return matches[-1]


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


def _validate_edit_boundaries(original_lines: list[str], modified_lines: list[str], start_idx: int, end_idx: int) -> None:
    """Validate that the edit only modified lines within the specified boundaries.

    Args:
        original_lines: Original file lines
        modified_lines: Modified file lines
        start_idx: Starting line index (0-indexed)
        end_idx: Ending line index (0-indexed)

    Raises:
        ValueError: If changes were made outside the specified range
    """
    # Check lines before start_idx
    for i in range(start_idx):
        if i >= len(original_lines) or i >= len(modified_lines) or original_lines[i] != modified_lines[i]:
            msg = f"Edit modified line {i + 1} which is before the specified start line {start_idx + 1}"
            raise ValueError(msg)


def semantic_edit(codebase: Codebase, filepath: str, edit_content: str, start: int = 1, end: int = -1) -> dict[str, str]:
    """Edit a file using semantic editing with line range support. This is an internal api and should not be called by the LLM."""
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
        return {
            "error": (
                f"File is {len(original_lines)} lines long. For files longer than {MAX_LINES} lines, "
                "please specify a line range using start and end parameters. "
                "You may need to make multiple targeted edits."
            ),
            "status": "error",
            "line_count": len(original_lines),
        }

    # Handle append mode
    if start == -1 and end == -1:
        try:
            file.add_symbol_from_source(edit_content)
            codebase.commit()

            return {"filepath": filepath, "content": file.content, "diff": generate_diff(original_content, file.content), "status": "success"}
        except Exception as e:
            msg = f"Failed to append content: {e!s}"
            raise ValueError(msg)

    # For range edits, get the context for the draft editor
    total_lines = len(original_lines)
    start_idx = start - 1
    end_idx = end - 1 if end != -1 else total_lines

    # Get the context for the edit
    context_lines = original_lines[start_idx : end_idx + 1]
    original_file_section = "\n".join(context_lines)

    # =====[ Get the LLM ]=====
    system_message = COMMANDER_SYSTEM_PROMPT
    human_message = _HUMAN_PROMPT_DRAFT_EDITOR
    prompt = ChatPromptTemplate.from_messages([system_message, human_message])
    llm = ChatAnthropic(
        model="claude-3-5-sonnet-latest",
        temperature=0,
        max_tokens=5000,
    )
    chain = prompt | llm
    response = chain.invoke({"original_file_section": original_file_section, "edit_content": edit_content})

    # Extract code from markdown code block
    try:
        modified_segment = _extract_code_block(response.content)
    except ValueError as e:
        msg = f"Failed to parse LLM response: {e!s}"
        raise ValueError(msg)

    # Merge the edited content with the original
    new_content = _merge_content(original_content, modified_segment, start, end)
    new_lines = new_content.splitlines()

    # Validate that no changes were made before the start line
    _validate_edit_boundaries(original_lines, new_lines, start_idx, end_idx)

    # Generate diff
    diff = generate_diff(original_content, new_content)

    # Apply the edit
    file.edit(new_content)
    codebase.commit()

    return {"filepath": filepath, "diff": diff, "status": "success", "new_content": add_line_numbers(new_content)}
