from __future__ import annotations

from typing import TYPE_CHECKING

from codegen.sdk.core.autocommit import commiter
from codegen.sdk.core.interfaces.has_name import HasName
from codegen.sdk.core.statements.symbol_statement import SymbolStatement
from codegen.sdk.enums import SymbolType
from codegen.sdk.extensions.utils import cached_property
from codegen.sdk.typescript.class_definition import TSClass
from codegen.sdk.typescript.enum_definition import TSEnum
from codegen.sdk.typescript.function import TSFunction
from codegen.sdk.typescript.interface import TSInterface
from codegen.sdk.typescript.interfaces.has_block import TSHasBlock
from codegen.sdk.typescript.symbol import TSSymbol
from codegen.sdk.typescript.type_alias import TSTypeAlias
from codegen.shared.decorators.docs import noapidoc, ts_apidoc

if TYPE_CHECKING:
    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.dataclasses.usage import UsageKind
    from codegen.sdk.core.node_id_factory import NodeId
    from codegen.sdk.core.statements.statement import Statement
    from codegen.sdk.core.symbol import Symbol
    from codegen.sdk.typescript.detached_symbols.code_block import TSCodeBlock


@ts_apidoc
class TSNamespace(TSSymbol, TSHasBlock, HasName):
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

        # Compute dependencies from the namespace's code block
        self.code_block._compute_dependencies(usage_type, dest)

    @cached_property
    def symbols(self) -> list[Symbol]:
        """Returns all symbols defined within this namespace, including nested ones."""
        all_symbols = []
        for stmt in self.code_block.statements:
            # Handle export statements
            if stmt.ts_node_type == "export_statement":
                for export in stmt.exports:
                    all_symbols.append(export.declared_symbol)
            # Handle direct symbols
            elif isinstance(stmt, SymbolStatement):
                all_symbols.append(stmt)
        return all_symbols

    def get_symbol(self, name: str, recursive: bool = True, optional: bool = False) -> Symbol | None:
        """Get a symbol by name from this namespace.

        Args:
            name: Name of the symbol to find
            recursive: If True, also search in nested namespaces
            optional: If True, return None if the symbol is not found

        Returns:
            Symbol | None: The found symbol, or None if not found
        """
        # First check direct symbols in this namespace
        for symbol in self.symbols:
            if hasattr(symbol, "name") and symbol.name == name:
                return symbol

            # If recursive and this is a namespace, check its symbols
            if recursive and isinstance(symbol, TSNamespace):
                nested_symbol = symbol.get_symbol(name, recursive=True)
                return nested_symbol

        if not optional:
            msg = f"Symbol {name} not found in namespace {self.name} of file {self.file_path}. Use optional=True to return None instead."
            raise ValueError(msg)

        return None

    @cached_property
    def functions(self) -> list[TSFunction]:
        """Get all functions defined in this namespace.

        Returns:
            List of Function objects in this namespace
        """
        return [symbol for symbol in self.symbols if isinstance(symbol, TSFunction)]

    def get_function(self, name: str, recursive: bool = True, use_full_name: bool = False, optional: bool = False) -> TSFunction | None:
        """Get a function by name from this namespace.

        Args:
            name: Name of the function to find (can be fully qualified like 'Outer.Inner.func')
            recursive: If True, also search in nested namespaces
            use_full_name: If True, match against the full qualified name
            optional: If True, return None if the function is not found

        Returns:
            TSFunction | None: The found function, or None if not found
        """
        if use_full_name and "." in name:
            namespace_path, func_name = name.rsplit(".", 1)
            target_ns = self.get_namespace(namespace_path)
            return target_ns.get_function(func_name, recursive=False) if target_ns else None

        if (symbol := self.get_symbol(name, recursive=recursive)) and isinstance(symbol, TSFunction):
            return symbol

        if not optional:
            msg = f"Function {name} not found in namespace {self.name} of file {self.file_path}. Use optional=True to return None instead."
            raise ValueError(msg)
        return None

    @cached_property
    def classes(self) -> list[TSClass]:
        """Get all classes defined in this namespace.

        Returns:
            List of Class objects in this namespace
        """
        return [symbol for symbol in self.symbols if isinstance(symbol, TSClass)]

    def get_class(self, name: str, recursive: bool = True, optional: bool = False) -> TSClass | None:
        """Get a class by name from this namespace.

        Args:
            name: Name of the class to find
            recursive: If True, also search in nested namespaces
            optional: If True, return None if the class is not found

        Returns:
            TSClass | None: The found class, or None if not found
        """
        if (symbol := self.get_symbol(name, recursive=recursive)) and isinstance(symbol, TSClass):
            return symbol
        if not optional:
            msg = f"Class {name} not found in namespace {self.name} of file {self.file_path}. Use optional=True to return None instead."
            raise ValueError(msg)
        return None

    def get_interface(self, name: str, recursive: bool = True, optional: bool = False) -> TSInterface | None:
        """Get an interface by name from this namespace.

        Args:
            name: Name of the interface to find
            recursive: If True, also search in nested namespaces
            optional: If True, return None if the interface is not found

        Returns:
            TSInterface | None: The found interface, or None if not found
        """
        if (symbol := self.get_symbol(name, recursive=recursive)) and isinstance(symbol, TSInterface):
            return symbol
        if not optional:
            msg = f"Interface {name} not found in namespace {self.name} of file {self.file_path}. Use optional=True to return None instead."
            raise ValueError(msg)
        return None

    def get_type(self, name: str, recursive: bool = True, optional: bool = False) -> TSTypeAlias | None:
        """Get a type alias by name from this namespace.

        Args:
            name: Name of the type to find
            recursive: If True, also search in nested namespaces
            optional: If True, return None if the type is not found

        Returns:
            TSTypeAlias | None: The found type alias, or None if not found
        """
        if (symbol := self.get_symbol(name, recursive=recursive)) and isinstance(symbol, TSTypeAlias):
            return symbol
        if not optional:
            msg = f"Type alias {name} not found in namespace {self.name} of file {self.file_path}. Use optional=True to return None instead."
            raise ValueError(msg)
        return None

    def get_enum(self, name: str, recursive: bool = True, optional: bool = False) -> TSEnum | None:
        """Get an enum by name from this namespace.

        Args:
            name: Name of the enum to find
            recursive: If True, also search in nested namespaces
            optional: If True, return None if the enum is not found

        Returns:
            TSEnum | None: The found enum, or None if not found
        """
        if (symbol := self.get_symbol(name, recursive=recursive)) and isinstance(symbol, TSEnum):
            return symbol
        if not optional:
            msg = f"Enum {name} not found in namespace {self.name} of file {self.file_path}. Use optional=True to return None instead."
            raise ValueError(msg)
        return None

    def get_namespace(self, name: str, recursive: bool = True, optional: bool = False) -> TSNamespace | None:
        """Get a namespace by name from this namespace.

        Args:
            name: Name of the namespace to find
            recursive: If True, also search in nested namespaces
            optional: If True, return None if the namespace is not found

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

        if not optional:
            msg = f"Namespace {name} not found in namespace {self.name} of file {self.file_path}. Use optional=True to return None instead."
            raise ValueError(msg)
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
