"""Tool for listing directory contents."""

from typing import ClassVar

from pydantic import Field

from codegen import Codebase

from .observation import Observation


class DirectoryInfo(Observation):
    """Information about a directory."""

    path: str = Field(
        description="Path to the directory",
    )
    files: list[str] = Field(
        description="List of files in the directory",
    )
    subdirectories: list[str] = Field(
        description="List of subdirectories",
    )

    str_template: ClassVar[str] = "Directory {path} ({file_count} files, {dir_count} subdirs)"

    def _get_details(self) -> dict[str, int]:
        """Get details for string representation."""
        return {
            "file_count": len(self.files),
            "dir_count": len(self.subdirectories),
        }

    def render(self) -> str:
        """Render directory listing as a file tree."""
        lines = [
            f"[LIST DIRECTORY]: {self.path}",
            "",
        ]

        def add_tree_item(name: str, prefix: str = "", is_last: bool = False) -> str:
            """Helper to format a tree item with proper prefix."""
            marker = "└── " if is_last else "├── "
            return prefix + marker + name

        # Sort files and directories
        items = []
        for f in sorted(self.files):
            items.append((f, False))  # False = not a directory
        for d in sorted(self.subdirectories):
            items.append((d + "/", True))  # True = is a directory

        if not items:
            lines.append("(empty directory)")
            return "\n".join(lines)

        # Generate tree
        for i, (name, is_dir) in enumerate(items):
            is_last = i == len(items) - 1
            lines.append(add_tree_item(name, is_last=is_last))

        return "\n".join(lines)


class ListDirectoryObservation(Observation):
    """Response from listing directory contents."""

    directory_info: DirectoryInfo = Field(
        description="Information about the directory",
    )

    str_template: ClassVar[str] = "{directory_info}"

    def render(self) -> str:
        """Render directory listing."""
        return self.directory_info.render()


def list_directory(codebase: Codebase, path: str) -> ListDirectoryObservation:
    """List the contents of a directory.

    Args:
        codebase: The codebase to operate on
        path: Path to the directory relative to workspace root
    """
    try:
        files, subdirs = codebase.list_directory(path)
        dir_info = DirectoryInfo(
            status="success",
            path=path,
            files=files,
            subdirectories=subdirs,
        )
        return ListDirectoryObservation(
            status="success",
            directory_info=dir_info,
        )
    except Exception as e:
        dir_info = DirectoryInfo(
            status="error",
            error=str(e),
            path=path,
            files=[],
            subdirectories=[],
        )
        return ListDirectoryObservation(
            status="error",
            error=str(e),
            directory_info=dir_info,
        )
