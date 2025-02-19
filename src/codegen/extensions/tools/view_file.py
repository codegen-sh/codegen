"""Tool for viewing file contents and metadata."""

from typing import Any

from codegen import Codebase


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


def view_file(codebase: Codebase, filepath: str, line_numbers: bool = True) -> dict[str, Any]:
    """View the contents and metadata of a file.

    Args:
        codebase: The codebase to operate on
        filepath: Path to the file relative to workspace root
        line_numbers: If True, add line numbers to the content (1-indexed)

    Returns:
        Dict containing file contents and metadata, or error information if file not found
    """
    file = None

    try:
        file = codebase.get_file(filepath)
    except ValueError:
        pass

    if not file:
        return {"error": f"File not found: {filepath}. Please use full filepath relative to workspace root."}

    content = file.content
    if line_numbers:
        content = add_line_numbers(content)

    return {
        "filepath": file.filepath,
        "content": content,
    }
