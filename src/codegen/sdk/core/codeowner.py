from collections.abc import Iterable, Iterator
from typing import Callable, Generic, Literal

from codeowners import CodeOwners as CodeOwnersParser

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
from codegen.shared.decorators.docs import apidoc, noapidoc
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


@apidoc
class CodeOwner(
    HasSymbols[TFile, TSymbol, TImportStatement, TGlobalVar, TClass, TFunction, TImport],
    Generic[TFile, TSymbol, TImportStatement, TGlobalVar, TClass, TFunction, TImport],
):
    """CodeOwner is a class that represents a code owner in a codebase.

    It is used to iterate over all files that are owned by a specific owner.

    Attributes:
        owner_type: The type of the owner (USERNAME, TEAM, EMAIL).
        owner_value: The value of the owner.
        files_source: A callable that returns an iterable of all files in the codebase.
    """

    _instance_iterator: Iterator[TFile]
    owner_type: Literal["USERNAME", "TEAM", "EMAIL"]
    owner_value: str
    files_source: Callable[FilesParam, Iterable[TFile]]

    def __init__(
        self,
        files_source: Callable[FilesParam, Iterable[TFile]],
        owner_type: Literal["USERNAME", "TEAM", "EMAIL"],
        owner_value: str,
    ):
        self.owner_type = owner_type
        self.owner_value = owner_value
        self.files_source = files_source

    @classmethod
    def from_parser(
        cls,
        parser: CodeOwnersParser,
        file_source: Callable[FilesParam, Iterable[TFile]],
    ) -> list["CodeOwner"]:
        """Create a list of CodeOwner objects from a CodeOwnersParser.

        Args:
            parser (CodeOwnersParser): The CodeOwnersParser to use.
            file_source (Callable[FilesParam, Iterable[TFile]]): A callable that returns an iterable of all files in the codebase.

        Returns:
            list[CodeOwner]: A list of CodeOwner objects.
        """
        codeowners = []
        for _, _, owners, _, _ in parser.paths:
            for owner_label, owner_value in owners:
                codeowners.append(CodeOwner(file_source, owner_label, owner_value))
        return codeowners

    @cached_generator(maxsize=16)
    @noapidoc
    def files_generator(self, *args: FilesParam.args, **kwargs: FilesParam.kwargs) -> Iterable[TFile]:
        for source_file in self.files_source(*args, **kwargs):
            # Filter files by owner value
            if self.owner_value in source_file.owners:
                yield source_file

    @proxy_property
    def files(self, *args: FilesParam.args, **kwargs: FilesParam.kwargs) -> Iterable[TFile]:
        """Recursively iterate over all files in the codebase that are owned by the current code owner."""
        return self.files_generator(*args, **kwargs)

    @property
    def name(self) -> str:
        """The name of the code owner."""
        return self.owner_value

    def __iter__(self) -> Iterator[TFile]:
        self._instance_iterator = iter(self.files_generator())
        return self

    def __next__(self) -> str:
        return next(self._instance_iterator)

    def __repr__(self) -> str:
        return f"CodeOwner(owner_type={self.owner_type}, owner_value={self.owner_value})"
