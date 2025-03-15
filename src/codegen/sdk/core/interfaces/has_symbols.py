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

    def get_symbol(self, name: str, optional: bool = False) -> TSymbol | None:
        """Get a symbol by name in files container."""
        symbol = next((s for s in self.symbols if s.name == name), None)
        if not symbol:
            if not optional:
                msg = f"Symbol {name} not found in files container. Use optional=True to return None instead."
                raise ValueError(msg)
            return None
        if len(symbol) > 1:
            msg = f"Multiple symbols with name {name} found in files container. Use get_symbol_by_type to resolve."
            raise ValueError(msg)
        return symbol

    def get_import_statement(self, name: str, optional: bool = False) -> TImportStatement | None:
        """Get an import statement by name in files container."""
        import_statement = next((s for s in self.import_statements if s.name == name), None)
        if not import_statement:
            if not optional:
                msg = f"Import statement {name} not found in files container. Use optional=True to return None instead."
                raise ValueError(msg)
            return None
        if len(import_statement) > 1:
            msg = f"Multiple import statements with name {name} found in files container. Use get_import_statement_by_type to resolve."
            raise ValueError(msg)
        return import_statement

    def get_global_var(self, name: str, optional: bool = False) -> TGlobalVar | None:
        """Get a global variable by name in files container."""
        global_var = next((s for s in self.global_vars if s.name == name), None)
        if not global_var:
            if not optional:
                msg = f"Global variable {name} not found in files container. Use optional=True to return None instead."
                raise ValueError(msg)
            return None
        if len(global_var) > 1:
            msg = f"Multiple global variables with name {name} found in files container. Use get_global_var_by_type to resolve."
            raise ValueError(msg)
        return global_var

    def get_class(self, name: str, optional: bool = False) -> TClass | None:
        """Get a class by name in files container."""
        class_ = next((s for s in self.classes if s.name == name), None)
        if not class_:
            if not optional:
                msg = f"Class {name} not found in files container. Use optional=True to return None instead."
                raise ValueError(msg)
            return None
        if len(class_) > 1:
            msg = f"Multiple classes with name {name} found in files container. Use get_class_by_type to resolve."
            raise ValueError(msg)
        return class_

    def get_function(self, name: str, optional: bool = False) -> TFunction | None:
        """Get a function by name in files container."""
        function = next((s for s in self.functions if s.name == name), None)
        if not function:
            if not optional:
                msg = f"Function {name} not found in files container. Use optional=True to return None instead."
                raise ValueError(msg)
            return None
        if len(function) > 1:
            msg = f"Multiple functions with name {name} found in files container. Use get_function_by_type to resolve."
            raise ValueError(msg)
        return function

    @py_noapidoc
    def get_export(
        self: "HasSymbols[TSFile, TSSymbol, TSImportStatement, TSGlobalVar, TSClass, TSFunction, TSImport]",
        name: str,
        optional: bool = False,
    ) -> "TSExport | None":
        """Get an export by name in files container (supports only typescript)."""
        export = next((s for s in self.exports if s.name == name), None)
        if not export:
            if not optional:
                msg = f"Export {name} not found in files container. Use optional=True to return None instead."
                raise ValueError(msg)
            return None
        if len(export) > 1:
            msg = f"Multiple exports with name {name} found in files container. Use get_export_by_type to resolve."
            raise ValueError(msg)
        return export

    def get_import(self, name: str, optional: bool = False) -> TImport | None:
        """Get an import by name in files container."""
        import_ = next((s for s in self.imports if s.name == name), None)
        if not import_:
            if not optional:
                msg = f"Import {name} not found in files container. Use optional=True to return None instead."
                raise ValueError(msg)
            return None
        if len(import_) > 1:
            msg = f"Multiple imports with name {name} found in files container. Use get_import_by_type to resolve."
            raise ValueError(msg)
        return import_
