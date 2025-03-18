"""Langchain tools for workspace operations."""

from collections.abc import Callable
from typing import ClassVar, Literal

from langchain_core.tools.base import BaseTool
from pydantic import BaseModel, Field

from codegen.extensions.linear.linear_client import LinearClient
from codegen.extensions.tools.bash import run_bash_command
from codegen.extensions.tools.github.checkout_pr import checkout_pr
from codegen.extensions.tools.github.view_pr_checks import view_pr_checks
from codegen.extensions.tools.global_replacement_edit import replacement_edit_global
from codegen.extensions.tools.linear.linear import (
    linear_comment_on_issue_tool,
    linear_create_issue_tool,
    linear_get_issue_comments_tool,
    linear_get_issue_tool,
    linear_get_teams_tool,
    linear_search_issues_tool,
)
from codegen.extensions.tools.link_annotation import add_links_to_message
from codegen.extensions.tools.reflection import perform_reflection
from codegen.extensions.tools.relace_edit import relace_edit
from codegen.extensions.tools.replacement_edit import replacement_edit
from codegen.extensions.tools.reveal_symbol import reveal_symbol
from codegen.extensions.tools.search import search
from codegen.extensions.tools.search_files_by_name import search_files_by_name
from codegen.extensions.tools.semantic_edit import semantic_edit
from codegen.extensions.tools.semantic_search import semantic_search
from codegen.sdk.core.codebase import Codebase

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
    view_file,
    view_pr,
)
from ..tools.relace_edit_prompts import RELACE_EDIT_PROMPT
from ..tools.semantic_edit_prompts import FILE_EDIT_PROMPT


class ViewFileInput(BaseModel):
    """Input for viewing a file."""

    filepath: str = Field(..., description="Path to the file relative to workspace root")
    start_line: int | None = Field(None, description="Starting line number to view (1-indexed, inclusive)")
    end_line: int | None = Field(None, description="Ending line number to view (1-indexed, inclusive)")
    max_lines: int | None = Field(None, description="Maximum number of lines to view at once, defaults to 250")
    line_numbers: bool | None = Field(True, description="If True, add line numbers to the content (1-indexed)")


class ViewFileTool(BaseTool):
    """Tool for viewing file contents and metadata."""

    name: ClassVar[str] = "view_file"
    description: ClassVar[str] = """View the contents and metadata of a file in the codebase.
For large files (>250 lines), content will be paginated. Use start_line and end_line to navigate through the file.
The response will indicate if there are more lines available to view."""
    args_schema: ClassVar[type[BaseModel]] = ViewFileInput
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(
        self,
        filepath: str,
        start_line: int | None = None,
        end_line: int | None = None,
        max_lines: int | None = None,
        line_numbers: bool | None = True,
    ) -> str:
        result = view_file(
            self.codebase,
            filepath,
            line_numbers=line_numbers if line_numbers is not None else True,
            start_line=start_line,
            end_line=end_line,
            max_lines=max_lines if max_lines is not None else 250,
        )

        return result.render()


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
        return result.render()


class SearchInput(BaseModel):
    """Input for searching the codebase."""

    query: str = Field(
        ...,
        description="""The search query to find in the codebase. When ripgrep is available, this will be passed as a ripgrep pattern. For regex searches, set use_regex=True.
        Ripgrep is the preferred method.""",
    )
    file_extensions: list[str] | None = Field(default=None, description="Optional list of file extensions to search (e.g. ['.py', '.ts'])")
    page: int = Field(default=1, description="Page number to return (1-based, default: 1)")
    files_per_page: int = Field(default=10, description="Number of files to return per page (default: 10)")
    use_regex: bool = Field(default=False, description="Whether to treat query as a regex pattern (default: False)")


class SearchTool(BaseTool):
    """Tool for searching the codebase."""

    name: ClassVar[str] = "search"
    description: ClassVar[str] = "Search the codebase using text search or regex pattern matching"
    args_schema: ClassVar[type[BaseModel]] = SearchInput
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(self, query: str, file_extensions: list[str] | None = None, page: int = 1, files_per_page: int = 10, use_regex: bool = False) -> str:
        result = search(self.codebase, query, file_extensions=file_extensions, page=page, files_per_page=files_per_page, use_regex=use_regex)
        return result.render()


