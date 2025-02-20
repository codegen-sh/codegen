import logging
import os
from collections.abc import Iterator
from pathlib import Path
from typing import Generic, Self

from codegen.sdk.core.interfaces.has_symbols import (
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
from codegen.shared.decorators.docs import apidoc, noapidoc

logger = logging.getLogger(__name__)


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

    path: Path  # Absolute Path
    dirpath: str  # Relative Path
    parent: Self | None
    items: dict[str, TFile | Self]

    def __init__(self, path: Path, dirpath: str, parent: Self | None):
        self.path = path
        self.dirpath = dirpath
        self.parent = parent
        self.items = {}

    def __iter__(self):
        return iter(self.items.values())

    def _is_a_subdirectory_of(self, target_directory: "Directory"):
        """Checks whether this directory is a subdirectory of another directory"""
        if self.parent == target_directory:
            return True
        if self.parent is None:
            return False
        return self.parent._is_a_subdirectory_of(target_directory=target_directory)

    def __contains__(self, item: str | TFile | Self) -> bool:
        if isinstance(item, str):
            return item in self.items
        elif isinstance(item, Directory):
            return item._is_a_subdirectory_of(self)
        else:
            # It could only ever be a file here, at least according to item's types...
            match item.directory:
                case None:
                    return False
                case _ if item.directory == self:
                    return True
                case _:
                    return item.directory._is_a_subdirectory_of(self)

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, item_name: str) -> TFile | Self:
        return self.items[item_name]

    def __setitem__(self, item_name: str, item: TFile | Self) -> None:
        self.items[item_name] = item

    def __delitem__(self, item_name: str) -> None:
        del self.items[item_name]
        msg = f"Item {item_name} not found in directory {self.dirpath}"
        raise KeyError(msg)

    def __repr__(self) -> str:
        return f"Directory({self.dirpath}, {self.items.keys()})"

    @property
    def name(self) -> str:
        """Get the base name of the directory's path.

        Extracts the final component of the directory path. For example, for a path '/home/user/project', returns 'project'.

        Returns:
            str: The directory's base name.
        """
        return os.path.basename(self.dirpath)

    @property
    def files(self) -> list[TFile]:
        """Get a recursive list of all files in the directory and its subdirectories."""
        files = []

        def _get_files(directory: Directory):
            for item in directory.items.values():
                if isinstance(item, Directory):
                    _get_files(item)
                else:
                    files.append(item)

        _get_files(self)
        return files

    @property
    def subdirectories(self) -> list[Self]:
        """Get a recursive list of all subdirectories in the directory and its subdirectories."""
        subdirectories = []

        def _get_subdirectories(directory: Directory):
            for item in directory.items.values():
                if isinstance(item, Directory):
                    subdirectories.append(item)
                    _get_subdirectories(item)

        _get_subdirectories(self)
        return subdirectories

    @noapidoc
    @cached_generator()
    def files_generator(self) -> Iterator[TFile]:
        """Yield files recursively from the directory."""
        yield from self.files

    # Directory-specific methods
    def add_file(self, file: TFile) -> None:
        """Add a file to the directory."""
        rel_path = os.path.relpath(file.file_path, self.dirpath)
        self.items[rel_path] = file

    def remove_file(self, file: TFile) -> None:
        """Remove a file from the directory."""
        rel_path = os.path.relpath(file.file_path, self.dirpath)
        del self.items[rel_path]

    def remove_file_by_path(self, file_path: os.PathLike) -> None:
        """Remove a file from the directory by its path."""
        rel_path = str(Path(file_path).relative_to(self.dirpath))
        del self.items[rel_path]

    def get_file(self, filename: str, ignore_case: bool = False) -> TFile | None:
        """Get a file by its name relative to the directory."""
        from codegen.sdk.core.file import File

        if ignore_case:
            return next(
                (f for name, f in self.items.items() if name.lower() == filename.lower() and isinstance(f, File)),
                None,
            )
        return self.items.get(filename, None)

    def add_subdirectory(self, subdirectory: Self) -> None:
        """Add a subdirectory to the directory."""
        rel_path = os.path.relpath(subdirectory.dirpath, self.dirpath)
        self.items[rel_path] = subdirectory

    def remove_subdirectory(self, subdirectory: Self) -> None:
        """Remove a subdirectory from the directory."""
        rel_path = os.path.relpath(subdirectory.dirpath, self.dirpath)
        del self.items[rel_path]

    def remove_subdirectory_by_path(self, subdirectory_path: str) -> None:
        """Remove a subdirectory from the directory by its path."""
        rel_path = os.path.relpath(subdirectory_path, self.dirpath)
        del self.items[rel_path]

    def get_subdirectory(self, subdirectory_name: str) -> Self | None:
        """Get a subdirectory by its name (relative to the directory)."""
        return self.items.get(subdirectory_name, None)

    def update_filepath(self, new_filepath: str) -> None:
        """Update the filepath of the directory and its contained files."""
        old_path = self.dirpath
        new_path = new_filepath
        for file in self.files:
            new_file_path = os.path.join(new_path, os.path.relpath(file.file_path, old_path))
            file.update_filepath(new_file_path)

    def remove(self) -> None:
        """Remove all the files in the files container."""
        for f in self.files:
            f.remove()

    def rename(self, new_name: str) -> None:
        """Rename the directory."""
        parent_dir, _ = os.path.split(self.dirpath)
        new_path = os.path.join(parent_dir, new_name)
        self.update_filepath(new_path)
