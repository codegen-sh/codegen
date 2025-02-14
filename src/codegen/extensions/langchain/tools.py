"""Langchain tools for workspace operations."""

import json
from typing import ClassVar, Literal, Optional

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from codegen import Codebase
from codegen.extensions.linear.linear_client import LinearClient
from codegen.extensions.tools.linear_tools import (
    linear_comment_on_issue_tool,
    linear_get_issue_comments_tool,
    linear_get_issue_tool,
)

from ..tools import (
    commit,
    create_file,
    create_pr,
    create_pr_comment,
    create_pr_review_comment,
    delete_file,
    edit_file,
    list_directory,
    move_symbol,
    rename_file,
    reveal_symbol,
    search,
    semantic_edit,
    semantic_search,
    view_file,
    view_pr,
)


class ViewFileInput(BaseModel):
    """Input for viewing a file."""

    filepath: str = Field(..., description="Path to the file relative to workspace root")


class ViewFileTool(BaseTool):
    """Tool for viewing file contents and metadata."""

    name: ClassVar[str] = "view_file"
    description: ClassVar[str] = "View the contents and metadata of a file in the codebase"
    args_schema: ClassVar[type[BaseModel]] = ViewFileInput
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(self, filepath: str) -> str:
        result = view_file(self.codebase, filepath)
        return json.dumps(result, indent=2)


class ListDirectoryInput(BaseModel):
    """Input for listing directory contents."""

    dirpath: str = Field(default="./", description="Path to directory relative to workspace root")
    depth: int = Field(default=1, description="How deep to traverse. Use -1 for unlimited depth.")


class ListDirectoryTool(BaseTool):
    """Tool for listing directory contents."""

    name: ClassVar[str] = "list_directory"
    description: ClassVar[str] = "List contents of a directory in the codebase"
    args_schema: ClassVar[type[BaseModel]] = ListDirectoryInput
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(self, dirpath: str = "./", depth: int = 1) -> str:
        result = list_directory(self.codebase, dirpath, depth)
        return json.dumps(result, indent=2)


class SearchInput(BaseModel):
    """Input for searching the codebase."""

    query: str = Field(..., description="The search query, passed into python's re.match()")
    target_directories: Optional[list[str]] = Field(default=None, description="Optional list of directories to search in")


class SearchTool(BaseTool):
    """Tool for searching the codebase."""

    name: ClassVar[str] = "search"
    description: ClassVar[str] = "Search the codebase using text search"
    args_schema: ClassVar[type[BaseModel]] = SearchInput
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(self, query: str, target_directories: Optional[list[str]] = None) -> str:
        result = search(self.codebase, query, target_directories)
        return json.dumps(result, indent=2)


class EditFileInput(BaseModel):
    """Input for editing a file."""

    filepath: str = Field(..., description="Path to the file to edit")
    content: str = Field(..., description="New content for the file")


class EditFileTool(BaseTool):
    """Tool for editing files."""

    name: ClassVar[str] = "edit_file"
    description: ClassVar[str] = "Edit a file by replacing its entire content"
    args_schema: ClassVar[type[BaseModel]] = EditFileInput
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(self, filepath: str, content: str) -> str:
        result = edit_file(self.codebase, filepath, content)
        return json.dumps(result, indent=2)


class CreateFileInput(BaseModel):
    """Input for creating a file."""

    filepath: str = Field(..., description="Path where to create the file")
    content: str = Field(default="", description="Initial file content")


class CreateFileTool(BaseTool):
    """Tool for creating files."""

    name: ClassVar[str] = "create_file"
    description: ClassVar[str] = "Create a new file in the codebase"
    args_schema: ClassVar[type[BaseModel]] = CreateFileInput
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(self, filepath: str, content: str = "") -> str:
        result = create_file(self.codebase, filepath, content)
        return json.dumps(result, indent=2)


class DeleteFileInput(BaseModel):
    """Input for deleting a file."""

    filepath: str = Field(..., description="Path to the file to delete")


