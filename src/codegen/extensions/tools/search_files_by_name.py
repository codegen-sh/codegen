import shutil
import subprocess
from typing import ClassVar

from pydantic import Field

from codegen.extensions.tools.observation import Observation
from codegen.sdk.core.codebase import Codebase
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class SearchFilesByNameResultObservation(Observation):
    """Response from searching files by filename pattern."""

    pattern: str = Field(
        description="The glob pattern that was searched for",
    )
    files: list[str] = Field(
        description="List of matching file paths",
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

    str_template: ClassVar[str] = "Found {total_files} files matching pattern: {pattern}"

    @property
    def total(self) -> int:
        return self.total_files

    def render(self) -> str:
        """Render search results in a readable format."""
        if self.status == "error":
            return f"[SEARCH FILES ERROR]: {self.error}"

        lines = [
            f"[SEARCH FILES RESULTS]: {self.pattern}",
            f"Found {self.total_files} files matching pattern (showing page {self.page} of {self.total_pages})",
            "",
        ]

        if not self.files:
            lines.append("No matching files found")
            return "\n".join(lines)

        for file in self.files:
            lines.append(f"📄 {file}")

        if self.total_pages > 1:
            lines.append("")
            lines.append(f"Page {self.page}/{self.total_pages} (use page parameter to see more results)")

        return "\n".join(lines)


def search_files_by_name(
    codebase: Codebase,
    pattern: str,
    page: int = 1,
    files_per_page: int = 50,
) -> SearchFilesByNameResultObservation:
    """Search for files by name pattern in the codebase.

    Args:
        codebase: The codebase to search in
        pattern: Glob pattern to search for (e.g. "*.py", "test_*.py")
        page: Page number to return (1-based, default: 1)
        files_per_page: Number of files to return per page (default: 50)
    """
    # Validate pagination parameters
    if page < 1:
        page = 1
    if files_per_page < 1:
        files_per_page = 50

    try:
        if shutil.which("fd") is None:
            logger.warning("fd is not installed, falling back to find")
            results = subprocess.check_output(
                ["find", "-name", pattern],
                cwd=codebase.repo_path,
                timeout=30,
            )
            all_files = [path.removeprefix("./") for path in results.decode("utf-8").strip().split("\n")] if results.strip() else []

        else:
            logger.info(f"Searching for files with pattern: {pattern}")
            results = subprocess.check_output(
                ["fd", "-g", pattern],
                cwd=codebase.repo_path,
                timeout=30,
            )
            all_files = results.decode("utf-8").strip().split("\n") if results.strip() else []

        # Sort files alphabetically for consistent pagination
        all_files.sort()

        # Calculate pagination
        total_files = len(all_files)
        total_pages = (total_files + files_per_page - 1) // files_per_page
        start_idx = (page - 1) * files_per_page
        end_idx = start_idx + files_per_page

        # Get the current page of results
        paginated_files = all_files[start_idx:end_idx]

        return SearchFilesByNameResultObservation(
            status="success",
            pattern=pattern,
            files=paginated_files,
            page=page,
            total_pages=total_pages,
            total_files=total_files,
            files_per_page=files_per_page,
        )

    except Exception as e:
        return SearchFilesByNameResultObservation(
            status="error",
            error=f"Error searching files: {e!s}",
            pattern=pattern,
            files=[],
            page=page,
            total_pages=0,
            total_files=0,
            files_per_page=files_per_page,
        )
