"""Simple text-based search functionality for the codebase.

This performs either a regex pattern match or simple text search across all files in the codebase.
Each matching line will be returned with its line number.
Results are paginated with a default of 10 files per page.
"""

import logging
import os
import re
import subprocess
from typing import ClassVar

from pydantic import Field

from codegen.sdk.core.codebase import Codebase

from .observation import Observation

logger = logging.getLogger(__name__)


class SearchMatch(Observation):
    """Information about a single line match."""

    line_number: int = Field(
        description="1-based line number of the match",
    )
    line: str = Field(
        description="The full line containing the match",
    )
    match: str = Field(
        description="The specific text that matched",
    )
    str_template: ClassVar[str] = "Line {line_number}: {match}"

    def render(self) -> str:
        """Render match in a VSCode-like format."""
        return f"{self.line_number:>4}:  {self.line}"


class SearchFileResult(Observation):
    """Search results for a single file."""

    filepath: str = Field(
        description="Path to the file containing matches",
    )
    matches: list[SearchMatch] = Field(
        description="List of matches found in this file",
    )

    str_template: ClassVar[str] = "{filepath}: {match_count} matches"

    def render(self) -> str:
        """Render file results in a VSCode-like format."""
        lines = [
            f"📄 {self.filepath}",
        ]
        for match in self.matches:
            lines.append(match.render())
        return "\n".join(lines)

    def _get_details(self) -> dict[str, str | int]:
        """Get details for string representation."""
        return {"match_count": len(self.matches)}


class SearchObservation(Observation):
    """Response from searching the codebase."""

    query: str = Field(
        description="The search query that was used",
    )
    page: int = Field(
        description="Current page number (1-based)",
    )
    total_pages: int = Field(
        description="Total number of pages available",
    )
    total_files: int = Field(
        description="Total number of files with matches",
    )
    files_per_page: int = Field(
        description="Number of files shown per page",
    )
    results: list[SearchFileResult] = Field(
        description="Search results for this page",
    )

    str_template: ClassVar[str] = "Found {total_files} files with matches for '{query}' (page {page}/{total_pages})"

    def render(self) -> str:
        """Render search results in a VSCode-like format."""
        if self.status == "error":
            return f"[SEARCH ERROR]: {self.error}"

        lines = [
            f"[SEARCH RESULTS]: {self.query}",
            f"Found {self.total_files} files with matches (showing page {self.page} of {self.total_pages})",
            "",
        ]

        if not self.results:
            lines.append("No matches found")
            return "\n".join(lines)

        for result in self.results:
            lines.append(result.render())
            lines.append("")  # Add blank line between files

        if self.total_pages > 1:
            lines.append(f"Page {self.page}/{self.total_pages} (use page parameter to see more results)")

        return "\n".join(lines)


def _search_with_ripgrep(
    codebase: Codebase,
    query: str,
    file_extensions: list[str] | None = None,
    page: int = 1,
    files_per_page: int = 10,
    use_regex: bool = False,
) -> SearchObservation:
    """Search the codebase using ripgrep.

    This is faster than the Python implementation, especially for large codebases.
    """
    # Build ripgrep command
    cmd = ["rg", "--line-number"]

    # Add case insensitivity if not using regex
    if not use_regex:
        cmd.append("--fixed-strings")
        cmd.append("--ignore-case")

    # Add file extensions if specified
    if file_extensions:
        for ext in file_extensions:
            # Remove leading dot if present
            ext = ext[1:] if ext.startswith(".") else ext
            cmd.extend(["--type-add", f"custom:*.{ext}", "--type", "custom"])

    # Add target directories if specified
    search_path = str(codebase.repo_path)

    # Add the query and path
    cmd.append(f"{query}")
    cmd.append(search_path)

    # Run ripgrep
    try:
        logger.info(f"Running ripgrep command: {' '.join(cmd)}")
        # Use text mode and UTF-8 encoding
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,  # Don't raise exception on non-zero exit code (no matches)
        )

        # Parse the output
        all_results: dict[str, list[SearchMatch]] = {}

        # ripgrep returns non-zero exit code when no matches are found
        if result.returncode != 0 and result.returncode != 1:
            # Real error occurred
            return SearchObservation(
                status="error",
                error=f"ripgrep error: {result.stderr}",
                query=query,
                page=page,
                total_pages=0,
                total_files=0,
                files_per_page=files_per_page,
                results=[],
            )

        # Parse output lines
        for line in result.stdout.splitlines():
            # ripgrep output format: file:line:content
            parts = line.split(":", 2)
            if len(parts) < 3:
                continue

            filepath, line_number_str, content = parts

            # Convert to relative path within the codebase
            rel_path = os.path.relpath(filepath, codebase.repo_path)

            try:
                line_number = int(line_number_str)

                # Find the actual match text
                match_text = query
                if use_regex:
                    # For regex, we need to find what actually matched
                    # This is a simplification - ideally we'd use ripgrep's --json option
                    # to get the exact match positions
                    pattern = re.compile(query)
                    match_obj = pattern.search(content)
                    if match_obj:
                        match_text = match_obj.group(0)

                # Create or append to file results
                if rel_path not in all_results:
                    all_results[rel_path] = []

                all_results[rel_path].append(
                    SearchMatch(
                        status="success",
                        line_number=line_number,
                        line=content.strip(),
                        match=match_text,
                    )
                )
            except ValueError:
                # Skip lines with invalid line numbers
                continue

        # Convert to SearchFileResult objects
        file_results = []
        for filepath, matches in all_results.items():
            file_results.append(
                SearchFileResult(
                    status="success",
                    filepath=filepath,
                    matches=sorted(matches, key=lambda x: x.line_number),
                )
            )

        # Sort results by filepath
        file_results.sort(key=lambda x: x.filepath)

        # Calculate pagination
        total_files = len(file_results)
        total_pages = (total_files + files_per_page - 1) // files_per_page
        start_idx = (page - 1) * files_per_page
        end_idx = start_idx + files_per_page

        # Get the current page of results
        paginated_results = file_results[start_idx:end_idx]

        return SearchObservation(
            status="success",
            query=query,
            page=page,
            total_pages=total_pages,
            total_files=total_files,
            files_per_page=files_per_page,
            results=paginated_results,
        )

    except (subprocess.SubprocessError, FileNotFoundError) as e:
        # Let the caller handle this by falling back to Python implementation
        raise