class EditFileInput(BaseModel):
    """Input for editing a file."""

    filepath: str = Field(..., description="Path to the file to edit")
    content: str = Field(..., description="New content for the file")


class EditFileTool(BaseTool):
    """Tool for editing files."""

    name: ClassVar[str] = "edit_file"
    description: ClassVar[str] = r"""
Edit a file by replacing its entire content. This tool should only be used for replacing entire file contents.
Input for searching the codebase.

    This tool provides powerful text-based search capabilities across your codebase,
    with support for both simple text matching and regular expressions. It uses ripgrep
    when available for high-performance searches, falling back to Python's regex engine
    when necessary.

    Features:
    - Plain text or regex pattern matching
    - Directory and file type filtering
    - Paginated results for large codebases
    - Case-insensitive by default for simple text searches

    Example queries:
    1. Simple text: "function calculateTotal" (matches exactly, case-insensitive)
    2. Regex: "def.*calculate.*\(.*\)" (with use_regex=True)
    3. File-specific: "TODO" with file_extensions=[".py", ".ts"]
    """
    args_schema: ClassVar[type[BaseModel]] = EditFileInput
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(self, filepath: str, content: str) -> str:
        result = edit_file(self.codebase, filepath, content)
        return result.render()


class CreateFileInput(BaseModel):
    """Input for creating a file."""

    filepath: str = Field(..., description="Path where to create the file")
    content: str = Field(
        ...,
        description="""
Content for the new file (REQUIRED).

⚠️ IMPORTANT: This parameter MUST be a STRING, not a dictionary, JSON object, or any other data type.
Example: content="print('Hello world')"
NOT: content={"code": "print('Hello world')"}
                         """,
    )


class CreateFileTool(BaseTool):
    """Tool for creating files."""

    name: ClassVar[str] = "create_file"
    description: ClassVar[str] = """
Create a new file in the codebase. Always provide content for the new file, even if minimal.

⚠️ CRITICAL WARNING ⚠️
Both parameters MUST be provided as STRINGS:
The content for the new file always needs to be provided.

1. filepath: The path where to create the file (as a string)
2. content: The content for the new file (as a STRING, NOT as a dictionary or JSON object)

✅ CORRECT usage:
create_file(filepath="path/to/file.py", content="print('Hello world')")

The content parameter is REQUIRED and MUST be a STRING. If you receive a validation error about
missing content, you are likely trying to pass a dictionary instead of a string.
"""
    args_schema: ClassVar[type[BaseModel]] = CreateFileInput
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(self, filepath: str, content: str) -> str:
        result = create_file(self.codebase, filepath, content)
        return result.render()


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
        return result.render()


class CommitTool(BaseTool):
    """Tool for committing changes."""

    name: ClassVar[str] = "commit"
    description: ClassVar[str] = "Commit any pending changes to disk"
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(self) -> str:
        result = commit(self.codebase)
        return result.render()


