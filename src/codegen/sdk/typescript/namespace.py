from __future__ import annotations

from typing import TYPE_CHECKING, override

from codegen.sdk.core.autocommit import commiter
from codegen.sdk.core.autocommit.decorators import writer
from codegen.sdk.core.export import Export
from codegen.sdk.core.interfaces.has_attribute import HasAttribute
from codegen.sdk.core.interfaces.has_name import HasName
from codegen.sdk.enums import SymbolType
from codegen.sdk.extensions.autocommit import reader
from codegen.sdk.extensions.sort import sort_editables
from codegen.sdk.extensions.utils import cached_property
from codegen.sdk.typescript.class_definition import TSClass
from codegen.sdk.typescript.enum_definition import TSEnum
from codegen.sdk.typescript.function import TSFunction
from codegen.sdk.typescript.interface import TSInterface
from codegen.sdk.typescript.interfaces.has_block import TSHasBlock
from codegen.sdk.typescript.symbol import TSSymbol
from codegen.sdk.typescript.type_alias import TSTypeAlias
from codegen.shared.decorators.docs import noapidoc, ts_apidoc
from codegen.shared.logging.get_logger import get_logger

if TYPE_CHECKING:
    from collections.abc import Sequence

    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.dataclasses.usage import UsageKind
    from codegen.sdk.core.interfaces.importable import Importable
    from codegen.sdk.core.node_id_factory import NodeId
    from codegen.sdk.core.statements.statement import Statement
    from codegen.sdk.core.symbol import Symbol
    from codegen.sdk.typescript.detached_symbols.code_block import TSCodeBlock
    from codegen.sdk.typescript.export import TSExport
    from codegen.sdk.typescript.import_resolution import TSImport


logger = get_logger(__name__)