class DeleteFileTool(BaseTool):
    """Tool for deleting files."""

    name: ClassVar[str] = "delete_file"
    description: ClassVar[str] = "Delete a file from the codebase"
    args_schema: ClassVar[type[BaseModel]] = DeleteFileInput
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(self, filepath: str) -> str:
        result = delete_file(self.codebase, filepath)
        return json.dumps(result, indent=2)


class CommitTool(BaseTool):
    """Tool for committing changes."""

    name: ClassVar[str] = "commit"
    description: ClassVar[str] = "Commit any pending changes to disk"
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(self) -> str:
        result = commit(self.codebase)
        return json.dumps(result, indent=2)


class RevealSymbolInput(BaseModel):
    """Input for revealing symbol relationships."""

    symbol_name: str = Field(..., description="Name of the symbol to analyze")
    degree: int = Field(default=1, description="How many degrees of separation to traverse")
    max_tokens: Optional[int] = Field(
        default=None,
        description="Optional maximum number of tokens for all source code combined",
    )
    collect_dependencies: bool = Field(default=True, description="Whether to collect dependencies")
    collect_usages: bool = Field(default=True, description="Whether to collect usages")


class RevealSymbolTool(BaseTool):
    """Tool for revealing symbol relationships."""

    name: ClassVar[str] = "reveal_symbol"
    description: ClassVar[str] = "Reveal the dependencies and usages of a symbol up to N degrees"
    args_schema: ClassVar[type[BaseModel]] = RevealSymbolInput
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(
        self,
        symbol_name: str,
        degree: int = 1,
        max_tokens: Optional[int] = None,
        collect_dependencies: bool = True,
        collect_usages: bool = True,
    ) -> str:
        result = reveal_symbol(
            codebase=self.codebase,
            symbol_name=symbol_name,
            degree=degree,
            max_tokens=max_tokens,
            collect_dependencies=collect_dependencies,
            collect_usages=collect_usages,
        )
        return json.dumps(result, indent=2)


class SemanticEditInput(BaseModel):
    """Input for semantic editing."""

    filepath: str = Field(..., description="Path to the file to edit")
    edit_spec: str = Field(
        ...,
        description="""The edit specification showing desired changes.
Must contain code blocks between '# ... existing code ...' markers.
Example:
# ... existing code ...
def new_function():
    print("Hello")
# ... existing code ...
""",
    )


class SemanticEditTool(BaseTool):
    """Tool for semantic editing of files."""

    name: ClassVar[str] = "semantic_edit"
    description: ClassVar[str] = "Edit a file using a semantic edit specification with code blocks"
    args_schema: ClassVar[type[BaseModel]] = SemanticEditInput
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(self, filepath: str, edit_spec: str) -> str:
        result = semantic_edit(self.codebase, filepath, edit_spec)
        return json.dumps(result, indent=2)


class RenameFileInput(BaseModel):
    """Input for renaming a file."""

    filepath: str = Field(..., description="Current path of the file relative to workspace root")
    new_filepath: str = Field(..., description="New path for the file relative to workspace root")


class RenameFileTool(BaseTool):
    """Tool for renaming files and updating imports."""

    name: ClassVar[str] = "rename_file"
    description: ClassVar[str] = "Rename a file and update all imports to point to the new location"
    args_schema: ClassVar[type[BaseModel]] = RenameFileInput
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(self, filepath: str, new_filepath: str) -> str:
        result = rename_file(self.codebase, filepath, new_filepath)
        return json.dumps(result, indent=2)


class MoveSymbolInput(BaseModel):
    """Input for moving a symbol between files."""

    source_file: str = Field(..., description="Path to the file containing the symbol")
    symbol_name: str = Field(..., description="Name of the symbol to move")
    target_file: str = Field(..., description="Path to the destination file")
    strategy: Literal["update_all_imports", "add_back_edge"] = Field(
        default="update_all_imports",
        description="Strategy for handling imports: 'update_all_imports' (default) or 'add_back_edge'",
    )
    include_dependencies: bool = Field(default=True, description="Whether to move dependencies along with the symbol")