class RevealSymbolInput(BaseModel):
    """Input for revealing symbol relationships."""

    symbol_name: str = Field(..., description="Name of the symbol to analyze")
    degree: int = Field(default=1, description="How many degrees of separation to traverse")
    max_tokens: int | None = Field(
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


# Note: a large file is over 300 lines. Please specify a range larger than the edit you want to make.
_SEMANTIC_EDIT_BRIEF = """Tool for file editing via an LLM delegate. Describe the changes you want to make and an expert will apply them to the file.

Specify the changes you want to make in the edit_content field, with helpful comments, like so:
```
# ... existing code ...

# edit: change function name and body
def function_redefinition():
    return 'new_function_body'

# ... existing code ...
```

Another agent will be responsible for applying your edit and will only see the `edit_content` and the range you specify, so be clear what you are looking to change.

For large files, specify a range slightly larger than the edit you want to make, and be clear in your description what should and shouldn't change.
"""


class SemanticEditInput(BaseModel):
    """Input for semantic editing."""

    filepath: str = Field(..., description="Path of the file relative to workspace root")
    edit_content: str = Field(..., description=FILE_EDIT_PROMPT)
    start: int = Field(default=1, description="Starting line number (1-indexed, inclusive). Default is 1.")
    end: int = Field(default=-1, description="Ending line number (1-indexed, inclusive). Default is -1 (end of file).")


class SemanticEditTool(BaseTool):
    """Tool for semantic editing of files."""

    name: ClassVar[str] = "semantic_edit"
    description: ClassVar[str] = _SEMANTIC_EDIT_BRIEF  # Short description
    args_schema: ClassVar[type[BaseModel]] = SemanticEditInput
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(self, filepath: str, edit_content: str, start: int = 1, end: int = -1) -> str:
        # Create the the draft editor mini llm
        result = semantic_edit(self.codebase, filepath, edit_content, start=start, end=end)
        return result.render()


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
        return result.render()


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
        return result.render()


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
        return result.render()


########################################################################################################################
# BASH
########################################################################################################################


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


########################################################################################################################
# GITHUB
########################################################################################################################


class GithubCreatePRInput(BaseModel):
    """Input for creating a PR"""

    title: str = Field(..., description="The title of the PR")
    body: str = Field(..., description="The body of the PR")


class GithubCreatePRTool(BaseTool):
    """Tool for creating a PR."""

    name: ClassVar[str] = "create_pr"
    description: ClassVar[str] = "Create a PR for the current branch"
    args_schema: ClassVar[type[BaseModel]] = GithubCreatePRInput
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(self, title: str, body: str) -> str:
        result = create_pr(self.codebase, title, body)
        return result.render()


class GithubSearchIssuesInput(BaseModel):
    """Input for searching GitHub issues."""

    query: str = Field(..., description="Search query string to find issues")


class GithubSearchIssuesTool(BaseTool):
    """Tool for searching GitHub issues."""

    name: ClassVar[str] = "search_issues"
    description: ClassVar[str] = "Search for GitHub issues/PRs using a query string from pygithub, e.g. 'is:pr is:open test_query'"
    args_schema: ClassVar[type[BaseModel]] = GithubSearchIssuesInput
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(self, query: str) -> str:
        result = search(self.codebase, query)
        return result.render()


class GithubViewPRInput(BaseModel):
    """Input for getting PR contents."""

    pr_id: int = Field(..., description="Number of the PR to get the contents for")


class GithubViewPRTool(BaseTool):
    """Tool for getting PR data."""

    name: ClassVar[str] = "view_pr"
    description: ClassVar[str] = "View the diff and associated context for a pull request"
    args_schema: ClassVar[type[BaseModel]] = GithubViewPRInput
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(self, pr_id: int) -> str:
        result = view_pr(self.codebase, pr_id)
        return result.render()


class GithubCheckoutPRInput(BaseModel):
    """Input for checkout out a PR head branch."""

    pr_number: int = Field(..., description="Number of the PR to checkout")


class GithubCheckoutPRTool(BaseTool):
    """Tool for checking out a PR head branch."""

    name: ClassVar[str] = "checkout_pr"
    description: ClassVar[str] = "Checkout out a PR head branch"
    args_schema: ClassVar[type[BaseModel]] = GithubCheckoutPRInput
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(self, pr_number: int) -> str:
        result = checkout_pr(self.codebase, pr_number)
        return result.render()


class GithubCreatePRCommentInput(BaseModel):
    """Input for creating a PR comment"""

    pr_number: int = Field(..., description="The PR number to comment on")
    body: str = Field(..., description="The comment text")


class GithubCreatePRCommentTool(BaseTool):
    """Tool for creating a general PR comment."""

    name: ClassVar[str] = "create_pr_comment"
    description: ClassVar[str] = "Create a general comment on a pull request"
    args_schema: ClassVar[type[BaseModel]] = GithubCreatePRCommentInput
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(self, pr_number: int, body: str) -> str:
        result = create_pr_comment(self.codebase, pr_number, body)
        return result.render()


class GithubCreatePRReviewCommentInput(BaseModel):
    """Input for creating an inline PR review comment"""

    pr_number: int = Field(..., description="The PR number to comment on")
    body: str = Field(..., description="The comment text")
    commit_sha: str = Field(..., description="The commit SHA to attach the comment to")
    path: str = Field(..., description="The file path to comment on")
    line: int = Field(..., description="The line number to comment on use the indices from the diff")
    start_line: int | None = Field(None, description="For multi-line comments, the starting line")


class GithubCreatePRReviewCommentTool(BaseTool):
    """Tool for creating inline PR review comments."""

    name: ClassVar[str] = "create_pr_review_comment"
    description: ClassVar[str] = "Create an inline review comment on a specific line in a pull request"
    args_schema: ClassVar[type[BaseModel]] = GithubCreatePRReviewCommentInput
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(
        self,
        pr_number: int,
        body: str,
        commit_sha: str,
        path: str,
        line: int,
        start_line: int | None = None,
    ) -> str:
        result = create_pr_review_comment(
            self.codebase,
            pr_number=pr_number,
            body=body,
            commit_sha=commit_sha,
            path=path,
            line=line,
        )
        return result.render()


class GithubViewPRCheckInput(BaseModel):
    """Input for viewing PR checks"""

    pr_number: int = Field(..., description="The PR number to view checks for")


class GithubViewPRCheckTool(BaseTool):
    """Tool for viewing PR checks."""

    name: ClassVar[str] = "view_pr_checks"
    description: ClassVar[str] = "View the check suites for a PR"
    args_schema: ClassVar[type[BaseModel]] = GithubCreatePRReviewCommentInput
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(self, pr_number: int) -> str:
        result = view_pr_checks(self.codebase, pr_number=pr_number)
        return result.render()


########################################################################################################################
# LINEAR
########################################################################################################################


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
        return result.render()


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
        return result.render()


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
        return result.render()


class LinearSearchIssuesInput(BaseModel):
    """Input for searching Linear issues."""

    query: str = Field(..., description="Search query string")
    limit: int = Field(default=10, description="Maximum number of issues to return")


class LinearSearchIssuesTool(BaseTool):
    """Tool for searching Linear issues."""

    name: ClassVar[str] = "linear_search_issues"
    description: ClassVar[str] = "Search for Linear issues using a query string"
    args_schema: ClassVar[type[BaseModel]] = LinearSearchIssuesInput
    client: LinearClient = Field(exclude=True)

    def __init__(self, client: LinearClient) -> None:
        super().__init__(client=client)

    def _run(self, query: str, limit: int = 10) -> str:
        result = linear_search_issues_tool(self.client, query, limit)
        return result.render()


class LinearCreateIssueInput(BaseModel):
    """Input for creating a Linear issue."""

    title: str = Field(..., description="Title of the issue")
    description: str | None = Field(None, description="Optional description of the issue")
    team_id: str | None = Field(None, description="Optional team ID. If not provided, uses the default team_id (recommended)")


class LinearCreateIssueTool(BaseTool):
    """Tool for creating Linear issues."""

    name: ClassVar[str] = "linear_create_issue"
    description: ClassVar[str] = "Create a new Linear issue"
    args_schema: ClassVar[type[BaseModel]] = LinearCreateIssueInput
    client: LinearClient = Field(exclude=True)

    def __init__(self, client: LinearClient) -> None:
        super().__init__(client=client)

    def _run(self, title: str, description: str | None = None, team_id: str | None = None) -> str:
        result = linear_create_issue_tool(self.client, title, description, team_id)
        return result.render()


class LinearGetTeamsTool(BaseTool):
    """Tool for getting Linear teams."""

    name: ClassVar[str] = "linear_get_teams"
    description: ClassVar[str] = "Get all Linear teams the authenticated user has access to"
    client: LinearClient = Field(exclude=True)

    def __init__(self, client: LinearClient) -> None:
        super().__init__(client=client)

    def _run(self) -> str:
        result = linear_get_teams_tool(self.client)
        return result.render()


########################################################################################################################
# SLACK
########################################################################################################################


class SlackSendMessageInput(BaseModel):
    """Input for sending a message to Slack."""

    content: str = Field(..., description="Message to send to Slack")


class SlackSendMessageTool(BaseTool):
    """Tool for sending a message to Slack."""

    name: ClassVar[str] = "send_slack_message"
    description: ClassVar[str] = (
        "Send a message via Slack."
        "Write symbol names (classes, functions, etc.) or full filepaths in single backticks and they will be auto-linked to the code."
        "Use Slack-style markdown for other links."
    )
    args_schema: ClassVar[type[BaseModel]] = SlackSendMessageInput
    say: Callable[[str], None] = Field(exclude=True)
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase, say: Callable[[str], None]) -> None:
        super().__init__(say=say, codebase=codebase)
        self.say = say
        self.codebase = codebase

    def _run(self, content: str) -> str:
        # TODO - pull this out into a separate function
        print("> Adding links to message")
        content_formatted = add_links_to_message(content, self.codebase)
        print("> Sending message to Slack")
        self.say(content_formatted)
        return "✅ Message sent successfully"


