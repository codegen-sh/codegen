"""Langchain tools for workspace operations."""

from collections.abc import Callable
from typing import Annotated, ClassVar, Literal, Optional

from langchain_core.messages import ToolMessage
from langchain_core.stores import InMemoryBaseStore
from langchain_core.tools import InjectedToolCallId
from langchain_core.tools.base import BaseTool
from langgraph.prebuilt import InjectedStore
from pydantic import BaseModel, Field

from codegen.extensions.tools.bash import run_bash_command
from codegen.extensions.tools.github.checkout_pr import checkout_pr
from codegen.extensions.tools.github.view_pr_checks import view_pr_checks
from codegen.extensions.tools.global_replacement_edit import replacement_edit_global

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

# Base Tool Classes

class ViewFileTool(BaseTool):
    """Tool for viewing file contents."""
    
    name: str = "view_file"
    description: str = "View the content of a file in the codebase"
    codebase: Codebase
    
    def __init__(self, codebase: Codebase):
        """Initialize the tool with a codebase."""
        super().__init__()
        self.codebase = codebase
    
    def _run(self, filepath: str) -> str:
        """Run the tool."""
        result = view_file(self.codebase, filepath)
        if result.status == "error":
            return f"Error: {result.error}"
        return f"File: {filepath}\n\n{result.content}"

class ListDirectoryTool(BaseTool):
    """Tool for listing directory contents."""
    
    name: str = "list_directory"
    description: str = "List the contents of a directory in the codebase"
    codebase: Codebase
    
    def __init__(self, codebase: Codebase):
        """Initialize the tool with a codebase."""
        super().__init__()
        self.codebase = codebase
    
    def _run(self, path: str = ".") -> str:
        """Run the tool."""
        result = list_directory(self.codebase, path)
        if result.status == "error":
            return f"Error: {result.error}"
        
        files_str = "\n".join([f"- {f}" for f in result.files])
        dirs_str = "\n".join([f"- {d}/" for d in result.directories])
        
        return f"Directory: {path}\n\nFiles:\n{files_str}\n\nDirectories:\n{dirs_str}"

class RipGrepTool(BaseTool):
    """Tool for searching code with ripgrep."""
    
    name: str = "search"
    description: str = "Search for patterns in the codebase using ripgrep"
    codebase: Codebase
    
    def __init__(self, codebase: Codebase):
        """Initialize the tool with a codebase."""
        super().__init__()
        self.codebase = codebase
    
    def _run(self, query: str, file_extensions: Optional[list[str]] = None) -> str:
        """Run the tool."""
        result = search(self.codebase, query, file_extensions=file_extensions)
        if result.status == "error":
            return f"Error: {result.error}"
        
        if not result.matches:
            return f"No matches found for query: {query}"
        
        matches_str = "\n\n".join([
            f"File: {match.filepath}\nLine {match.line_number}: {match.line_content}"
            for match in result.matches
        ])
        
        return f"Search results for '{query}':\n\n{matches_str}"

class CreateFileTool(BaseTool):
    """Tool for creating new files."""
    
    name: str = "create_file"
    description: str = "Create a new file in the codebase"
    codebase: Codebase
    
    def __init__(self, codebase: Codebase):
        """Initialize the tool with a codebase."""
        super().__init__()
        self.codebase = codebase
    
    def _run(self, filepath: str, content: str) -> str:
        """Run the tool."""
        result = create_file(self.codebase, filepath, content)
        if result.status == "error":
            return f"Error: {result.error}"
        return f"Successfully created file: {filepath}"

class DeleteFileTool(BaseTool):
    """Tool for deleting files."""
    
    name: str = "delete_file"
    description: str = "Delete a file from the codebase"
    codebase: Codebase
    
    def __init__(self, codebase: Codebase):
        """Initialize the tool with a codebase."""
        super().__init__()
        self.codebase = codebase
    
    def _run(self, filepath: str) -> str:
        """Run the tool."""
        result = delete_file(self.codebase, filepath)
        if result.status == "error":
            return f"Error: {result.error}"
        return f"Successfully deleted file: {filepath}"