class MoveSymbolTool(BaseTool):
    """Tool for moving symbols between files."""

    name: ClassVar[str] = "move_symbol"
    description: ClassVar[str] = "Move a symbol from one file to another, with configurable import handling"
    args_schema: ClassVar[type[BaseModel]] = MoveSymbolInput
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(
        self,
        source_file: str,
        symbol_name: str,
        target_file: str,
        strategy: Literal["update_all_imports", "add_back_edge"] = "update_all_imports",
        include_dependencies: bool = True,
    ) -> str:
        result = move_symbol(
            self.codebase,
            source_file,
            symbol_name,
            target_file,
            strategy=strategy,
            include_dependencies=include_dependencies,
        )
        return json.dumps(result, indent=2)


class SemanticSearchInput(BaseModel):
    """Input for Semantic search of a codebase"""

    query: str = Field(..., description="The natural language search query")
    k: int = Field(default=5, description="Number of results to return")
    preview_length: int = Field(default=200, description="Length of content preview in characters")


class SemanticSearchTool(BaseTool):
    """Tool for semantic code search."""

    name: ClassVar[str] = "semantic_search"
    description: ClassVar[str] = "Search the codebase using natural language queries and semantic similarity"
    args_schema: ClassVar[type[BaseModel]] = SemanticSearchInput
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(self, query: str, k: int = 5, preview_length: int = 200) -> str:
        result = semantic_search(self.codebase, query, k=k, preview_length=preview_length)
        return json.dumps(result, indent=2)


class CreatePRInput(BaseModel):
    """Input for creating a PR"""

    title: str = Field(..., description="The title of the PR")
    body: str = Field(..., description="The body of the PR")


class CreatePRTool(BaseTool):
    """Tool for creating a PR."""

    name: ClassVar[str] = "create_pr"
    description: ClassVar[str] = "Create a PR for the current branch"
    args_schema: ClassVar[type[BaseModel]] = CreatePRInput
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(self, title: str, body: str) -> str:
        result = create_pr(self.codebase, title, body)
        return json.dumps(result, indent=2)


class GetPRContentsInput(BaseModel):
    """Input for getting PR contents."""

    pr_id: int = Field(..., description="Number of the PR to get the contents for")


class GetPRcontentsTool(BaseTool):
    """Tool for getting PR data."""

    name: ClassVar[str] = "get_pr_contents"
    description: ClassVar[str] = "Get the diff and modified symbols of a PR along with the dependencies of the modified symbols"
    args_schema: ClassVar[type[BaseModel]] = GetPRContentsInput
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(self, pr_id: int) -> str:
        result = view_pr(self.codebase, pr_id)
        return json.dumps(result, indent=2)


class CreatePRCommentInput(BaseModel):
    """Input for creating a PR comment"""

    pr_number: int = Field(..., description="The PR number to comment on")
    body: str = Field(..., description="The comment text")


class CreatePRCommentTool(BaseTool):
    """Tool for creating a general PR comment."""

    name: ClassVar[str] = "create_pr_comment"
    description: ClassVar[str] = "Create a general comment on a pull request"
    args_schema: ClassVar[type[BaseModel]] = CreatePRCommentInput
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(self, pr_number: int, body: str) -> str:
        result = create_pr_comment(self.codebase, pr_number, body)
        return json.dumps(result, indent=2)


class CreatePRReviewCommentInput(BaseModel):
    """Input for creating an inline PR review comment"""

    pr_number: int = Field(..., description="The PR number to comment on")
    body: str = Field(..., description="The comment text")
    commit_sha: str = Field(..., description="The commit SHA to attach the comment to")
    path: str = Field(..., description="The file path to comment on")
    line: int | None = Field(None, description="The line number to comment on")
    side: str | None = Field(None, description="Which version of the file to comment on ('LEFT' or 'RIGHT')")
    start_line: int | None = Field(None, description="For multi-line comments, the starting line")


