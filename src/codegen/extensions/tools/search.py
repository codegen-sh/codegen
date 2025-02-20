"""Simple text-based search functionality for the codebase.

This performs either a regex pattern match or simple text search across all files in the codebase.
Each matching line will be returned with its line number.
Results are paginated with a default of 10 files per page.
"""

import re
from typing import ClassVar, Optional

from pydantic import Field

from codegen.sdk.core.codebase import Codebase

from .observation import Observation


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


def search(
    codebase: Codebase,
    query: str,
    target_directories: Optional[list[str]] = None,
    file_extensions: Optional[list[str]] = None,
    page: int = 1,
    files_per_page: int = 10,
    use_regex: bool = False,
) -> SearchObservation:
    """Search the codebase using text search or regex pattern matching.

    If use_regex is True, performs a regex pattern match on each line.
    Otherwise, performs a case-insensitive text search.
    Returns matching lines with their line numbers, grouped by file.
    Results are paginated by files, with a default of 10 files per page.

    Args:
        codebase: The codebase to operate on
        query: The text to search for or regex pattern to match
        target_directories: Optional list of directories to search in
        file_extensions: Optional list of file extensions to search (e.g. ['.py', '.ts']).
                        If None, searches all files ('*')
        page: Page number to return (1-based, default: 1)
        files_per_page: Number of files to return per page (default: 10)
        use_regex: Whether to treat query as a regex pattern (default: False)

    Returns:
        SearchObservation containing search results with matches and their sources
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
        # Skip if file doesn't match target directories
        if target_directories and not any(file.filepath.startswith(d) for d in target_directories):
            continue

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
