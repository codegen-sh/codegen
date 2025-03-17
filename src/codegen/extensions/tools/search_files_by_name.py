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

    str_template: ClassVar[str] = "Found {total} files matching pattern: {pattern}"

    @property
    def total(self) -> int:
        return len(self.files)


def search_files_by_name(
    codebase: Codebase,
    pattern: str,
) -> SearchFilesByNameResultObservation:
    """Search for files by name pattern in the codebase.

    Args:
        codebase: The codebase to search in
        pattern: Glob pattern to search for (e.g. "*.py", "test_*.py")
    """
    try:
        if shutil.which("fd") is None:
            logger.warning("fd is not installed, falling back to find")
            results = subprocess.check_output(
                ["find", "-name", pattern],
                cwd=codebase.repo_path,
                timeout=30,
            )
            files = [path.removeprefix("./") for path in results.decode("utf-8").strip().split("\n")] if results.strip() else []

        else:
            logger.info(f"Searching for files with pattern: {pattern}")
            results = subprocess.check_output(
                ["fd", "-g", pattern],
                cwd=codebase.repo_path,
                timeout=30,
            )
            files = results.decode("utf-8").strip().split("\n") if results.strip() else []

        return SearchFilesByNameResultObservation(
            status="success",
            pattern=pattern,
            files=files,
        )

    except Exception as e:
        return SearchFilesByNameResultObservation(
            status="error",
            error=f"Error searching files: {e!s}",
            pattern=pattern,
            files=[],
        )
