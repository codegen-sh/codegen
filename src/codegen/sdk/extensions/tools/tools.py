
from collections.abc import Callable
from typing import Annotated, ClassVar, Literal, Optional

from langchain_core.messages import ToolMessage
from langchain_core.stores import InMemoryBaseStore
from langchain_core.tools import InjectedToolCallId
from langchain_core.tools.base import BaseTool
from langgraph.prebuilt import InjectedStore
from pydantic import BaseModel, Field
from codegen.sdk.core.codebase import Codebase

from list_directory import list_directory
from view_file import view_file
from reveal_symbol import reveal_symbol
from reflection import perform_reflection
from bash import run_bash_command

class RunBashCommandInput(BaseModel):
    """Input for running a bash command."""

    command: str = Field(..., description="The command to run")
    is_background: bool = Field(default=False, description="Whether to run the command in the background")


class RunBashCommandTool(BaseTool):
    """Tool for running bash commands."""

    name: ClassVar[str] = "run_bash_command"
    description: ClassVar[str] = "Run a bash command and return its output"
    args_schema: ClassVar[type[BaseModel]] = RunBashCommandInput

    def _run(self, command: str, is_background: bool = False) -> str:
        result = run_bash_command(command, is_background)
        return result.render()


class ViewFileInput(BaseModel):
    """Input for viewing a file."""

    filepath: str = Field(
        ..., description="Path to the file relative to workspace root"
    )
    start_line: Optional[int] = Field(
        None, description="Starting line number to view (1-indexed, inclusive)"
    )
    end_line: Optional[int] = Field(
        None, description="Ending line number to view (1-indexed, inclusive)"
    )
    max_lines: Optional[int] = Field(
        None, description="Maximum number of lines to view at once, defaults to 500"
    )
    line_numbers: Optional[bool] = Field(
        True, description="If True, add line numbers to the content (1-indexed)"
    )
    tool_call_id: Annotated[str, InjectedToolCallId]


class ViewFileTool(BaseTool):
    """Tool for viewing file contents and metadata."""

    name: ClassVar[str] = "view_file"
    description: ClassVar[
        str
    ] = """View the contents and metadata of a file in the codebase.
For large files (>500 lines), content will be paginated. Use start_line and end_line to navigate through the file.
The response will indicate if there are more lines available to view."""
    args_schema: ClassVar[type[BaseModel]] = ViewFileInput
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(
        self,
        tool_call_id: str,
        filepath: str,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
        max_lines: Optional[int] = None,
        line_numbers: Optional[bool] = True,
    ) -> ToolMessage:
        result = view_file(
            self.codebase,
            filepath,
            line_numbers=line_numbers if line_numbers is not None else True,
            start_line=start_line,
            end_line=end_line,
            max_lines=max_lines if max_lines is not None else 500,
        )

        return result.render(tool_call_id)


class ListDirectoryInput(BaseModel):
    """Input for listing directory contents."""

    dirpath: str = Field(
        default="./", description="Path to directory relative to workspace root"
    )
    depth: int = Field(
        default=1, description="How deep to traverse. Use -1 for unlimited depth."
    )
    tool_call_id: Annotated[str, InjectedToolCallId]


class ListDirectoryTool(BaseTool):
    """Tool for listing directory contents."""

    name: ClassVar[str] = "list_directory"
    description: ClassVar[str] = "List contents of a directory in the codebase"
    args_schema: ClassVar[type[BaseModel]] = ListDirectoryInput
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(
        self, tool_call_id: str, dirpath: str = "./", depth: int = 1
    ) -> ToolMessage:
        result = list_directory(self.codebase, dirpath, depth)
        return result.render(tool_call_id)


class RevealSymbolInput(BaseModel):
    """Input for revealing symbol relationships."""

    symbol_name: str = Field(..., description="Name of the symbol to analyze")
    degree: int = Field(
        default=1, description="How many degrees of separation to traverse"
    )
    max_tokens: int | None = Field(
        default=None,
        description="Optional maximum number of tokens for all source code combined",
    )
    collect_dependencies: bool = Field(
        default=True, description="Whether to collect dependencies"
    )
    collect_usages: bool = Field(default=True, description="Whether to collect usages")


class RevealSymbolTool(BaseTool):
    """Tool for revealing symbol relationships."""

    name: ClassVar[str] = "reveal_symbol"
    description: ClassVar[str] = (
        "Reveal the dependencies and usages of a symbol up to N degrees"
    )
    args_schema: ClassVar[type[BaseModel]] = RevealSymbolInput
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(
        self,
        symbol_name: str,
        degree: int = 1,
        max_tokens: int | None = None,
        collect_dependencies: bool = True,
        collect_usages: bool = True,
    ) -> str:
        result = reveal_symbol(
            codebase=self.codebase,
            symbol_name=symbol_name,
            max_depth=degree,
            max_tokens=max_tokens,
            collect_dependencies=collect_dependencies,
            collect_usages=collect_usages,
        )
        return result.render()
class ReflectionInput(BaseModel):
    """Input for agent reflection."""

    context_summary: str = Field(..., description="Summary of the current context and problem being solved")
    findings_so_far: str = Field(..., description="Key information and insights gathered so far")
    current_challenges: str = Field(default="", description="Current obstacles or questions that need to be addressed")
    reflection_focus: str | None = Field(default=None, description="Optional specific aspect to focus reflection on (e.g., 'architecture', 'performance', 'next steps')")


class ReflectionTool(BaseTool):
    """Tool for agent self-reflection and planning."""

    name: ClassVar[str] = "reflect"
    description: ClassVar[str] = """
    Reflect on current understanding and plan next steps.
    This tool helps organize thoughts, identify knowledge gaps, and create a strategic plan.
    Use this when you need to consolidate information or when facing complex decisions.
    """
    args_schema: ClassVar[type[BaseModel]] = ReflectionInput
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(
        self,
        context_summary: str,
        findings_so_far: str,
        current_challenges: str = "",
        reflection_focus: str | None = None,
    ) -> str:
        result = perform_reflection(context_summary=context_summary, findings_so_far=findings_so_far, current_challenges=current_challenges, reflection_focus=reflection_focus, codebase=self.codebase)

        return result.render()

def get_workspace_tools(codebase: Codebase) -> list["BaseTool"]:
    """Get all workspace tools initialized with a codebase.

    Args:
        codebase: The codebase to operate on

    Returns:
        List of initialized Langchain tools
    """
    return [
,
        ListDirectoryTool(codebase),
        RevealSymbolTool(codebase),
        RunBashCommandTool(),  # Note: This tool doesn't need the codebase
        ViewFileTool(codebase),
        ReflectionTool(codebase),
    ]