class RenameFileTool(BaseTool):
    """Tool for renaming files."""
    
    name: str = "rename_file"
    description: str = "Rename a file in the codebase"
    codebase: Codebase
    
    def __init__(self, codebase: Codebase):
        """Initialize the tool with a codebase."""
        super().__init__()
        self.codebase = codebase
    
    def _run(self, old_path: str, new_path: str) -> str:
        """Run the tool."""
        result = rename_file(self.codebase, old_path, new_path)
        if result.status == "error":
            return f"Error: {result.error}"
        return f"Successfully renamed file from {old_path} to {new_path}"

class MoveSymbolTool(BaseTool):
    """Tool for moving symbols between files."""
    
    name: str = "move_symbol"
    description: str = "Move a symbol (function, class, etc.) from one file to another"
    codebase: Codebase
    
    def __init__(self, codebase: Codebase):
        """Initialize the tool with a codebase."""
        super().__init__()
        self.codebase = codebase
    
    def _run(self, symbol_name: str, source_file: str, target_file: str) -> str:
        """Run the tool."""
        result = move_symbol(self.codebase, symbol_name, source_file, target_file)
        if result.status == "error":
            return f"Error: {result.error}"
        return f"Successfully moved symbol {symbol_name} from {source_file} to {target_file}"

class RevealSymbolTool(BaseTool):
    """Tool for revealing symbol definitions."""
    
    name: str = "reveal_symbol"
    description: str = "Find the definition of a symbol in the codebase"
    codebase: Codebase
    
    def __init__(self, codebase: Codebase):
        """Initialize the tool with a codebase."""
        super().__init__()
        self.codebase = codebase
    
    def _run(self, symbol_name: str) -> str:
        """Run the tool."""
        result = reveal_symbol(self.codebase, symbol_name)
        if result.status == "error":
            return f"Error: {result.error}"
        
        definitions_str = "\n\n".join([
            f"File: {definition.filepath}\nLine {definition.line_number}: {definition.line_content}"
            for definition in result.definitions
        ])
        
        return f"Definitions for symbol '{symbol_name}':\n\n{definitions_str}"

class ReplacementEditTool(BaseTool):
    """Tool for making replacement edits to files."""
    
    name: str = "replacement_edit"
    description: str = "Make a replacement edit to a file"
    codebase: Codebase
    
    def __init__(self, codebase: Codebase):
        """Initialize the tool with a codebase."""
        super().__init__()
        self.codebase = codebase
    
    def _run(self, filepath: str, start_line: int, end_line: int, replacement: str) -> str:
        """Run the tool."""
        result = replacement_edit(self.codebase, filepath, start_line, end_line, replacement)
        if result.status == "error":
            return f"Error: {result.error}"
        return f"Successfully edited file {filepath} from line {start_line} to {end_line}"

class GlobalReplacementEditTool(BaseTool):
    """Tool for making global replacement edits."""
    
    name: str = "global_replacement_edit"
    description: str = "Make a global replacement edit across multiple files"
    codebase: Codebase
    
    def __init__(self, codebase: Codebase):
        """Initialize the tool with a codebase."""
        super().__init__()
        self.codebase = codebase
    
    def _run(self, pattern: str, replacement: str, file_extensions: Optional[list[str]] = None) -> str:
        """Run the tool."""
        result = replacement_edit_global(self.codebase, pattern, replacement, file_extensions=file_extensions)
        if result.status == "error":
            return f"Error: {result.error}"
        
        if not result.files_changed:
            return f"No files were changed for pattern: {pattern}"
        
        files_str = "\n".join([f"- {f}" for f in result.files_changed])
        return f"Successfully made global replacement of '{pattern}' with '{replacement}' in files:\n{files_str}"

class RelaceEditTool(BaseTool):
    """Tool for making edits using Relace."""
    
    name: str = "relace_edit"
    description: str = "Edit a file using the Relace Instant Apply API"
    codebase: Codebase
    
    def __init__(self, codebase: Codebase):
        """Initialize the tool with a codebase."""
        super().__init__()
        self.codebase = codebase
    
    def _run(self, filepath: str, edit_snippet: str) -> str:
        """Run the tool."""
        result = relace_edit(self.codebase, filepath, edit_snippet)
        if result.status == "error":
            return f"Error: {result.error}"
        return f"Successfully edited file {filepath} using Relace"

