from collections.abc import Iterator
from itertools import chain
from typing import TYPE_CHECKING, Generic, ParamSpec, TypeVar

from codegen.sdk.core.utils.cache_utils import cached_generator
from codegen.shared.decorators.docs import py_noapidoc
from codegen.shared.logging.get_logger import get_logger

if TYPE_CHECKING:
    from codegen.sdk.core.assignment import Assignment
    from codegen.sdk.core.class_definition import Class
    from codegen.sdk.core.file import SourceFile
    from codegen.sdk.core.function import Function
    from codegen.sdk.core.import_resolution import Import, ImportStatement
    from codegen.sdk.core.symbol import Symbol
    from codegen.sdk.typescript.class_definition import TSClass
    from codegen.sdk.typescript.export import TSExport
    from codegen.sdk.typescript.file import TSFile
    from codegen.sdk.typescript.function import TSFunction
    from codegen.sdk.typescript.import_resolution import TSImport
    from codegen.sdk.typescript.statements.import_statement import TSImportStatement
    from codegen.sdk.typescript.symbol import TSSymbol

logger = get_logger(__name__)


TFile = TypeVar("TFile", bound="SourceFile")
TSymbol = TypeVar("TSymbol", bound="Symbol")
TImportStatement = TypeVar("TImportStatement", bound="ImportStatement")
TGlobalVar = TypeVar("TGlobalVar", bound="Assignment")
TClass = TypeVar("TClass", bound="Class")
TFunction = TypeVar("TFunction", bound="Function")
TImport = TypeVar("TImport", bound="Import")
FilesParam = ParamSpec("FilesParam")

TSGlobalVar = TypeVar("TSGlobalVar", bound="Assignment")


class HasSymbols(Generic[TFile, TSymbol, TImportStatement, TGlobalVar, TClass, TFunction, TImport]):
    """Abstract interface for files in a codebase.

    Abstract interface for files in a codebase.
    """

    @cached_generator()
    def files_generator(self, *args: FilesParam.args, **kwargs: FilesParam.kwargs) -> Iterator[TFile]:
        """Generator for yielding files of the current container's scope."""
        msg = "This method should be implemented by the subclass"
        raise NotImplementedError(msg)

    @property
    def symbols(self) -> list[TSymbol]:
        """Get a recursive list of all symbols in files container."""
        return list(chain.from_iterable(f.symbols for f in self.files_generator()))

    @property
    def import_statements(self) -> list[TImportStatement]:
        """Get a recursive list of all import statements in files container."""
        return list(chain.from_iterable(f.import_statements for f in self.files_generator()))

    @property
    def global_vars(self) -> list[TGlobalVar]:
        """Get a recursive list of all global variables in files container."""
        return list(chain.from_iterable(f.global_vars for f in self.files_generator()))

    @property
    def classes(self) -> list[TClass]:
        """Get a recursive list of all classes in files container."""
        return list(chain.from_iterable(f.classes for f in self.files_generator()))

    @property
    def functions(self) -> list[TFunction]:
        """Get a recursive list of all functions in files container."""
        return list(chain.from_iterable(f.functions for f in self.files_generator()))

    @property
    @py_noapidoc
    def exports(self) -> "list[TSExport]":
        """Get a recursive list of all exports in files container."""
        return list(chain.from_iterable(f.exports for f in self.files_generator()))

    @property
    def imports(self) -> list[TImport]:
        """Get a recursive list of all imports in files container."""
        return list(chain.from_iterable(f.imports for f in self.files_generator()))

    def get_symbol(self, name: str) -> TSymbol | None:
        """Get a symbol by name in files container."""
        return next((s for s in self.symbols if s.name == name), None)

    def get_import_statement(self, name: str) -> TImportStatement | None:
        """Get an import statement by name in files container."""
        return next((s for s in self.import_statements if s.name == name), None)

    def get_global_var(self, name: str) -> TGlobalVar | None:
        """Get a global variable by name in files container."""
        return next((s for s in self.global_vars if s.name == name), None)

    def get_class(self, name: str) -> TClass | None:
        """Get a class by name in files container."""
        return next((s for s in self.classes if s.name == name), None)

    def get_function(self, name: str) -> TFunction | None:
        """Get a function by name in files container."""
        return next((s for s in self.functions if s.name == name), None)

    @py_noapidoc
    def get_export(
        self: "HasSymbols[TSFile, TSSymbol, TSImportStatement, TSGlobalVar, TSClass, TSFunction, TSImport]",
        name: str,
    ) -> "TSExport | None":
        """Get an export by name in files container (supports only typescript)."""
        return next((s for s in self.exports if s.name == name), None)

    def get_import(self, name: str) -> TImport | None:
        """Get an import by name in files container."""
        return next((s for s in self.imports if s.name == name), None)