@ts_apidoc
class TSNamespace(TSSymbol, TSHasBlock, HasName, HasAttribute):
    """Representation of a namespace module in TypeScript.

    Attributes:
        symbol_type: The type of the symbol, set to SymbolType.Namespace.
        code_block: The code block associated with this namespace.
    """

    symbol_type = SymbolType.Namespace
    code_block: TSCodeBlock

    def __init__(self, ts_node: TSNode, file_id: NodeId, ctx: CodebaseContext, parent: Statement, namespace_node: TSNode | None = None) -> None:
        ts_node = namespace_node or ts_node
        name_node = ts_node.child_by_field_name("name")
        super().__init__(ts_node, file_id, ctx, parent, name_node=name_node)

    @noapidoc
    @commiter
    def _compute_dependencies(self, usage_type: UsageKind | None = None, dest: HasName | None = None) -> None:
        """Computes dependencies for the namespace by analyzing its code block.

        Args:
            usage_type: Optional UsageKind specifying how the dependencies are used
            dest: Optional HasName destination for the dependencies
        """
        # Use self as destination if none provided
        dest = dest or self.self_dest
        # Compute dependencies from namespace's code block
        self.code_block._compute_dependencies(usage_type, dest)

    @cached_property
    def symbols(self) -> list[Symbol]:
        """Returns all symbols defined within this namespace, including nested ones."""
        all_symbols = []
        for stmt in self.code_block.statements:
            if stmt.ts_node_type == "export_statement":
                for export in stmt.exports:
                    all_symbols.append(export.declared_symbol)
            elif hasattr(stmt, "assignments"):
                all_symbols.extend(stmt.assignments)
            else:
                all_symbols.append(stmt)
        return all_symbols

    def get_symbol(self, name: str, recursive: bool = True, get_private: bool = False) -> Symbol | None:
        """Get an exported or private symbol by name from this namespace. Returns only exported symbols by default.

        Args:
            name: Name of the symbol to find
            recursive: If True, also search in nested namespaces
            get_private: If True, also search in private symbols

        Returns:
            Symbol | None: The found symbol, or None if not found
        """
        # First check direct symbols in this namespace
        for symbol in self.symbols:
            # Handle TSAssignmentStatement case
            if hasattr(symbol, "assignments"):
                for assignment in symbol.assignments:
                    if assignment.name == name:
                        # If we are looking for private symbols then return it, else only return exported symbols
                        if get_private:
                            return assignment
                        elif assignment.is_exported:
                            return assignment

            # Handle regular symbol case
            if hasattr(symbol, "name") and symbol.name == name:
                if get_private:
                    return symbol
                elif symbol.is_exported:
                    return symbol

            # If recursive and this is a namespace, check its symbols
            if recursive and isinstance(symbol, TSNamespace):
                nested_symbol = symbol.get_symbol(name, recursive=True, get_private=get_private)
                return nested_symbol

        return None

    @reader(cache=False)
    @noapidoc
    def get_nodes(self, *, sort_by_id: bool = False, sort: bool = True) -> Sequence[Importable]:
        """Returns all nodes in the namespace, sorted by position in the namespace."""
        file_nodes = self.file.get_nodes(sort_by_id=sort_by_id, sort=sort)
        start_limit = self.start_byte
        end_limit = self.end_byte
        namespace_nodes = []
        for file_node in file_nodes:
            if file_node.start_byte > start_limit:
                if file_node.end_byte < end_limit:
                    namespace_nodes.append(file_node)
                else:
                    break
        return namespace_nodes

    @cached_property
    @reader(cache=False)
    def exports(self) -> list[TSExport]:
        """Returns all Export symbols in the namespace.

        Retrieves a list of all top-level export declarations in the current TypeScript namespace.

        Returns:
            list[TSExport]: A list of TSExport objects representing all top-level export declarations in the namespace.
        """
        # Filter to only get exports that are direct children of the namespace's code block
        return sort_editables(filter(lambda node: isinstance(node, Export), self.get_nodes(sort=False)), by_id=True)

    @cached_property
    def functions(self) -> list[TSFunction]:
        """Get all functions defined in this namespace.

        Returns:
            List of Function objects in this namespace
        """
        return [symbol for symbol in self.symbols if isinstance(symbol, TSFunction)]

    def get_function(self, name: str, recursive: bool = True) -> TSFunction | None:
        """Get a function by name from this namespace.

        Args:
            name: Name of the function to find
            recursive: If True, also search in nested namespaces
        """
        symbol = self.get_symbol(name, recursive=recursive)
        return symbol if isinstance(symbol, TSFunction) else None

    @cached_property
    def classes(self) -> list[TSClass]:
        """Get all classes defined in this namespace.

        Returns:
            List of Class objects in this namespace
        """
        return [symbol for symbol in self.symbols if isinstance(symbol, TSClass)]

    def get_class(self, name: str, recursive: bool = True) -> TSClass | None:
        """Get a class by name from this namespace.

        Args:
            name: Name of the class to find
            recursive: If True, also search in nested namespaces
        """
        symbol = self.get_symbol(name, recursive=recursive)
        return symbol if isinstance(symbol, TSClass) else None

    def get_interface(self, name: str, recursive: bool = True) -> TSInterface | None:
        """Get an interface by name from this namespace.

        Args:
            name: Name of the interface to find
            recursive: If True, also search in nested namespaces
        """
        symbol = self.get_symbol(name, recursive=recursive)
        return symbol if isinstance(symbol, TSInterface) else None

    def get_type(self, name: str, recursive: bool = True) -> TSTypeAlias | None:
        """Get a type alias by name from this namespace.

        Args:
            name: Name of the type to find
            recursive: If True, also search in nested namespaces
        """
        symbol = self.get_symbol(name, recursive=recursive)
        return symbol if isinstance(symbol, TSTypeAlias) else None

    def get_enum(self, name: str, recursive: bool = True) -> TSEnum | None:
        """Get an enum by name from this namespace.

        Args:
            name: Name of the enum to find
            recursive: If True, also search in nested namespaces
        """
        symbol = self.get_symbol(name, recursive=recursive)
        return symbol if isinstance(symbol, TSEnum) else None

    def get_namespace(self, name: str, recursive: bool = True) -> TSNamespace | None:
        """Get a namespace by name from this namespace.

        Args:
            name: Name of the namespace to find
            recursive: If True, also search in nested namespaces

        Returns:
            TSNamespace | None: The found namespace, or None if not found
        """
        # First check direct symbols in this namespace
        for symbol in self.symbols:
            if isinstance(symbol, TSNamespace) and symbol.name == name:
                return symbol

            # If recursive and this is a namespace, check its symbols
            if recursive and isinstance(symbol, TSNamespace):
                nested_namespace = symbol.get_namespace(name, recursive=True)
                return nested_namespace

        return None

    def get_nested_namespaces(self) -> list[TSNamespace]:
        """Get all nested namespaces within this namespace.

        Returns:
            list[TSNamespace]: List of all nested namespace objects
        """
        nested = []
        for symbol in self.symbols:
            if isinstance(symbol, TSNamespace):
                nested.append(symbol)
                nested.extend(symbol.get_nested_namespaces())
        return nested

    @writer
    def add_symbol_from_source(self, source: str) -> None:
        """Adds a symbol to a namespace from a string representation.

        This method adds a new symbol definition to the namespace by appending its source code string. The symbol will be added
        after existing symbols if present, otherwise at the beginning of the namespace.

        Args:
            source (str): String representation of the symbol to be added. This should be valid source code for
                the file's programming language.

        Returns:
            None: The symbol is added directly to the namespace's content.
        """
        symbols = self.symbols
        if len(symbols) > 0:
            symbols[-1].insert_after("\n" + source, fix_indentation=True)
        else:
            self.insert_after("\n" + source)

    @commiter
    def add_symbol(self, symbol: TSSymbol, should_export: bool = True) -> TSSymbol | None:
        """Adds a new symbol to the namespace, optionally exporting it if applicable. If the symbol already exists in the namespace, returns the existing symbol.

        Args:
            symbol: The symbol to add to the namespace (either a TSSymbol instance or source code string)
            export: Whether to export the symbol. Defaults to True.

        Returns:
            TSSymbol | None: The existing symbol if it already exists in the file or None if it was added.
        """
        existing_symbol = self.get_symbol(symbol.name)
        if existing_symbol is not None:
            return existing_symbol

        if not self.file.symbol_can_be_added(symbol):
            msg = f"Symbol {symbol.name} cannot be added to this file type."
            raise ValueError(msg)

        source = symbol.source
        if isinstance(symbol, TSFunction) and symbol.is_arrow:
            raw_source = symbol._named_arrow_function.text.decode("utf-8")
        else:
            raw_source = symbol.ts_node.text.decode("utf-8")
        if should_export and hasattr(symbol, "export") and (not symbol.is_exported or raw_source not in symbol.export.source):
            source = source.replace(source, f"export {source}")
        self.add_symbol_from_source(source)

    @commiter
    def remove_symbol(self, symbol_name: str) -> TSSymbol | None:
        """Removes a symbol from the namespace by name.

        Args:
            symbol_name: Name of the symbol to remove

        Returns:
            The removed symbol if found, None otherwise
        """
        symbol = self.get_symbol(symbol_name)
        if symbol:
            # Remove from code block statements
            for i, stmt in enumerate(self.code_block.statements):
                if symbol.source == stmt.source:
                    logger.debug(f"stmt to be removed: {stmt}")
                    self.code_block.statements.pop(i)
                    return symbol
        return None

    @commiter
    def rename_symbol(self, old_name: str, new_name: str) -> None:
        """Renames a symbol within the namespace.

        Args:
            old_name: Current symbol name
            new_name: New symbol name
        """
        symbol = self.get_symbol(old_name)
        if symbol:
            symbol.rename(new_name)

    @commiter
    @noapidoc
    def export_symbol(self, name: str) -> None:
        """Marks a symbol as exported in the namespace.

        Args:
            name: Name of symbol to export
        """
        symbol = self.get_symbol(name, get_private=True)
        if not symbol or symbol.is_exported:
            return

        export_source = f"export {symbol.source}"
        symbol.parent.edit(export_source)

    @cached_property
    @noapidoc
    @reader(cache=True)
    def valid_import_names(self) -> dict[str, TSSymbol | TSImport]:
        """Returns set of valid import names for this namespace.

        This includes all exported symbols plus the namespace name itself
        for namespace imports.
        """
        valid_export_names = {}
        valid_export_names[self.name] = self
        for export in self.exports:
            for name, dest in export.names:
                valid_export_names[name] = dest
        return valid_export_names

    def resolve_import(self, import_name: str) -> Symbol | None:
        """Resolves an import name to a symbol within this namespace.

        Args:
            import_name: Name to resolve

        Returns:
            Resolved symbol or None if not found
        """
        # First check direct symbols
        for symbol in self.symbols:
            if symbol.is_exported and symbol.name == import_name:
                return symbol

        # Then check nested namespaces
        for nested in self.get_nested_namespaces():
            resolved = nested.resolve_import(import_name)
            if resolved is not None:
                return resolved

        return None

    @override
    def resolve_attribute(self, name: str) -> Symbol | None:
        """Resolves an attribute access on the namespace.

        Args:
            name: Name of the attribute to resolve

        Returns:
            The resolved symbol or None if not found
        """
        return self.valid_import_names.get(name, None)
