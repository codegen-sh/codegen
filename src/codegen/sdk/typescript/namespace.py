from __future__ import annotations

from typing import TYPE_CHECKING

from codegen.sdk.core.autocommit import commiter
from codegen.sdk.core.dataclasses.usage import Usage, UsageType
from codegen.sdk.core.interfaces.has_name import HasName
from codegen.sdk.enums import EdgeType, SymbolType
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

        if dest and dest != self:
            # Add direct usage of namespace itself
            usage = Usage(kind=usage_type, match=self, usage_type=UsageType.DIRECT, usage_symbol=dest.parent_symbol, imported_by=None)
            self.G.add_edge(self.node_id, dest.node_id, EdgeType.SYMBOL_USAGE, usage)

            # For each exported symbol accessed through namespace
            for symbol in self.symbols:
                if symbol and symbol.ts_node_type == "export_statement":
                    # Add chained usage edge
                    chained_usage = Usage(kind=usage_type, match=symbol, usage_type=UsageType.CHAINED, usage_symbol=dest.parent_symbol, imported_by=None)
                    self.G.add_edge(symbol.node_id, dest.node_id, EdgeType.SYMBOL_USAGE, chained_usage)

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

    @cached_property
    def functions(self) -> list[TSFunction]:
        """Get all functions defined in this namespace.

        Returns:
            List of Function objects in this namespace
        """
        return [symbol for symbol in self.symbols if isinstance(symbol, TSFunction)]

    def get_function(self, name: str, recursive: bool = True, use_full_name: bool = False) -> TSFunction | None:
        """Get a function by name from this namespace.

        Args:
            name: Name of the function to find (can be fully qualified like 'Outer.Inner.func')
            recursive: If True, also search in nested namespaces
            use_full_name: If True, match against the full qualified name

        Returns:
            TSFunction | None: The found function, or None if not found
        """
        if use_full_name and "." in name:
            namespace_path, func_name = name.rsplit(".", 1)
            target_ns = self.get_namespace(namespace_path)
            return target_ns.get_function(func_name, recursive=False) if target_ns else None

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

    @ts_apidoc
    @commiter
    def add_symbol(self, symbol: TSSymbol | str, export: bool = False, remove_original: bool = False) -> TSSymbol:
        """Adds a new symbol to the namespace.

        Args:
            symbol: The symbol to add to the namespace (either a TSSymbol instance or source code string)
            export: Whether to export the symbol. Defaults to False.
            remove_original: Whether to remove the original symbol. Defaults to False.

        Returns:
            The added symbol
        """
        # TODO: Do we need to check if symbol can be added to the namespace?
        # if not self.symbol_can_be_added(symbol):
        #     raise ValueError(f"Symbol {symbol.name} cannot be added to the namespace.")
        # TODO: add symbol by moving
        # TODO: use self.export_symbol() to export the symbol if needed ?

        print("SYMBOL to be added: ", symbol, "export: ", export)
        symbol_name = symbol.name if isinstance(symbol, TSSymbol) else symbol.split(" ")[2 if export else 1]

        # Check if the symbol already exists in file
        existing_symbol = self.get_symbol(symbol_name)
        if existing_symbol is not None:
            return existing_symbol

        # Export symbol if needed, then append to code block
        if isinstance(symbol, str):
            if export and not symbol.startswith("export "):
                symbol = f"export {symbol}"
            self.code_block.statements.append(symbol)
        elif isinstance(symbol, TSSymbol):
            source = symbol.source
            if export and not symbol.is_exported:
                source = f"export {source}"
            self.code_block.statements.append(source)
        self.G.commit_transactions()

        # Remove symbol from original location if remove_original is True
        if remove_original and symbol.parent is not None:
            symbol.parent.remove_symbol(symbol_name)

        self.G.commit_transactions()
        added_symbol = self.get_symbol(symbol_name)
        if added_symbol is None:
            msg = f"Failed to add symbol {symbol_name} to namespace"
            raise ValueError(msg)
        return added_symbol

    @ts_apidoc
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
                    print("stmt to be removed: ", stmt)
                    self.code_block.statements.pop(i)
                    self.G.commit_transactions()
                    return symbol
        return None

    @ts_apidoc
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
        self.G.commit_transactions()

    @commiter
    def export_symbol(self, name: str) -> None:
        """Marks a symbol as exported in the namespace.

        Args:
            name: Name of symbol to export
        """
        symbol = self.get_symbol(name)
        if not symbol or symbol.is_exported:
            return

        export_source = f"export {symbol.source}"
        symbol.parent.edit(export_source)
        self.G.commit_transactions()

    @property
    def valid_import_names(self) -> set[str]:
        """Returns set of valid import names for this namespace.

        This includes all exported symbols plus the namespace name itself
        for namespace imports.
        """
        names = {self.name}  # Namespace itself can be imported
        for stmt in self.code_block.statements:
            if stmt.ts_node_type == "export_statement":
                for export in stmt.exports:
                    names.add(export.name)
        return names

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

    @ts_apidoc
    def resolve_attribute(self, name: str) -> Symbol | None:
        """Resolves an attribute access on the namespace.

        Args:
            name: Name of the attribute to resolve

        Returns:
            The resolved symbol or None if not found
        """
        # First check direct symbols
        if symbol := self.get_symbol(name):
            return symbol

        # Then check nested namespaces recursively
        for nested in self.get_nested_namespaces():
            if symbol := nested.get_symbol(name):
                return symbol

        return None
