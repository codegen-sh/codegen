"""Tool for making edits to files using the Relace Instant Apply API."""

import difflib
import os
from typing import TYPE_CHECKING, ClassVar

import requests
from langchain_core.messages import ToolMessage
from pydantic import Field

from codegen.sdk.core.codebase import Codebase

from .observation import Observation
from .view_file import add_line_numbers

if TYPE_CHECKING:
    from codegen.extensions.tools.tool_output_types import RelaceEditArtifacts


class RelaceEditObservation(Observation):
    """Response from making edits to a file using Relace Instant Apply API."""

    filepath: str = Field(
        description="Path to the edited file",
    )
    diff: str | None = Field(
        default=None,
        description="Unified diff showing the changes made",
    )
    new_content: str | None = Field(
        default=None,
        description="New content with line numbers",
    )
    line_count: int | None = Field(
        default=None,
        description="Total number of lines in file",
    )

    str_template: ClassVar[str] = "Edited file {filepath} using Relace Instant Apply"

    def render(self, tool_call_id: str) -> ToolMessage:
        """Render the relace edit observation as a ToolMessage."""
        artifacts: RelaceEditArtifacts = {
            "filepath": self.filepath,
            "diff": self.diff,
            "new_content": self.new_content,
            "line_count": self.line_count,
            "error": self.error,
        }

        if self.status == "error":
            return ToolMessage(
                content=f"[ERROR EDITING FILE]: {self.filepath}: {self.error}",
                status=self.status,
                name="relace_edit",
                artifact=artifacts,
                tool_call_id=tool_call_id,
            )

        return ToolMessage(
            content=self.render_as_string(),
            status=self.status,
            name="relace_edit",
            tool_call_id=tool_call_id,
            artifact=artifacts,
        )


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


def get_relace_api_key() -> str:
    """Get the Relace API key from environment variables.

    Returns:
        The Relace API key

    Raises:
        ValueError: If the API key is not found
    """
    api_key = os.environ.get("RELACE_API")
    if not api_key:
        msg = "RELACE_API environment variable not found. Please set it in your .env file."
        raise ValueError(msg)
    return api_key


def apply_relace_edit(api_key: str, initial_code: str, edit_snippet: str, stream: bool = False) -> str:
    """Apply an edit using the Relace Instant Apply API.

    Args:
        api_key: Relace API key
        initial_code: The existing code to modify
        edit_snippet: The edit snippet containing the modifications
        stream: Whether to enable streaming response

    Returns:
        The merged code

    Raises:
        Exception: If the API request fails
    """
    url = "https://codegen-instantapply.endpoint.relace.run/v1/code/apply"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

    data = {"initialCode": initial_code, "editSnippet": edit_snippet, "stream": stream}

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["mergedCode"]
    except Exception as e:
        msg = f"Relace API request failed: {e!s}"
        raise Exception(msg)


def relace_edit(codebase: Codebase, filepath: str, edit_snippet: str, api_key: str | None = None) -> RelaceEditObservation:
    """Edit a file using the Relace Instant Apply API.

    Args:
        codebase: Codebase object
        filepath: Path to the file to edit
        edit_snippet: The edit snippet containing the modifications
        api_key: Optional Relace API key. If not provided, will be retrieved from environment variables.

    Returns:
        RelaceEditObservation with the results
    """
    try:
        file = codebase.get_file(filepath)
    except ValueError:
        # Return an observation with error status instead of raising an exception
        # Include the full filepath in the error message
        return RelaceEditObservation(
            status="error",
            error=f"File not found: {filepath}. Please provide the full filepath relative to the repository root.",
            filepath=filepath,
        )

    # Get the original content
    original_content = file.content
    original_lines = original_content.split("\n")

    # Get API key if not provided
    if api_key is None:
        try:
            api_key = get_relace_api_key()
        except ValueError as e:
            return RelaceEditObservation(
                status="error",
                error=str(e),
                filepath=filepath,
            )

    # Apply the edit using Relace API
    try:
        merged_code = apply_relace_edit(api_key, original_content, edit_snippet)
        if original_content.endswith("\n") and not merged_code.endswith("\n"):
            merged_code += "\n"
    except Exception as e:
        return RelaceEditObservation(
            status="error",
            error=str(e),
            filepath=filepath,
        )

    # Generate diff
    diff = generate_diff(original_content, merged_code)

    # Apply the edit to the file
    file.edit(merged_code)
    codebase.commit()

    return RelaceEditObservation(
        status="success",
        filepath=filepath,
        diff=diff,
        new_content=add_line_numbers(merged_code),
        line_count=len(merged_code.split("\n")),
    )
