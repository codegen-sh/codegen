from typing import ClassVar, Literal, Optional

from langchain_core.tools.base import BaseTool
from pydantic import BaseModel

from codegen.extensions.langchain.tools import (
    _SEMANTIC_EDIT_BRIEF,
    CommitTool,
    CreateFileInput,
    CreateFileTool,
    DeleteFileInput,
    DeleteFileTool,
    EditFileInput,
    EditFileTool,
    ListDirectoryInput,
    ListDirectoryTool,
    MoveSymbolInput,
    MoveSymbolTool,
    RenameFileInput,
    RenameFileTool,
    ReplacementEditInput,
    ReplacementEditTool,
    RevealSymbolInput,
    RevealSymbolTool,
    SearchInput,
    SearchTool,
    SemanticEditInput,
    SemanticEditTool,
    SemanticSearchInput,
    SemanticSearchTool,
    ViewFileInput,
    ViewFileTool,
)
from codegen.runner.clients.sandbox_client import RemoteSandboxClient


class CodegenTool(BaseTool):
    """Base class for all Codegen tools."""

    client: RemoteSandboxClient

    def __init__(self, client: RemoteSandboxClient) -> None:
        super().__init__(client=client)


class ViewFileToolV2(CodegenTool):
    """Tool for viewing file contents and metadata."""

    name: ClassVar[str] = "view_file"
    description: ClassVar[str] = """View the contents and metadata of a file in the codebase.
For large files (>250 lines), content will be paginated. Use start_line and end_line to navigate through the file.
The response will indicate if there are more lines available to view."""
    args_schema: ClassVar[type[BaseModel]] = ViewFileInput

    def _run(
        self,
        filepath: str,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
        max_lines: Optional[int] = None,
        line_numbers: Optional[bool] = True,
    ) -> str:
        res = self.client.post(
            ViewFileTool.name,
            ViewFileInput(
                filepath=filepath,
                start_line=start_line,
                end_line=end_line,
                max_lines=max_lines,
                line_numbers=line_numbers,
            ),
        )
        return res.json().get("content")


class ListDirectoryToolV2(CodegenTool):
    """Tool for listing directory contents."""

    name: ClassVar[str] = "list_directory"
    description: ClassVar[str] = "List contents of a directory in the codebase"
    args_schema: ClassVar[type[BaseModel]] = ListDirectoryInput

    def _run(self, dirpath: str = "./", depth: int = 1) -> str:
        res = self.client.post(
            ListDirectoryTool.name,
            ListDirectoryInput(
                dirpath=dirpath,
                depth=depth,
            ),
        )
        return res.json().get("content")


class SearchToolV2(CodegenTool):
    """Tool for searching the codebase."""

    name: ClassVar[str] = "search"
    description: ClassVar[str] = "Search the codebase using text search"
    args_schema: ClassVar[type[BaseModel]] = SearchInput

    def _run(self, query: str, target_directories: Optional[list[str]] = None) -> str:
        res = self.client.post(
            SearchTool.name,
            SearchInput(
                query=query,
                target_directories=target_directories,
            ),
        )
        return res.json().get("content")


class EditFileToolV2(CodegenTool):
    """Tool for editing files."""

    name: ClassVar[str] = "edit_file"
    description: ClassVar[str] = "Edit a file by replacing its entire content. This tool should only be used for replacing entire file contents."
    args_schema: ClassVar[type[BaseModel]] = EditFileInput

    def _run(self, filepath: str, content: str) -> str:
        res = self.client.post(
            EditFileTool.name,
            EditFileInput(
                filepath=filepath,
                content=content,
            ),
        )
        return res.json().get("content")


class CreateFileToolV2(CodegenTool):
    """Tool for creating files."""

    name: ClassVar[str] = "create_file"
    description: ClassVar[str] = "Create a new file in the codebase"
    args_schema: ClassVar[type[BaseModel]] = CreateFileInput

    def _run(self, filepath: str, content: str = "") -> str:
        res = self.client.post(
            CreateFileTool.name,
            CreateFileInput(
                filepath=filepath,
                content=content,
            ),
        )
        return res.json().get("content")


class DeleteFileToolV2(CodegenTool):
    """Tool for deleting files."""

    name: ClassVar[str] = "delete_file"
    description: ClassVar[str] = "Delete a file from the codebase"
    args_schema: ClassVar[type[BaseModel]] = DeleteFileInput

    def _run(self, filepath: str) -> str:
        res = self.client.post(
            DeleteFileTool.name,
            DeleteFileInput(
                filepath=filepath,
            ),
        )
        return res.json().get("content")


class SemanticSearchToolV2(CodegenTool):
    """Tool for semantic code search."""

    name: ClassVar[str] = "semantic_search"
    description: ClassVar[str] = "Search the codebase using natural language queries and semantic similarity"
    args_schema: ClassVar[type[BaseModel]] = SemanticSearchInput

    def _run(self, query: str, k: int = 5, preview_length: int = 200) -> str:
        res = self.client.post(
            SemanticSearchTool.name,
            SemanticSearchInput(
                query=query,
                k=k,
                preview_length=preview_length,
            ),
        )
        return res.json().get("content")


