"""Tool for listing directory contents."""

from typing import ClassVar

from langchain_core.messages import ToolMessage
from pydantic import Field

from codegen.extensions.tools.observation import Observation
from codegen.extensions.tools.tool_output_types import ListDirectoryArtifacts
from codegen.sdk.core.codebase import Codebase
from codegen.sdk.core.directory import Directory


class DirectoryInfo(Observation):
    """Information about a directory."""

    name: str = Field(
        description="Name of the directory",
    )
    path: str = Field(
        description="Full path to the directory",
    )
    files: list[str] | None = Field(
        default=None,
        description="List of files in this directory (None if at max depth)",
    )
    subdirectories: list["DirectoryInfo"] = Field(
        default_factory=list,
        description="List of subdirectories",
    )
    is_leaf: bool = Field(
        default=False,
        description="Whether this is a leaf node (at max depth)",
    )
    depth: int = Field(
        default=0,
        description="Current depth in the tree",
    )
    max_depth: int = Field(
        default=1,
        description="Maximum depth allowed",
    )

    str_template: ClassVar[str] = "Directory {path} ({file_count} files, {dir_count} subdirs)"

    def _get_details(self) -> dict[str, int]:
        """Get details for string representation."""
        return {
            "file_count": len(self.files or []),
            "dir_count": len(self.subdirectories),
        }

    def render_as_string(self) -> str:
        """Render directory listing as a file tree."""
        lines = [
            f"[LIST DIRECTORY]: {self.path}",
            "",
        ]

        def add_tree_item(name: str, prefix: str = "", is_last: bool = False) -> tuple[str, str]:
            """Helper to format a tree item with proper prefix."""
            marker = "└── " if is_last else "├── "
            indent = "    " if is_last else "│   "
            return prefix + marker + name, prefix + indent

        def build_tree(items: list[tuple[str, bool, "DirectoryInfo | None"]], prefix: str = "") -> list[str]:
            """Recursively build tree with proper indentation."""
            if not items:
                return []

            result = []
            for i, (name, is_dir, dir_info) in enumerate(items):
                is_last = i == len(items) - 1
                line, new_prefix = add_tree_item(name, prefix, is_last)
                result.append(line)

                # If this is a directory and not a leaf node, show its contents
                if dir_info and not dir_info.is_leaf:
                    subitems = []
                    # Add files first
                    if dir_info.files:
                        for f in sorted(dir_info.files):
                            subitems.append((f, False, None))
                    # Then add subdirectories
                    for d in dir_info.subdirectories:
                        subitems.append((d.name + "/", True, d))

                    result.extend(build_tree(subitems, new_prefix))

            return result

        # Sort files and directories
        items = []
        if self.files:
            for f in sorted(self.files):
                items.append((f, False, None))
        for d in self.subdirectories:
            items.append((d.name + "/", True, d))

        if not items:
            lines.append("(empty directory)")
            return "\n".join(lines)

        # Generate tree
        lines.extend(build_tree(items))

        return "\n".join(lines)

    def to_artifacts(self) -> ListDirectoryArtifacts:
        """Convert directory info to artifacts for UI."""
        artifacts: ListDirectoryArtifacts = {
            "dirpath": self.path,
            "name": self.name,
            "is_leaf": self.is_leaf,
            "depth": self.depth,
            "max_depth": self.max_depth,
        }

        if self.files is not None:
            artifacts["files"] = self.files
            artifacts["file_paths"] = [f"{self.path}/{f}" for f in self.files]

        if self.subdirectories:
            artifacts["subdirs"] = [d.name for d in self.subdirectories]
            artifacts["subdir_paths"] = [d.path for d in self.subdirectories]

        return artifacts


class ListDirectoryObservation(Observation):
    """Response from listing directory contents."""

    directory_info: DirectoryInfo = Field(
        description="Information about the directory",
    )

    str_template: ClassVar[str] = "{directory_info}"

    def render(self, tool_call_id: str) -> ToolMessage:
        """Render directory listing with artifacts for UI."""
        if self.status == "error":
            error_artifacts: ListDirectoryArtifacts = {
                "dirpath": self.directory_info.path,
                "name": self.directory_info.name,
                "error": self.error,
            }
            return ToolMessage(
                content=f"[ERROR LISTING DIRECTORY]: {self.directory_info.path}: {self.error}",
                status=self.status,
                name="list_directory",
                artifact=error_artifacts,
                tool_call_id=tool_call_id,
            )

        return ToolMessage(
            content=self.directory_info.render_as_string(),
            status=self.status,
            name="list_directory",
            artifact=self.directory_info.to_artifacts(),
            tool_call_id=tool_call_id,
        )


def list_directory(codebase: Codebase, path: str = "./", depth: int = 2) -> ListDirectoryObservation:
    """List contents of a directory.

    Args:
        codebase: The codebase to operate on
        path: Path to directory relative to workspace root
        depth: How deep to traverse the directory tree. Default is 1 (immediate children only).
               Use -1 for unlimited depth.
    """
    try:
        directory = codebase.get_directory(path)
    except ValueError:
        return ListDirectoryObservation(
            status="error",
            error=f"Directory not found: {path}",
            directory_info=DirectoryInfo(
                status="error",
                name=path.split("/")[-1],
                path=path,
                files=[],
                subdirectories=[],
            ),
        )

    def get_directory_info(dir_obj: Directory, current_depth: int, max_depth: int) -> DirectoryInfo:
        """Helper function to get directory info recursively."""
        # Get direct files (always include files unless at max depth)
        all_files = []
        for file_name in dir_obj.file_names:
            all_files.append(file_name)

        # Get direct subdirectories
        subdirs = []
        for subdir in dir_obj.subdirectories(recursive=True):
            # Only include direct descendants
            if subdir.parent == dir_obj:
                if current_depth > 1 or current_depth == -1:
                    # For deeper traversal, get full directory info
                    new_depth = current_depth - 1 if current_depth > 1 else -1
                    subdirs.append(get_directory_info(subdir, new_depth, max_depth))
                else:
                    # At max depth, return a leaf node
                    subdirs.append(
                        DirectoryInfo(
                            status="success",
                            name=subdir.name,
                            path=subdir.dirpath,
                            files=None,  # Don't include files at max depth
                            is_leaf=True,
                            depth=current_depth,
                            max_depth=max_depth,
                        )
                    )

        return DirectoryInfo(
            status="success",
            name=dir_obj.name,
            path=dir_obj.dirpath,
            files=sorted(all_files),
            subdirectories=subdirs,
            depth=current_depth,
            max_depth=max_depth,
        )

    dir_info = get_directory_info(directory, depth, depth)
    return ListDirectoryObservation(
        status="success",
        directory_info=dir_info,
    )
