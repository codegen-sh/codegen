from __future__ import annotations

import os
from typing import TYPE_CHECKING

from codegen.sdk.core.autocommit import mover, reader, writer
from codegen.sdk.core.file import SourceFile
from codegen.sdk.core.interfaces.exportable import Exportable
from codegen.sdk.enums import ImportType, NodeType, SymbolType
from codegen.sdk.extensions.sort import sort_editables
from codegen.sdk.extensions.utils import cached_property
from codegen.sdk.typescript.assignment import TSAssignment
from codegen.sdk.typescript.class_definition import TSClass
from codegen.sdk.typescript.detached_symbols.code_block import TSCodeBlock
from codegen.sdk.typescript.export import TSExport
from codegen.sdk.typescript.function import TSFunction
from codegen.sdk.typescript.import_resolution import TSImport
from codegen.sdk.typescript.interface import TSInterface
from codegen.sdk.typescript.interfaces.has_block import TSHasBlock
from codegen.sdk.typescript.namespace import TSNamespace
from codegen.sdk.utils import calculate_base_path
from codegen.shared.decorators.docs import noapidoc, ts_apidoc
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.statements.export_statement import ExportStatement
    from codegen.sdk.core.symbol import Symbol
    from codegen.sdk.typescript.detached_symbols.promise_chain import TSPromiseChain
    from codegen.sdk.typescript.symbol import TSSymbol
    from codegen.sdk.typescript.ts_config import TSConfig
    from codegen.sdk.typescript.type_alias import TSTypeAlias