########################################################################################################################
# EXPORT
########################################################################################################################


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
        DeleteFileTool(codebase),
        EditFileTool(codebase),
        GithubViewPRTool(codebase),
        ListDirectoryTool(codebase),
        MoveSymbolTool(codebase),
        RenameFileTool(codebase),
        ReplacementEditTool(codebase),
        RevealSymbolTool(codebase),
        GlobalReplacementEditTool(codebase),
        RunBashCommandTool(),  # Note: This tool doesn't need the codebase
        SearchTool(codebase),
        SearchFilesByNameTool(codebase),
        # SemanticEditTool(codebase),
        # SemanticSearchTool(codebase),
        ViewFileTool(codebase),
        RelaceEditTool(codebase),
        ReflectionTool(codebase),
        # Github
        GithubCreatePRTool(codebase),
        GithubCreatePRCommentTool(codebase),
        GithubCreatePRReviewCommentTool(codebase),
        GithubViewPRTool(codebase),
        GithubSearchIssuesTool(codebase),
        # Linear
        LinearGetIssueTool(codebase),
        LinearGetIssueCommentsTool(codebase),
        LinearCommentOnIssueTool(codebase),
        LinearSearchIssuesTool(codebase),
        LinearCreateIssueTool(codebase),
        LinearGetTeamsTool(codebase),
    ]


