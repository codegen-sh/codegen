import os
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Generic, Literal, Self

from codegen.sdk._proxy import proxy_property
from codegen.sdk.core.interfaces.has_symbols import (
    FilesParam,
    HasSymbols,
    TClass,
    TFile,
    TFunction,
    TGlobalVar,
    TImport,
    TImportStatement,
    TSymbol,
)
from codegen.sdk.core.utils.cache_utils import cached_generator
from codegen.sdk.enums import NodeType
from codegen.sdk.extensions.sort import sort_editables
from codegen.shared.decorators.docs import apidoc, noapidoc
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


if TYPE_CHECKING:
    from codegen.sdk.codebase.codebase_context import CodebaseContext


@apidoc
class Directory(
    HasSymbols[TFile, TSymbol, TImportStatement, TGlobalVar, TClass, TFunction, TImport],
    Generic[TFile, TSymbol, TImportStatement, TGlobalVar, TClass, TFunction, TImport],
):
    """Directory representation for codebase.

    GraphSitter abstraction of a file directory that can be used to look for files and symbols within a specific directory.

    Attributes:
        path: Absolute path of the directory.
        dirpath: Relative path of the directory.
        parent: The parent directory, if any.
        items: A dictionary containing files and subdirectories within the directory.
    """

    ctx: "CodebaseContext"
    path: Path  # Absolute Path
    dirpath: str  # Relative Path
    _files: list[str]  # List of file names
    _subdirectories: list[str]  # List of subdirectory names

    def __init__(self, ctx: "CodebaseContext", path: Path, dirpath: str):
        self.ctx = ctx
        self.path = path
        self.dirpath = dirpath
        self._files = []
        self._subdirectories = []

    def __iter__(self):
        return iter(self.items)

    def _is_a_subdirectory_of(self, target_directory: Self):
        """Checks whether this directory is a subdirectory of another directory"""
        if self.parent == target_directory:
            return True
        if self.parent is None:
            return False
        return self.parent._is_a_subdirectory_of(target_directory=target_directory)

    def __contains__(self, item: str | TFile | Self) -> bool:
        from codegen.sdk.core.file import File

        # Try to match all file and subdirectory names
        if isinstance(item, str):
            if item in self.item_names:
                return True
        # Try to match all subdirectories
        elif isinstance(item, Directory):
            if item.name in [directory.name for directory in self.subdirectories]:
                return True
        # Try to match all files
        elif isinstance(item, File):
            if item.name in [file.name for file in self.files(extensions="*")]:
                return True

        # Attempt to match recursively
        for directory in self.subdirectories(recursive=False):
            if item in directory:
                return True

        # If no match, return False
        return False

    def __len__(self) -> int:
        # Using item names here as items will cause an infinite loop
        return len(self.item_names)

    def __getitem__(self, item_name: str) -> TFile | Self:
        return next((item for item in self.items if item.name == item_name), None)

    def __repr__(self) -> str:
        return f"Directory(name='{self.name}', items={self.item_names})"

    @property
    def name(self) -> str:
        """Get the base name of the directory's path.

        Extracts the final component of the directory path. For example, for a path '/home/user/project', returns 'project'.

        Returns:
            str: The directory's base name.
        """
        return os.path.basename(self.dirpath)

    @proxy_property
    def files(self, *, extensions: list[str] | Literal["*"] | None = None, recursive: bool = False) -> list[TFile]:
        """Gets a list of all top level files in the directory.

        Set `recursive=True` to get all files recursively.

        By default, this only returns source files. Setting `extensions='*'` will return all files, and
        `extensions=[...]` will return all files with the specified extensions.

        For Python and Typescript repos WITH file parsing enabled,
        `extensions='*'` is REQUIRED for listing all non source code files.
        Or else, codebase.files will ONLY return source files (e.g. .py, .ts).

        For repos with file parsing disabled or repos with other languages, this will return all files in the codebase.

        Returns all Files in the codebase, sorted alphabetically. For Python codebases, returns PyFiles (python files).
        For Typescript codebases, returns TSFiles (typescript files).

        Returns:
            list[TSourceFile]: A sorted list of source files in the codebase.
        """
        # If there are no source files, return ALL files
        if len(self.ctx.get_nodes(NodeType.FILE)) == 0:
            extensions = "*"
        # If extensions is not set, use the extensions from the codebase
        elif extensions is None:
            extensions = self.ctx.extensions

        files = []
        for file_name in self._files:
            if extensions == "*":
                files.append(self.get_file(file_name))
            elif extensions is not None:
                if any(file_name.endswith(ext) for ext in extensions):
                    files.append(self.get_file(file_name))

        if recursive:
            for directory in self.subdirectories:
                files.extend(directory.files(extensions=extensions, recursive=True))

        return sort_editables(files, alphabetical=True, dedupe=False)

    @proxy_property
    def subdirectories(self, recursive: bool = False) -> list[Self]:
        """Get a list of all top level subdirectories in the directory.

        Set `recursive=True` to get all subdirectories recursively.

        Returns:
            list[Directory]: A sorted list of subdirectories in the directory.
        """
        subdirectories = []
        for directory_name in self._subdirectories:
            subdirectories.append(self.get_subdirectory(directory_name))

        if recursive:
            for directory in self.subdirectories:
                subdirectories.extend(directory.subdirectories(recursive=True))

        return sorted(subdirectories, key=lambda x: x.name)

    @proxy_property
    def items(self, recursive: bool = False) -> list[Self | TFile]:
        """Get a list of all files and subdirectories in the directory.

        Set `recursive=True` to get all files and subdirectories recursively.

        Returns:
            list[Self | TFile]: A sorted list of files and subdirectories in the directory.
        """
        return self.files(extensions="*", recursive=recursive) + self.subdirectories(recursive=recursive)

    @property
    def item_names(self, recursive: bool = False) -> list[str]:
        """Get a list of all file and subdirectory names in the directory.

        Set `recursive=True` to get all file and subdirectory names recursively.

        Returns:
            list[str]: A list of file and subdirectory names in the directory.
        """
        return self._files + self._subdirectories

    @property
    def file_names(self) -> list[str]:
        """Get a list of all file names in the directory."""
        return self._files

    @property
    def tree(self) -> list[Self | TFile]:
        """Get a recursive list of all files and subdirectories in the directory.

        Returns:
            list[Self | TFile]: A recursive list of files and subdirectories in the directory.
        """
        return self.items(recursive=True)

    @property
    def parent(self) -> Self | None:
        """Get the parent directory of the current directory."""
        return self.ctx.get_directory(self.path.parent)

    @noapidoc
    @cached_generator()
    def files_generator(self, *args: FilesParam.args, **kwargs: FilesParam.kwargs) -> Iterator[TFile]:
        """Yield files recursively from the directory."""
        yield from self.files(*args, extensions="*", **kwargs, recursive=True)

    def get_file(self, filename: str, ignore_case: bool = False) -> TFile | None:
        """Get a file by its name relative to the directory."""
        file_path = os.path.join(self.dirpath, filename)
        absolute_path = self.ctx.to_absolute(file_path)
        # Try to get the file from the graph first
        file = self.ctx.get_file(file_path, ignore_case=ignore_case)
        if file is not None:
            return file
        # If the file is not in the graph, check the filesystem
        for file in absolute_path.parent.iterdir():
            if ignore_case and str(absolute_path).lower() == str(file).lower():
                return self.ctx._get_raw_file_from_path(file)
            elif not ignore_case and str(absolute_path) == str(file):
                return self.ctx._get_raw_file_from_path(file)
        return None

    def get_subdirectory(self, subdirectory_name: str) -> Self | None:
        """Get a subdirectory by its name (relative to the directory)."""
        return self.ctx.get_directory(os.path.join(self.dirpath, subdirectory_name))

    def update_filepath(self, new_filepath: str) -> None:
        """Update the filepath of the directory and its contained files."""
        old_path = self.dirpath
        new_path = new_filepath
        for file in self.files(recursive=True):
            new_file_path = os.path.join(new_path, os.path.relpath(file.file_path, old_path))
            file.update_filepath(new_file_path)

    def remove(self) -> None:
        """Remove all the files in the files container."""
        for f in self.files(recursive=True):
            f.remove()

    def rename(self, new_name: str) -> None:
        """Rename the directory."""
        parent_dir, _ = os.path.split(self.dirpath)
        new_path = os.path.join(parent_dir, new_name)
        self.update_filepath(new_path)

    def _add_file(self, file_name: str) -> None:
        """Add a file to the directory."""
        self._files.append(file_name)

    def _add_subdirectory(self, subdirectory_name: str) -> None:
        """Add a subdirectory to the directory."""
        self._subdirectories.append(subdirectory_name)