class ReflectionTool(BaseTool):
    """Tool for agent reflection."""
    
    name: str = "reflection"
    description: str = "Reflect on the current state of the task and plan next steps"
    codebase: Codebase
    
    def __init__(self, codebase: Codebase):
        """Initialize the tool with a codebase."""
        super().__init__()
        self.codebase = codebase
    
    def _run(
        self, 
        context_summary: str, 
        findings_so_far: str, 
        current_challenges: str = "", 
        reflection_focus: Optional[str] = None
    ) -> str:
        """Run the tool."""
        result = perform_reflection(
            self.codebase, 
            context_summary, 
            findings_so_far, 
            current_challenges, 
            reflection_focus
        )
        if result.status == "error":
            return f"Error: {result.error}"
        return result.reflection

class SearchFilesByNameTool(BaseTool):
    """Tool for searching files by name."""
    
    name: str = "search_files_by_name"
    description: str = "Search for files by name pattern"
    codebase: Codebase
    
    def __init__(self, codebase: Codebase):
        """Initialize the tool with a codebase."""
        super().__init__()
        self.codebase = codebase
    
    def _run(self, pattern: str) -> str:
        """Run the tool."""
        result = search_files_by_name(self.codebase, pattern)
        if result.status == "error":
            return f"Error: {result.error}"
        
        if not result.files:
            return f"No files found matching pattern: {pattern}"
        
        files_str = "\n".join([f"- {f}" for f in result.files])
        return f"Files matching pattern '{pattern}':\n{files_str}"

# GitHub PR Review Tools

class GithubViewPRTool(BaseTool):
    """Tool for viewing PR contents."""
    
    name: str = "view_pr"
    description: str = "View the contents of a GitHub pull request"
    codebase: Codebase
    
    def __init__(self, codebase: Codebase):
        """Initialize the tool with a codebase."""
        super().__init__()
        self.codebase = codebase
    
    def _run(self, pr_id: int) -> str:
        """Run the tool."""
        result = view_pr(self.codebase, pr_id)
        if result.status == "error":
            return f"Error: {result.error}"
        
        return f"PR #{result.pr_id}\n\nPatch:\n{result.patch}\n\nModified symbols: {', '.join(result.modified_symbols)}"

class GithubCreatePRCommentTool(BaseTool):
    """Tool for creating PR comments."""
    
    name: str = "create_pr_comment"
    description: str = "Create a general comment on a GitHub pull request"
    codebase: Codebase
    
    def __init__(self, codebase: Codebase):
        """Initialize the tool with a codebase."""
        super().__init__()
        self.codebase = codebase
    
    def _run(self, pr_number: int, body: str) -> str:
        """Run the tool."""
        result = create_pr_comment(self.codebase, pr_number, body)
        if result.status == "error":
            return f"Error: {result.error}"
        return f"Successfully added comment to PR #{result.pr_number}"

class GithubCreatePRReviewCommentTool(BaseTool):
    """Tool for creating PR review comments."""
    
    name: str = "create_pr_review_comment"
    description: str = "Create an inline review comment on a specific line in a GitHub pull request"
    codebase: Codebase
    
    def __init__(self, codebase: Codebase):
        """Initialize the tool with a codebase."""
        super().__init__()
        self.codebase = codebase
    
    def _run(
        self, 
        pr_number: int, 
        body: str, 
        commit_sha: str, 
        path: str, 
        line: int, 
        start_line: Optional[int] = None
    ) -> str:
        """Run the tool."""
        result = create_pr_review_comment(
            self.codebase, 
            pr_number, 
            body, 
            commit_sha, 
            path, 
            line, 
            start_line
        )
        if result.status == "error":
            return f"Error: {result.error}"
        return f"Successfully added review comment to PR #{result.pr_number} at {result.path}:{result.line}"
