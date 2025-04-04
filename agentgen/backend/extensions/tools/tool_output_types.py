"""Type definitions for tool outputs."""

from typing import Optional, TypedDict


class EditFileArtifacts(TypedDict, total=False):
    """Artifacts for edit file operations.

    All fields are optional to support both success and error cases.
    """

    filepath: str  # Path to the edited file
    diff: Optional[str]  # Diff of changes made to the file
    error: Optional[str]  # Error message (only present on error)


class ViewFileArtifacts(TypedDict, total=False):
    """Artifacts for view file operations.

    All fields are optional to support both success and error cases.
    Includes metadata useful for UI logging and pagination.
    """

    filepath: str  # Path to the viewed file
    start_line: Optional[int]  # Starting line number viewed
    end_line: Optional[int]  # Ending line number viewed
    content: Optional[str]  # Content of the file
    total_lines: Optional[int]  # Total number of lines in file
    has_more: Optional[bool]  # Whether there are more lines to view
    max_lines_per_page: Optional[int]  # Maximum lines that can be viewed at once
    file_size: Optional[int]  # Size of file in bytes
    error: Optional[str]  # Error message (only present on error)


class ListDirectoryArtifacts(TypedDict, total=False):
    """Artifacts for directory listing operations.

    All fields are optional to support both success and error cases.
    Includes metadata useful for UI tree view and navigation.
    """

    dirpath: str  # Full path to the directory
    name: str  # Name of the directory
    files: Optional[list[str]]  # List of files in this directory
    file_paths: Optional[list[str]]  # Full paths to files in this directory
    subdirs: Optional[list[str]]  # List of subdirectory names
    subdir_paths: Optional[list[str]]  # Full paths to subdirectories
    is_leaf: Optional[bool]  # Whether this is a leaf node (at max depth)
    depth: Optional[int]  # Current depth in the tree
    max_depth: Optional[int]  # Maximum depth allowed
    error: Optional[str]  # Error message (only present on error)


class SearchMatch(TypedDict, total=False):
    """Information about a single search match."""

    filepath: str  # Path to the file containing the match
    line_number: int  # 1-based line number of the match
    line: str  # The full line containing the match
    match: str  # The specific text that matched


class SearchArtifacts(TypedDict, total=False):
    """Artifacts for search operations.

    All fields are optional to support both success and error cases.
    Includes metadata useful for UI search results and navigation.
    """

    query: str  # Search query that was used
    page: int  # Current page number (1-based)
    total_pages: int  # Total number of pages available
    total_files: int  # Total number of files with matches
    files_per_page: int  # Number of files shown per page
    matches: list[SearchMatch]  # List of matches with file paths and line numbers
    file_paths: list[str]  # List of files containing matches
    error: Optional[str]  # Error message (only present on error)


class SemanticEditArtifacts(TypedDict, total=False):
    """Artifacts for semantic edit operations.

    All fields are optional to support both success and error cases.
    Includes metadata useful for UI diff view and file content.
    """

    filepath: str  # Path to the edited file
    diff: Optional[str]  # Unified diff of changes made to the file
    new_content: Optional[str]  # New content of the file after edits
    line_count: Optional[int]  # Total number of lines in the edited file
    error: Optional[str]  # Error message (only present on error)


class RelaceEditArtifacts(TypedDict, total=False):
    """Artifacts for relace edit operations.

    All fields are optional to support both success and error cases.
    Includes metadata useful for UI diff view and file content.
    """

    filepath: str  # Path to the edited file
    diff: Optional[str]  # Unified diff of changes made to the file
    new_content: Optional[str]  # New content of the file after edits
    line_count: Optional[int]  # Total number of lines in the edited file
    error: Optional[str]  # Error message (only present on error)