class GlobalReplacementEditInput(BaseModel):
    """Input for replacement editing across the entire codebase."""

    file_pattern: str = Field(
        default="*",
        description=("Glob pattern to match files that should be edited. Supports all Python glob syntax including wildcards (*, ?, **)"),
    )
    pattern: str = Field(
        ...,
        description=(
            "Regular expression pattern to match text that should be replaced. "
            "Supports all Python regex syntax including capture groups (\\1, \\2, etc). "
            "The pattern is compiled with re.MULTILINE flag by default."
        ),
    )
    replacement: str = Field(
        ...,
        description=(
            "Text to replace matched patterns with. Can reference regex capture groups using \\1, \\2, etc. If using regex groups in pattern, make sure to preserve them in replacement if needed."
        ),
    )
    count: int | None = Field(
        default=None,
        description=(
            "Maximum number of replacements to make. "
            "Use None to replace all occurrences (default), or specify a number to limit replacements. "
            "Useful when you only want to replace the first N occurrences."
        ),
    )


class GlobalReplacementEditTool(BaseTool):
    """Tool for regex-based replacement editing of files across the entire codebase.

    Use this to make a change across an entire codebase if you have a regex pattern that matches the text you want to replace and are trying to edit a large number of files.
    """

    name: ClassVar[str] = "global_replace"
    description: ClassVar[str] = "Replace text in the entire codebase using regex pattern matching."
    args_schema: ClassVar[type[BaseModel]] = GlobalReplacementEditInput
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(
        self,
        file_pattern: str,
        pattern: str,
        replacement: str,
        count: int | None = None,
    ) -> str:
        result = replacement_edit_global(self.codebase, file_pattern, pattern, replacement, count)
        return result.render()


