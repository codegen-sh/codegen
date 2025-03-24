import math
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
    files_per_page: int | float = Field(
        description="Number of files shown per page",
    )

    str_template: ClassVar[str] = "Found {total_files} files matching pattern: {pattern} (page {page}/{total_pages})"

    @property
    def total(self) -> int:
        return self.total_files


def search_files_by_name(
    codebase: Codebase,
    pattern: str,
    page: int = 1,
    files_per_page: int | float = 10,
) -> SearchFilesByNameResultObservation:
    """Search for files by name pattern in the codebase.

    Args:
        codebase: The codebase to search in
        pattern: Glob pattern to search for (e.g. "*.py", "test_*.py", "**/.github/workflows/*.yml")
        page: Page number to return (1-based, default: 1)
        files_per_page: Number of files to return per page (default: 10)
    """
    try:
        # Validate pagination parameters
        if page < 1:
            page = 1
        if files_per_page is not None and files_per_page < 1:
            files_per_page = 20

        # Handle patterns that start with **/ by removing the leading ** and searching from root
        # This is a common pattern for finding files at any depth
        search_pattern = pattern
        search_dir = codebase.repo_path

        if pattern.startswith("**/"):
            # Remove the **/ prefix for the search pattern
            search_pattern = pattern[3:]

        if shutil.which("fd") is None:
            logger.warning("fd is not installed, falling back to find")

            # For find, we need to handle the pattern differently
            find_args = ["find", ".", "-type", "f"]

            # If the pattern contains **, we need to use -path instead of -name
            if "**" in pattern:
                # Convert ** glob pattern to find's -path syntax
                path_pattern = pattern.replace("**/", "**/")
                find_args.extend(["-path", f"*{search_pattern}"])
            else:
                # Use -name for simple patterns
                find_args.extend(["-name", search_pattern])

            results = subprocess.check_output(
                find_args,
                cwd=search_dir,
                timeout=30,
            )
            all_files = [path.removeprefix("./") for path in results.decode("utf-8").strip().split("\n")] if results.strip() else []

        else:
            logger.info(f"Searching for files with pattern: {pattern}")

            # fd handles ** patterns natively
            fd_args = ["fd", "-t", "f", "-g", pattern]

            results = subprocess.check_output(
                fd_args,
                cwd=search_dir,
                timeout=30,
            )
            all_files = results.decode("utf-8").strip().split("\n") if results.strip() else []

        # Filter out empty strings
        all_files = [f for f in all_files if f]

        # Sort files for consistent pagination
        all_files.sort()

        # Calculate pagination
        total_files = len(all_files)
        if files_per_page == math.inf:
            files_per_page = total_files
            total_pages = 1
        else:
            total_pages = (total_files + files_per_page - 1) // files_per_page if total_files > 0 else 1

        # Ensure page is within valid range
        page = min(page, total_pages)

        # Get paginated results
        start_idx = (page - 1) * files_per_page
        end_idx = start_idx + files_per_page
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