class CreatePRReviewCommentTool(BaseTool):
    """Tool for creating inline PR review comments."""

    name: ClassVar[str] = "create_pr_review_comment"
    description: ClassVar[str] = "Create an inline review comment on a specific line in a pull request"
    args_schema: ClassVar[type[BaseModel]] = CreatePRReviewCommentInput
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(
        self,
        pr_number: int,
        body: str,
        commit_sha: str,
        path: str,
        line: int | None = None,
        side: str | None = None,
        start_line: int | None = None,
    ) -> str:
        result = create_pr_review_comment(
            self.codebase,
            pr_number=pr_number,
            body=body,
            commit_sha=commit_sha,
            path=path,
            line=line,
            side=side,
            start_line=start_line,
        )
        return json.dumps(result, indent=2)


class LinearGetIssueInput(BaseModel):
    """Input for getting a Linear issue."""

    issue_id: str = Field(..., description="ID of the Linear issue to retrieve")


class LinearGetIssueTool(BaseTool):
    """Tool for getting Linear issue details."""

    name: ClassVar[str] = "linear_get_issue"
    description: ClassVar[str] = "Get details of a Linear issue by its ID"
    args_schema: ClassVar[type[BaseModel]] = LinearGetIssueInput
    client: LinearClient = Field(exclude=True)

    def __init__(self, client: LinearClient) -> None:
        super().__init__(client=client)

    def _run(self, issue_id: str) -> str:
        result = linear_get_issue_tool(self.client, issue_id)
        return json.dumps(result, indent=2)


class LinearGetIssueCommentsInput(BaseModel):
    """Input for getting Linear issue comments."""

    issue_id: str = Field(..., description="ID of the Linear issue to get comments for")


class LinearGetIssueCommentsTool(BaseTool):
    """Tool for getting Linear issue comments."""

    name: ClassVar[str] = "linear_get_issue_comments"
    description: ClassVar[str] = "Get all comments on a Linear issue"
    args_schema: ClassVar[type[BaseModel]] = LinearGetIssueCommentsInput
    client: LinearClient = Field(exclude=True)

    def __init__(self, client: LinearClient) -> None:
        super().__init__(client=client)

    def _run(self, issue_id: str) -> str:
        result = linear_get_issue_comments_tool(self.client, issue_id)
        return json.dumps(result, indent=2)


class LinearCommentOnIssueInput(BaseModel):
    """Input for commenting on a Linear issue."""

    issue_id: str = Field(..., description="ID of the Linear issue to comment on")
    body: str = Field(..., description="The comment text")


class LinearCommentOnIssueTool(BaseTool):
    """Tool for commenting on Linear issues."""

    name: ClassVar[str] = "linear_comment_on_issue"
    description: ClassVar[str] = "Add a comment to a Linear issue"
    args_schema: ClassVar[type[BaseModel]] = LinearCommentOnIssueInput
    client: LinearClient = Field(exclude=True)

    def __init__(self, client: LinearClient) -> None:
        super().__init__(client=client)

    def _run(self, issue_id: str, body: str) -> str:
        result = linear_comment_on_issue_tool(self.client, issue_id, body)
        return json.dumps(result, indent=2)


def get_workspace_tools(codebase: Codebase) -> list["BaseTool"]:
    """Get all workspace tools initialized with a codebase.

    Args:
        codebase: The codebase to operate on

    Returns:
        List of initialized Langchain tools
    """
    return [
        CommitTool(codebase),
        CreateFileTool(codebase),
        CreatePRTool(codebase),
        CreatePRCommentTool(codebase),
        CreatePRReviewCommentTool(codebase),
        DeleteFileTool(codebase),
        EditFileTool(codebase),
        GetPRcontentsTool(codebase),
        ListDirectoryTool(codebase),
        MoveSymbolTool(codebase),
        RenameFileTool(codebase),
        RevealSymbolTool(codebase),
        SearchTool(codebase),
        SemanticEditTool(codebase),
        SemanticSearchTool(codebase),
        ViewFileTool(codebase),
        LinearGetIssueTool(codebase),
        LinearGetIssueCommentsTool(codebase),
        LinearCommentOnIssueTool(codebase),
    ]