class ReplacementEditInput(BaseModel):
    """Input for replacement editing."""

    filepath: str = Field(
        ...,
        description=("Path to the file to edit relative to the workspace root. The file must exist and be a text file."),
    )
    pattern: str = Field(
        ...,
        description=(
            "Regular expression pattern to match text that should be replaced. "
            "Supports all Python regex syntax including capture groups (\\1, \\2, etc). "
            "The pattern is compiled with re.MULTILINE flag by default."
        ),
    )
    replacement: str = Field(
        ...,
        description=(
            "Text to replace matched patterns with. Can reference regex capture groups using \\1, \\2, etc. If using regex groups in pattern, make sure to preserve them in replacement if needed."
        ),
    )
    start: int = Field(
        default=1,
        description=("Starting line number (1-indexed, inclusive) to begin replacements from. Use this with 'end' to limit changes to a specific region. Default is 1 (start of file)."),
    )
    end: int = Field(
        default=-1,
        description=(
            "Ending line number (1-indexed, inclusive) to stop replacements at. "
            "Use -1 to indicate end of file. Use this with 'start' to limit changes to a specific region. "
            "Default is -1 (end of file)."
        ),
    )
    count: int | None = Field(
        default=None,
        description=(
            "Maximum number of replacements to make. "
            "Use None to replace all occurrences (default), or specify a number to limit replacements. "
            "Useful when you only want to replace the first N occurrences."
        ),
    )


class ReplacementEditTool(BaseTool):
    """Tool for regex-based replacement editing of files."""

    name: ClassVar[str] = "replace"
    description: ClassVar[str] = "Replace text in a file using regex pattern matching. For files over 300 lines, specify a line range."
    args_schema: ClassVar[type[BaseModel]] = ReplacementEditInput
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(
        self,
        filepath: str,
        pattern: str,
        replacement: str,
        start: int = 1,
        end: int = -1,
        count: int | None = None,
    ) -> str:
        result = replacement_edit(
            self.codebase,
            filepath=filepath,
            pattern=pattern,
            replacement=replacement,
            start=start,
            end=end,
            count=count,
        )
        return result.render()


# Brief description for the Relace Edit tool
_RELACE_EDIT_BRIEF = """Tool for file editing using the Relace Instant Apply API.
This high-speed code generation engine optimizes for real-time performance at 2000 tokens/second.

Provide an edit snippet that describes the changes you want to make, with helpful comments to indicate unchanged sections, like so:
```
// ... keep existing imports ...

// Add new function
function calculateDiscount(price, discountPercent) {
  return price * (discountPercent / 100);
}

// ... keep existing code ...
```

The API will merge your edit snippet with the existing code to produce the final result.
The API key will be automatically retrieved from the RELACE_API environment variable.
"""


class RelaceEditInput(BaseModel):
    """Input for Relace editing."""

    filepath: str = Field(..., description="Path of the file relative to workspace root")
    edit_snippet: str = Field(..., description=RELACE_EDIT_PROMPT)


class RelaceEditTool(BaseTool):
    """Tool for editing files using the Relace Instant Apply API."""

    name: ClassVar[str] = "relace_edit"
    description: ClassVar[str] = _RELACE_EDIT_BRIEF
    args_schema: ClassVar[type[BaseModel]] = RelaceEditInput
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(self, filepath: str, edit_snippet: str) -> str:
        result = relace_edit(self.codebase, filepath, edit_snippet)
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


class SearchFilesByNameInput(BaseModel):
    """Input for searching files by name pattern."""

    pattern: str = Field(..., description="`fd`-compatible glob pattern to search for (e.g. '*.py', 'test_*.py')")


class SearchFilesByNameTool(BaseTool):
    """Tool for searching files by filename across a codebase."""

    name: ClassVar[str] = "search_files_by_name"
    description: ClassVar[str] = """
Search for files and directories by glob pattern across the active codebase. This is useful when you need to:
- Find specific file types (e.g., '*.py', '*.tsx')
- Locate configuration files (e.g., 'package.json', 'requirements.txt')
- Find files with specific names (e.g., 'README.md', 'Dockerfile')
"""
    args_schema: ClassVar[type[BaseModel]] = SearchFilesByNameInput
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase):
        super().__init__(codebase=codebase)

    def _run(self, pattern: str) -> str:
        """Execute the glob pattern search using fd."""
        return search_files_by_name(self.codebase, pattern).render()