@ts_apidoc
class TSFile(SourceFile[TSImport, TSFunction, TSClass, TSAssignment, TSInterface, TSCodeBlock], TSHasBlock, Exportable):
    """Extends the SourceFile class to provide TypeScript-specific functionality.

    Attributes:
        programming_language: The programming language of the file. Set to ProgrammingLanguage.TYPESCRIPT.
        ts_config: The ts_config file nearest to this file.
    """

    programming_language = ProgrammingLanguage.TYPESCRIPT
    ts_config: TSConfig | None = None

    @cached_property
    @reader(cache=False)
    def exports(self) -> list[TSExport]:
        """Returns all Export symbols in the file.

        Retrieves a list of all top-level export declarations in the current TypeScript file.
        Does not include exports inside namespaces.

        Returns:
            list[TSExport]: A list of TSExport objects representing all top-level export declarations in the file.
        """
        # Filter to only get exports that are direct children of the file's code block
        return sort_editables(filter(lambda node: isinstance(node, TSExport) and ((node.parent.parent.parent == self) or (node.parent.parent == self)), self.get_nodes(sort=False)), by_id=True)

    @property
    @reader(cache=False)
    def export_statements(self) -> list[ExportStatement[TSExport]]:
        """Returns a list of all export statements in the file.

        Each export statement in the returned list can contain multiple exports. The export statements
        are sorted by their position in the file.

        Args:
            None

        Returns:
            list[ExportStatement[TSExport]]: A list of ExportStatement objects, where each ExportStatement
                contains one or more TSExport objects.
        """
        export_statements = [exp.export_statement for exp in self.exports]
        return sort_editables(export_statements)

    @property
    @reader(cache=False)
    def default_exports(self) -> list[TSExport]:
        """Returns all default export symbols from the file.

        A property method that retrieves all export objects that are designated as default exports from the file.

        Returns:
            list[TSExport]: A list of default export objects. Each object belongs to a single export statement.
        """
        return [x for x in self.exports if x.is_default_export()]

    @property
    @reader
    def named_exports(self) -> list[TSExport]:
        """Returns the named exports declared in the file.

        Gets all export statements in the file that are not default exports. These exports are defined
        using the `export` keyword rather than `export default`.

        Args:
            self (TSFile): The TypeScript file object.

        Returns:
            list[TSExport]: A list of TSExport objects representing named exports in the file.
        """
        return [x for x in self.exports if not x.is_default_export()]

    @reader
    def get_export(self, export_name: str) -> TSExport | None:
        """Returns an export object with the specified name from the file.

        This method searches for an export with the given name in the file.

        Args:
            export_name (str): The name of the export to find.

        Returns:
            TSExport | None: The export object if found, None otherwise.
        """
        return next((x for x in self.exports if x.name == export_name), None)

    @property
    @reader
    def interfaces(self) -> list[TSInterface]:
        """Returns all Interfaces in the file.

        Retrieves all symbols in the file that are of type Interface.

        Args:
            None

        Returns:
            list[TSInterface]: A list of TypeScript interface symbols defined in the file.
        """
        return [s for s in self.symbols if s.symbol_type == SymbolType.Interface]

    @reader
    def get_interface(self, name: str) -> TSInterface | None:
        """Retrieves a specific interface from the file by its name.

        Args:
            name (str): The name of the interface to find.

        Returns:
            TSInterface | None: The interface with the specified name if found, None otherwise.
        """
        return next((x for x in self.interfaces if x.name == name), None)

    @property
    @reader
    def types(self) -> list[TSTypeAlias]:
        """Returns all type aliases in the file.

        Retrieves a list of all type aliases defined in the current TypeScript/JavaScript file.

        Returns:
            list[TSTypeAlias]: A list of all type aliases in the file. Empty list if no type aliases are found.
        """
        return [s for s in self.symbols if s.symbol_type == SymbolType.Type]

    @reader
    def get_type(self, name: str) -> TSTypeAlias | None:
        """Returns a specific Type by name from the file's types.

        Retrieves a TypeScript type alias by its name from the file's collection of types.

        Args:
            name (str): The name of the type alias to retrieve.

        Returns:
            TSTypeAlias | None: The TypeScript type alias with the matching name, or None if not found.
        """
        return next((x for x in self.types if x.name == name), None)

    @staticmethod
    def get_extensions() -> list[str]:
        """Returns a list of file extensions that this class can parse.

        Returns a list of file extensions for TypeScript and JavaScript files that this File class can parse and process.

        Returns:
            list[str]: A list of file extensions including '.tsx', '.ts', '.jsx', and '.js'.
        """
        return [".tsx", ".ts", ".jsx", ".js"]

    def symbol_can_be_added(self, symbol: TSSymbol) -> bool:
        """Determines if a TypeScript symbol can be added to this file based on its type and JSX compatibility.

        This method checks whether a given symbol can be added to the current TypeScript file by validating its compatibility with the file's extension.
        In particular, it ensures that JSX functions are only added to appropriate file types (.tsx or .jsx).

        Args:
            symbol (TSSymbol): The TypeScript symbol to be checked.

        Returns:
            bool: True if the symbol can be added to this file, False otherwise.
        """
        if symbol.symbol_type == SymbolType.Function:
            if symbol.is_jsx:
                if not (self.file_path.endswith("tsx") or self.file_path.endswith("jsx")):
                    return False
        return True

    @reader
    def get_config(self) -> TSConfig | None:
        """Returns the nearest tsconfig.json applicable to this file.

        Gets the TypeScript configuration for the current file by retrieving the nearest tsconfig.json file in the directory hierarchy.

        Returns:
            TSConfig | None: The TypeScript configuration object if found, None otherwise.
        """
        return self.ts_config

    @writer
    def add_export_to_symbol(self, symbol: TSSymbol) -> None:
        """Adds an export keyword to a symbol in a TypeScript file.

        Marks a symbol for export by adding the 'export' keyword. This modifies the symbol's
        declaration to make it available for import by other modules.

        Args:
            symbol (TSSymbol): The TypeScript symbol (function, class, interface, etc.) to be exported.

        Returns:
            None
        """
        # TODO: this should be in symbol.py class. Rename as `add_export`
        symbol.add_keyword("export")

    @writer
    def remove_unused_exports(self) -> None:
        """Removes unused exports from the file.

        Analyzes all exports in the file and removes any that are not used. An export is considered unused if it has no direct
        symbol usages and no re-exports that are used elsewhere in the codebase.

        When removing unused exports, the method also cleans up any related unused imports. For default exports, it removes
        the 'export default' keyword, and for named exports, it removes the 'export' keyword or the entire export statement.

        Args:
            None

        Returns:
            None
        """
        for export in self.exports:
            symbol_export_unused = True
            symbols_to_remove = []

            exported_symbol = export.resolved_symbol
            for export_usage in export.symbol_usages:
                if export_usage.node_type == NodeType.IMPORT or (export_usage.node_type == NodeType.EXPORT and export_usage.resolved_symbol != exported_symbol):
                    # If the import has no usages then we can add the import to the list of symbols to remove
                    reexport_usages = export_usage.symbol_usages
                    if len(reexport_usages) == 0:
                        symbols_to_remove.append(export_usage)
                        break

                    # If any of the import's usages are valid symbol usages, export is used.
                    if any(usage.node_type == NodeType.SYMBOL for usage in reexport_usages):
                        symbol_export_unused = False
                        break

                    symbols_to_remove.append(export_usage)

                elif export_usage.node_type == NodeType.SYMBOL:
                    symbol_export_unused = False
                    break

            # export is not used, remove it
            if symbol_export_unused:
                # remove the unused imports
                for imp in symbols_to_remove:
                    imp.remove()

                if exported_symbol == exported_symbol.export.declared_symbol:
                    # change this to be more robust
                    if exported_symbol.source.startswith("export default "):
                        exported_symbol.replace("export default ", "")
                    else:
                        exported_symbol.replace("export ", "")
                else:
                    exported_symbol.export.remove()
                if exported_symbol.export != export:
                    export.remove()

    @noapidoc
    def _get_export_data(self, relative_path: str, export_type: str = "EXPORT") -> tuple[tuple[str, str], dict[str, callable]]:
        quoted_paths = (f"'{relative_path}'", f'"{relative_path}"')
        export_type_conditions = {
            "WILDCARD": lambda exp: exp.is_wildcard_export(),
            "TYPE": lambda exp: exp.is_type_export(),
            # Changed this condition - it was incorrectly handling type exports
            "EXPORT": lambda exp: (not exp.is_type_export() and not exp.is_wildcard_export()),
        }
        return quoted_paths, export_type_conditions

    @reader
    def has_export_statement_for_path(self, relative_path: str, export_type: str = "EXPORT") -> bool:
        """Checks if the file has exports of specified type that contains the given path in single or double quotes.

        Args:
            relative_path (str): The path to check for in export statements
            export_type (str): Type of export to check for - "WILDCARD", "TYPE", or "EXPORT" (default)

        Returns:
            bool: True if there exists an export of specified type with the exact relative path (quoted)
                  in its source, False otherwise.
        """
        if not self.export_statements:
            return False

        quoted_paths, export_type_conditions = self._get_export_data(relative_path, export_type)
        condition = export_type_conditions[export_type]

        return any(any(quoted_path in stmt.source for quoted_path in quoted_paths) and any(condition(exp) for exp in stmt.exports) for stmt in self.export_statements)

    ####################################################################################################################
    # GETTERS
    ####################################################################################################################

    @reader
    def get_export_statement_for_path(self, relative_path: str, export_type: str = "EXPORT") -> ExportStatement | None:
        """Gets the first export of specified type that contains the given path in single or double quotes.

        Args:
            relative_path (str): The path to check for in export statements
            export_type (str): Type of export to get - "WILDCARD", "TYPE", or "EXPORT" (default)

        Returns:
            TSExport | None: The first matching export if found, None otherwise.
        """
        if not self.export_statements:
            return None

        quoted_paths, export_type_conditions = self._get_export_data(relative_path, export_type)
        condition = export_type_conditions[export_type]

        for stmt in self.export_statements:
            if any(quoted_path in stmt.source for quoted_path in quoted_paths):
                for exp in stmt.exports:
                    if condition(exp):
                        return exp

        return None

    @noapidoc
    def get_import_module_name_for_file(self, filepath: str, ctx: CodebaseContext) -> str:
        """Returns the module name that this file gets imported as"""
        # TODO: support relative and absolute module path
        import_path = filepath

        # Apply path import aliases to import_path
        if self.ts_config:
            import_path = self.ts_config.translate_absolute_path(import_path)

        # Remove file extension
        import_path = os.path.splitext(import_path)[0]
        return f"'{import_path}'"

    @reader
    def get_import_string(self, alias: str | None = None, module: str | None = None, import_type: ImportType = ImportType.UNKNOWN, is_type_import: bool = False) -> str:
        """Generates and returns an import statement for the file.

        Constructs an import statement string based on the file's name and module information.

        Args:
            alias (str | None): Alternative name for the imported module. Defaults to None.
            module (str | None): Module path to import from. If None, uses file's default module name.
            import_type (ImportType): The type of import statement. Defaults to ImportType.UNKNOWN.
            is_type_import (bool): Whether this is a type-only import. Defaults to False.

        Returns:
            str: A formatted import statement string importing all exports from the module.
        """
        import_module = module if module is not None else self.import_module_name
        file_module = self.name
        return f"import * as {file_module} from {import_module}"

    @cached_property
    @noapidoc
    @reader(cache=True)
    def valid_import_names(self) -> dict[str, Symbol | TSImport]:
        """Returns a dict mapping name => Symbol (or import) in this file that can be imported from another file"""
        valid_export_names = {}
        if len(self.default_exports) == 1:
            valid_export_names["default"] = self.default_exports[0]
        for export in self.exports:
            for name, dest in export.names:
                valid_export_names[name] = dest
        return valid_export_names

    ####################################################################################################################
    # MANIPULATIONS
    ####################################################################################################################

    @mover
    def update_filepath(self, new_filepath: str) -> None:
        """Updates the file path of the current file and all associated imports.

        Renames the current file to a new file path and updates all imports that reference this file to point to the new location.

        Args:
            new_filepath (str): The new file path to move the file to.

        Returns:
            None
        """
        # =====[ Add the new filepath as a new file node in the graph ]=====
        new_file = self.ctx.node_classes.file_cls.from_content(new_filepath, self.content, self.ctx)
        # =====[ Change the file on disk ]=====
        self.transaction_manager.add_file_rename_transaction(self, new_filepath)
        # =====[ Update all the inbound imports to point to the new module ]=====
        for imp in self.inbound_imports:
            existing_imp = imp.module.source.strip("'")
            new_module_name = new_file.import_module_name.strip("'")
            # Web specific hacks
            if self.ctx.repo_name == "web":
                if existing_imp.startswith("./"):
                    relpath = calculate_base_path(new_filepath, existing_imp)
                    new_module_name = new_module_name.replace(relpath, ".")
                elif existing_imp.startswith("~/src"):
                    new_module_name = new_module_name.replace("src/", "~/src/")
            imp.set_import_module(f"'{new_module_name}'")

    @reader
    def get_namespace(self, name: str) -> TSNamespace | None:
        """Returns a specific namespace by name from the file's namespaces.

        Args:
            name (str): The name of the namespace to find.

        Returns:
            TSNamespace | None: The namespace with the specified name if found, None otherwise.
        """
        return next((x for x in self.symbols if isinstance(x, TSNamespace) and x.name == name), None)

    @property
    @reader
    def promise_chains(self) -> list[TSPromiseChain]:
        """Returns all promise chains in the file.

        Returns:
            list[TSPromiseChain]: A list of promise chains in the file.
        """
        promise_chains = []
        for function in self.functions:
            for promise_chain in function.promise_chains:
                promise_chains.append(promise_chain)
        return promise_chains