class CommitToolV2(CodegenTool):
    """Tool for committing changes."""

    name: ClassVar[str] = "commit"
    description: ClassVar[str] = "Commit any pending changes to disk"

    def _run(self) -> str:
        res = self.client.post(CommitTool.name, {})
        return res.json().get("content")


class RevealSymbolToolV2(CodegenTool):
    """Tool for revealing symbol relationships."""

    name: ClassVar[str] = "reveal_symbol"
    description: ClassVar[str] = "Reveal the dependencies and usages of a symbol up to N degrees"
    args_schema: ClassVar[type[BaseModel]] = RevealSymbolInput

    def _run(
        self,
        symbol_name: str,
        degree: int = 1,
        max_tokens: Optional[int] = None,
        collect_dependencies: bool = True,
        collect_usages: bool = True,
    ) -> str:
        res = self.client.post(
            RevealSymbolTool.name,
            RevealSymbolInput(
                symbol_name=symbol_name,
                degree=degree,
                max_tokens=max_tokens,
                collect_dependencies=collect_dependencies,
                collect_usages=collect_usages,
            ),
        )
        return res.json().get("content")


class SemanticEditToolV2(CodegenTool):
    """Tool for semantic editing of files."""

    name: ClassVar[str] = "semantic_edit"
    description: ClassVar[str] = _SEMANTIC_EDIT_BRIEF
    args_schema: ClassVar[type[BaseModel]] = SemanticEditInput

    def _run(self, filepath: str, edit_content: str, start: int = 1, end: int = -1) -> str:
        res = self.client.post(
            SemanticEditTool.name,
            SemanticEditInput(
                filepath=filepath,
                edit_content=edit_content,
                start=start,
                end=end,
            ),
        )
        return res.json().get("content")


class RenameFileToolV2(CodegenTool):
    """Tool for renaming files and updating imports."""

    name: ClassVar[str] = "rename_file"
    description: ClassVar[str] = "Rename a file and update all imports to point to the new location"
    args_schema: ClassVar[type[BaseModel]] = RenameFileInput

    def _run(self, filepath: str, new_filepath: str) -> str:
        res = self.client.post(
            RenameFileTool.name,
            RenameFileInput(
                filepath=filepath,
                new_filepath=new_filepath,
            ),
        )
        return res.json().get("content")


class MoveSymbolToolV2(CodegenTool):
    """Tool for moving symbols between files."""

    name: ClassVar[str] = "move_symbol"
    description: ClassVar[str] = "Move a symbol from one file to another, with configurable import handling"
    args_schema: ClassVar[type[BaseModel]] = MoveSymbolInput

    def _run(
        self,
        source_file: str,
        symbol_name: str,
        target_file: str,
        strategy: Literal["update_all_imports", "add_back_edge"] = "update_all_imports",
        include_dependencies: bool = True,
    ) -> str:
        res = self.client.post(
            MoveSymbolTool.name,
            MoveSymbolInput(
                source_file=source_file,
                symbol_name=symbol_name,
                target_file=target_file,
                strategy=strategy,
                include_dependencies=include_dependencies,
            ),
        )
        return res.json().get("content")


class ReplacementEditToolV2(CodegenTool):
    """Tool for regex-based replacement editing of files."""

    name: ClassVar[str] = "replace"
    description: ClassVar[str] = "Replace text in a file using regex pattern matching. For files over 300 lines, specify a line range."
    args_schema: ClassVar[type[BaseModel]] = ReplacementEditInput

    def _run(
        self,
        filepath: str,
        pattern: str,
        replacement: str,
        start: int = 1,
        end: int = -1,
        count: Optional[int] = None,
    ) -> str:
        res = self.client.post(
            ReplacementEditTool.name,
            ReplacementEditInput(
                filepath=filepath,
                pattern=pattern,
                replacement=replacement,
                start=start,
                end=end,
                count=count,
            ),
        )
        return res.json().get("content")


def get_tools(client: RemoteSandboxClient) -> list[BaseTool]:
    """Get all tools initialized with a client.

    Args:
        client: The client to use for tool operations

    Returns:
        List of initialized tools
    """
    return [
        ViewFileToolV2(client),
        ListDirectoryToolV2(client),
        SearchToolV2(client),
        EditFileToolV2(client),
        CreateFileToolV2(client),
        DeleteFileToolV2(client),
        SemanticSearchToolV2(client),
        CommitToolV2(client),
        RevealSymbolToolV2(client),
        SemanticEditToolV2(client),
        RenameFileToolV2(client),
        MoveSymbolToolV2(client),
        ReplacementEditToolV2(client),
    ]