def _search_with_python(
    codebase: Codebase,
    query: str,
    file_extensions: list[str] | None = None,
    page: int = 1,
    files_per_page: int = 10,
    use_regex: bool = False,
) -> SearchObservation:
    """Search the codebase using Python's regex engine.

    This is a fallback for when ripgrep is not available.
    """
    # Validate pagination parameters
    if page < 1:
        page = 1
    if files_per_page < 1:
        files_per_page = 10

    # Prepare the search pattern
    if use_regex:
        try:
            pattern = re.compile(query)
        except re.error as e:
            return SearchObservation(
                status="error",
                error=f"Invalid regex pattern: {e!s}",
                query=query,
                page=page,
                total_pages=0,
                total_files=0,
                files_per_page=files_per_page,
                results=[],
            )
    else:
        # For non-regex searches, escape special characters and make case-insensitive
        pattern = re.compile(re.escape(query), re.IGNORECASE)

    # Handle file extensions
    extensions = file_extensions if file_extensions is not None else "*"

    all_results = []
    for file in codebase.files(extensions=extensions):
        # Skip binary files
        try:
            content = file.content
        except ValueError:  # File is binary
            continue

        file_matches = []
        # Split content into lines and store with line numbers (1-based)
        lines = enumerate(content.splitlines(), 1)

        # Search each line for the pattern
        for line_number, line in lines:
            match = pattern.search(line)
            if match:
                file_matches.append(
                    SearchMatch(
                        status="success",
                        line_number=line_number,
                        line=line.strip(),
                        match=match.group(0),
                    )
                )

        if file_matches:
            all_results.append(
                SearchFileResult(
                    status="success",
                    filepath=file.filepath,
                    matches=sorted(file_matches, key=lambda x: x.line_number),
                )
            )

    # Sort all results by filepath
    all_results.sort(key=lambda x: x.filepath)

    # Calculate pagination
    total_files = len(all_results)
    total_pages = (total_files + files_per_page - 1) // files_per_page
    start_idx = (page - 1) * files_per_page
    end_idx = start_idx + files_per_page

    # Get the current page of results
    paginated_results = all_results[start_idx:end_idx]

    return SearchObservation(
        status="success",
        query=query,
        page=page,
        total_pages=total_pages,
        total_files=total_files,
        files_per_page=files_per_page,
        results=paginated_results,
    )


def search(
    codebase: Codebase,
    query: str,
    file_extensions: list[str] | None = None,
    page: int = 1,
    files_per_page: int = 10,
    use_regex: bool = False,
) -> SearchObservation:
    """Search the codebase using text search or regex pattern matching.

    Uses ripgrep for performance when available, with fallback to Python's regex engine.
    If use_regex is True, performs a regex pattern match on each line.
    Otherwise, performs a case-insensitive text search.
    Returns matching lines with their line numbers, grouped by file.
    Results are paginated by files, with a default of 10 files per page.

    Args:
        codebase: The codebase to operate on
        query: The text to search for or regex pattern to match
        file_extensions: Optional list of file extensions to search (e.g. ['.py', '.ts']).
                        If None, searches all files ('*')
        page: Page number to return (1-based, default: 1)
        files_per_page: Number of files to return per page (default: 10)
        use_regex: Whether to treat query as a regex pattern (default: False)

    Returns:
        SearchObservation containing search results with matches and their sources
    """
    # Try to use ripgrep first
    try:
        return _search_with_ripgrep(codebase, query, file_extensions, page, files_per_page, use_regex)
    except (FileNotFoundError, subprocess.SubprocessError):
        # Fall back to Python implementation if ripgrep fails or isn't available
        return _search_with_python(codebase, query, file_extensions, page, files_per_page, use_regex)
