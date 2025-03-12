from __future__ import annotations

import os
from collections import deque
from typing import TYPE_CHECKING, Self, override

from codegen.sdk.core.autocommit import reader
from codegen.sdk.core.expressions import Name
from codegen.sdk.core.import_resolution import Import, ImportResolution, WildcardImport
from codegen.sdk.core.interfaces.exportable import Exportable
from codegen.sdk.enums import ImportType, NodeType
from codegen.sdk.utils import find_all_descendants, find_first_ancestor, find_first_descendant
from codegen.shared.decorators.docs import noapidoc, ts_apidoc

if TYPE_CHECKING:
    from collections.abc import Generator

    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.external_module import ExternalModule
    from codegen.sdk.core.interfaces.editable import Editable
    from codegen.sdk.core.node_id_factory import NodeId
    from codegen.sdk.core.statements.import_statement import ImportStatement
    from codegen.sdk.core.symbol import Symbol
    from codegen.sdk.typescript.file import TSFile
    from codegen.sdk.typescript.statements.import_statement import TSImportStatement


@ts_apidoc
class TSImport(Import["TSFile"], Exportable):
    """Extends Import for TypeScript codebases."""

    @reader
    def is_type_import(self) -> bool:
        """Checks if an import is a type import.

        Determines whether an import statement is specifically for types. This includes explicit type imports
        (e.g., 'import type foo from bar'), exports of types, and dynamic imports followed by property access.

        Returns:
            bool: True if the import is a type import, False otherwise.
        """
        if self.ts_node.type == "import_statement":
            return self.source.startswith("import type ")
        elif self.ts_node.type == "export_statement":
            return self.source.startswith("export type ")
        elif call_node := find_first_descendant(self.ts_node, ["call_expression"]):
            # If the import is an import using functions `import` or `require`,
            # assume it is a type import if it is followed by a dot notation
            while call_node.parent and call_node.parent.type in ["await_expression", "parenthesized_expression"]:
                call_node = call_node.parent
            sibling = call_node.next_named_sibling
            return sibling and sibling.type == "property_identifier"
        return False

    @reader
    def is_module_import(self) -> bool:
        """Determines if an import represents a module-level import.

        Module imports represent imports of an entire file rather than specific symbols from a file.
        These imports must traverse through the file to resolve the actual symbol(s) being imported.

        Args:
            self (TSImport): The import object to check.

        Returns:
            bool: True if the import is a module-level import, False otherwise.
                Returns True for:
                - Imports of type MODULE, WILDCARD, or DEFAULT_EXPORT
                - Side effect imports that are not type imports
        """
        if self.import_type in [ImportType.MODULE, ImportType.WILDCARD, ImportType.DEFAULT_EXPORT]:
            return True
        return self.import_type == ImportType.SIDE_EFFECT and not self.is_type_import()

    @reader
    def is_default_import(self) -> bool:
        """Determines whether the import is a default export import.

        Checks if the import is importing a default export from a module. The default export
        may be a single symbol or an entire module.

        Args:
            self (TSImport): The import instance.

        Returns:
            bool: True if the import is a default export import, False otherwise.
        """
        return self.import_type == ImportType.DEFAULT_EXPORT

    @property
    @reader
    def namespace(self) -> str | None:
        """If import is a module import, returns any namespace prefix that must be used with import reference.

        Returns the namespace prefix for import reference when the import is a module import, specifically when
        the import resolves to a file node_type. The namespace is determined by the alias if set, otherwise None.

        Returns:
            str | None: The alias name if the import resolves to a file node_type and has an alias,
                None otherwise.
        """
        resolved_symbol = self.resolved_symbol
        if resolved_symbol is not None and resolved_symbol.node_type == NodeType.FILE:
            return self.alias.source if self.alias is not None else None
        return None

    @property
    @reader
    def imported_exports(self) -> list[Exportable]:
        """Returns the enumerated list of exports imported from a module import.

        Returns a list of exports that this import statement references. The exports can be direct exports
        or re-exports from other modules.

        Returns:
            list[Exportable]: List of exported symbols. Empty list if this import doesn't reference any exports
            or if imported_symbol is None.
        """
        if self.imported_symbol is None:
            return []

        if not self.is_module_import():
            return [] if self.imported_symbol.export is None else [self.imported_symbol.export]

        from_file = self.imported_symbol
        if from_file.node_type != NodeType.FILE:
            return []

        if self.is_default_import():
            return from_file.default_exports

        return from_file.exports

    @property
    @reader
    def resolved_symbol(self) -> Symbol | ExternalModule | TSFile | None:
        """Returns the resolved symbol that the import is referencing.

        Follows the imported symbol and returns the final symbol it resolves to. For default imports, resolves to the exported symbol.
        For module imports with matching symbol names, resolves through module imports to find the matching symbol.
        For indirect imports, follows the import chain to find the ultimate symbol.

        Returns:
            Union[Symbol, ExternalModule, TSFile, None]: The resolved symbol. Returns None if the import cannot be resolved,
            Symbol for resolved import symbols, ExternalModule for external module imports,
            or TSFile for module/file imports.
        """
        imports_seen = set()
        resolved_symbol = self.imported_symbol

        if resolved_symbol is None:
            return None

        # If the default import is a single symbol export, resolve to the symbol
        if self.is_default_import():
            if resolved_symbol is not None and resolved_symbol.node_type == NodeType.FILE:
                file = resolved_symbol
                if len(file.default_exports) == 1 and (export_symbol := file.default_exports[0]).is_default_symbol_export():
                    while export_symbol and export_symbol.node_type == NodeType.EXPORT:
                        export_symbol = export_symbol.exported_symbol
                    resolved_symbol = export_symbol

        # If the imported symbol is a file even though the import is not a module import,
        # hop through the file module imports to resolve the symbol that matches the import symbol name
        if resolved_symbol and resolved_symbol.node_type == NodeType.FILE and not self.is_module_import():
            # Perform BFS search on the file's module imports to find the resolved symbol
            module_imps_seen = set()
            module_imports_to_search = deque([imp for imp in resolved_symbol.imports if imp.is_module_import()])
            while module_imports_to_search:
                module_imp = module_imports_to_search.popleft()
                if module_imp in module_imps_seen:
                    continue

                module_imps_seen.add(module_imp)
                # Search through all the symbols that this module imp is potentially importing!
                for export in module_imp.imported_exports:
                    if export.is_named_export():
                        # TODO: Why does this break? When is symbol_name None?
                        if self.symbol_name is not None and export.name == self.symbol_name.source:
                            resolved_symbol = export.resolved_symbol
                            break
                    else:
                        exported_symbol = export.exported_symbol
                        if isinstance(exported_symbol, TSImport) and exported_symbol.is_module_import():
                            module_imports_to_search.append(exported_symbol)

        # If the imported symbol is an indirect import, hop through the import resolution edges
        while resolved_symbol is not None and resolved_symbol.node_type == NodeType.IMPORT:
            if resolved_symbol in imports_seen:
                return resolved_symbol

            imports_seen.add(resolved_symbol)
            resolved_symbol = resolved_symbol.imported_symbol

        return resolved_symbol

    @reader
    def resolve_import(self, base_path: str | None = None, *, add_module_name: str | None = None) -> ImportResolution[TSFile] | None:
        """Resolves an import statement to its target file and symbol.

        This method is used by GraphBuilder to resolve import statements to their target files and symbols. It handles both relative and absolute imports,
        and supports various import types including named imports, default imports, and module imports.

        Args:
            base_path (str | None): The base path to resolve imports from. If None, uses the codebase's base path
                or the tsconfig base URL.

        Returns:
            ImportResolution[TSFile] | None: An ImportResolution object containing the resolved file and symbol,
                or None if the import could not be resolved (treated as an external module).
                The ImportResolution contains:
                - from_file: The file being imported from
                - symbol: The specific symbol being imported (None for module imports)
                - imports_file: True if importing the entire file/module
        """
        try:
            self.file: TSFile  # Type cast ts_file
            base_path = base_path or self.ctx.projects[0].base_path or ""

            # Get the import source path
            import_source = self.module.source.strip('"').strip("'") if self.module else ""

            # Try to resolve the import using the tsconfig paths
            if self.file.ts_config:
                import_source = self.file.ts_config.translate_import_path(import_source)

            # Check if need to resolve relative import path to absolute path
            relative_import = False
            if import_source.startswith("."):
                relative_import = True

            # Insert base path
            # This has the happen before the relative path resolution
            if not import_source.startswith(base_path):
                import_source = os.path.join(base_path, import_source)

            # If the import is relative, convert it to an absolute path
            if relative_import:
                import_source = self._relative_to_absolute_import(import_source)
            else:
                import_source = os.path.normpath(import_source)

            # covers the case where the import is from a directory ex: "import { postExtract } from './post'"
            import_name = import_source.split("/")[-1]
            if "." not in import_name:
                possible_paths = ["index.ts", "index.js", "index.tsx", "index.jsx"]
                for p_path in possible_paths:
                    if self.ctx.to_absolute(os.path.join(import_source, p_path)).exists():
                        import_source = os.path.join(import_source, p_path)
                        break

            # Loop through all extensions and try to find the file
            extensions = ["", ".ts", ".d.ts", ".tsx", ".d.tsx", ".js", ".jsx"]
            # Try both filename with and without extension
            for import_source_base in (import_source, os.path.splitext(import_source)[0]):
                for extension in extensions:
                    import_source_ext = import_source_base + extension
                    if file := self.ctx.get_file(import_source_ext):
                        if self.is_module_import():
                            return ImportResolution(from_file=file, symbol=None, imports_file=True)
                        else:
                            # If the import is a named import, resolve to the named export in the file
                            if self.symbol_name is None:
                                return ImportResolution(from_file=file, symbol=None, imports_file=True)
                            export_symbol = file.get_export(export_name=self.symbol_name.source)
                            if export_symbol is None:
                                # If the named export is not found, it is importing a module re-export.
                                # In this case, resolve to the file itself and dynamically resolve the symbol later.
                                return ImportResolution(from_file=file, symbol=None, imports_file=True)
                            return ImportResolution(from_file=file, symbol=export_symbol)

            # If the imported file is not found, treat it as an external module
            return None
        except AssertionError:
            # Codebase is probably trying to import file from outside repo
            return None

    @noapidoc
    @reader
    def _relative_to_absolute_import(self, relative_import: str) -> str:
        """Helper to go from a relative import to an absolute one.
        Ex: "./foo/bar" in "src/file.ts" would be -> "src/foo/bar"
        Ex: "../foo/bar" in "project/src/file.ts" would be -> "project/foo/bar"
        """
        import_file_path = self.to_file.file_path  # the filepath the import is in
        import_dir = os.path.dirname(import_file_path)  # the directory of the file this import is in
        absolute_import = os.path.join(import_dir, relative_import)  # absolute path of the import
        normalized_absolute_import = os.path.normpath(absolute_import)  # normalized absolute path of the import. removes redundant separators and './' or '../' segments.
        return normalized_absolute_import

    @classmethod
    @noapidoc
    def from_export_statement(cls, source_node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: TSImportStatement) -> list[TSImport]:
        """Constructs import objects defined from an export statement"""
        export_statement_node = find_first_ancestor(source_node, ["export_statement"])
        imports = []
        if export_clause := next((child for child in export_statement_node.named_children if child.type == "export_clause"), None):
            # === [ Named export import ] ===
            # e.g. export { default as subtract } from './subtract';
            for export_specifier in export_clause.named_children:
                name = export_specifier.child_by_field_name("name")
                alias = export_specifier.child_by_field_name("alias") or name
                import_type = ImportType.DEFAULT_EXPORT if (name and name.text.decode("utf-8") == "default") else ImportType.NAMED_EXPORT
                imp = cls(ts_node=export_statement_node, file_node_id=file_node_id, ctx=ctx, parent=parent, module_node=source_node, name_node=name, alias_node=alias, import_type=import_type)
                imports.append(imp)
        else:
            # ==== [ Wildcard export import ] ====
            # Note: re-exporting using wildcard syntax does NOT include the default export!
            if namespace_export := next((child for child in export_statement_node.named_children if child.type == "namespace_export"), None):
                # Aliased wildcard export (e.g. export * as myNamespace from './m';)
                alias = next(child for child in namespace_export.named_children if child.type == "identifier") or namespace_export
                imp = cls(
                    ts_node=export_statement_node,
                    file_node_id=file_node_id,
                    ctx=ctx,
                    parent=parent,
                    module_node=source_node,
                    name_node=namespace_export,
                    alias_node=alias,
                    import_type=ImportType.WILDCARD,
                )
                imports.append(imp)
            else:
                # No alias wildcard export (e.g. export * from './m';)
                imp = cls(ts_node=export_statement_node, file_node_id=file_node_id, ctx=ctx, parent=parent, module_node=source_node, name_node=None, alias_node=None, import_type=ImportType.WILDCARD)
                imports.append(imp)
        return imports

    @classmethod
    @noapidoc
    def from_import_statement(cls, import_statement_node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: TSImportStatement) -> list[TSImport]:
        source_node = import_statement_node.child_by_field_name("source")
        import_clause = next((x for x in import_statement_node.named_children if x.type == "import_clause"), None)
        if import_clause is None:
            # === [ Side effect module import ] ===
            # Will not have any import usages in the file! (e.g. import './module';)
            return [cls(ts_node=import_statement_node, file_node_id=file_node_id, ctx=ctx, parent=parent, module_node=source_node, name_node=None, alias_node=None, import_type=ImportType.SIDE_EFFECT)]

        imports = []
        for import_type_node in import_clause.named_children:
            if import_type_node.type == "identifier":
                # === [ Default export import ] ===
                # e.g. import a from './module'
                imp = cls(
                    ts_node=import_statement_node,
                    file_node_id=file_node_id,
                    ctx=ctx,
                    parent=parent,
                    module_node=source_node,
                    name_node=import_type_node,
                    alias_node=import_type_node,
                    import_type=ImportType.DEFAULT_EXPORT,
                )
                imports.append(imp)
            elif import_type_node.type == "named_imports":
                # === [ Named export import ] ===
                # e.g. import { a, b as c } from './module';
                for import_specifier in import_type_node.named_children:
                    # Skip comment nodes
                    if import_specifier.type == "comment":
                        continue

                    name_node = import_specifier.child_by_field_name("name")
                    alias_node = import_specifier.child_by_field_name("alias") or name_node
                    imp = cls(
                        ts_node=import_statement_node,
                        file_node_id=file_node_id,
                        ctx=ctx,
                        parent=parent,
                        module_node=source_node,
                        name_node=name_node,
                        alias_node=alias_node,
                        import_type=ImportType.NAMED_EXPORT,
                    )
                    imports.append(imp)  # MODIFY IMPORT HERE ?
            elif import_type_node.type == "namespace_import":
                # === [ Wildcard module import ] ===
                # Imports both default and named exports e.g. import * as someAlias from './module';
                alias_node = next(x for x in import_type_node.named_children if x.type == "identifier")
                imp = cls(
                    ts_node=import_statement_node,
                    file_node_id=file_node_id,
                    ctx=ctx,
                    module_node=source_node,
                    parent=parent,
                    name_node=import_type_node,
                    alias_node=alias_node,
                    import_type=ImportType.WILDCARD,
                )
                imports.append(imp)
        return imports

    @classmethod
    @noapidoc
    def from_dynamic_import_statement(cls, import_call_node: TSNode, module_node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: ImportStatement) -> list[TSImport]:
        """Parses a dynamic import statement, given a reference to the `import`/`require` node and `module` node.
        e.g.
        const myModule = await import('./someFile')`;
        const { exportedFunction, exportedVariable: aliasedVariable } = await import('./someFile');
        import('./someFile');

        const myModule = require('./someFile')`;
        const { exportedFunction, exportedVariable: aliasedVariable } = require('./someFile');
        require('./someFile');
        Note: imports using `require` will import whatever is defined in `module.exports = ...` or `export = ...`
        """
        if module_node is None:
            # TODO: fixme
            return []
        imports = []

        # TODO: FIX THIS, is a horrible hack to avoid a crash on the next.js
        if len(module_node.named_children) == 0:
            return []

        # Grab the first element of dynamic import call expression argument list
        module_node = module_node.named_children[0]

        # Get the top most parent of call expression node that bypasses wrappers that doesn't change the semantics
        call_node = find_first_ancestor(import_call_node, ["call_expression"])
        while call_node.parent and call_node.parent.type in ["await_expression", "parenthesized_expression", "binary_expression", "ternary_expression"]:
            call_node = call_node.parent

        import_statement_node = call_node.parent
        if import_statement_node.type == "expression_statement":
            # ==== [ Side effect module import ] ====
            # Will not have any import usages in the file! (e.g. await import('./module');)
            imp = cls(ts_node=import_statement_node, file_node_id=file_node_id, ctx=ctx, parent=parent, module_node=module_node, name_node=None, alias_node=None, import_type=ImportType.SIDE_EFFECT)
            imports.append(imp)
        else:
            if import_statement_node.type == "member_expression":
                # ==== [ Type import ] ====
                # Imports a type defined in module -- in javascript, type imports are entirely emitted
                # e.g. type DynamicType = typeof import('./module').SomeType;
                #      const MyType = typeof import('./module').SomeType;
                #      const DefaultType = (await import('./module')).default
                #      import('./module').SomeType
                #      function foo(param: import('./module').SomeType) {}
                name_node = import_statement_node.child_by_field_name("property")
                parent_type_names = ["type_alias_declaration", "variable_declarator", "assignment_expression", "expression_statement"]
                import_statement_node = find_first_ancestor(import_statement_node, parent_type_names, max_depth=2) or import_statement_node
            else:
                name_type_name = "left" if import_statement_node.type == "assignment_expression" else "name"
                name_node = import_statement_node.child_by_field_name(name_type_name)

            # TODO: Handle dynamic import name not found (CG-8722)
            if name_node is None:
                alias_node = import_statement_node.child_by_field_name("name") or import_statement_node.child_by_field_name("left")
                imp = cls(
                    ts_node=import_statement_node, file_node_id=file_node_id, ctx=ctx, parent=parent, module_node=module_node, name_node=None, alias_node=alias_node, import_type=ImportType.SIDE_EFFECT
                )
                imports.append(imp)
                return imports

            # If import statement is a variable declaration, capture the variable scoping keyword (const, let, var, etc)
            if import_statement_node.type == "lexical_declaration":
                statement_node = import_statement_node
            else:
                statement_node = import_statement_node.parent if import_statement_node.type in ["variable_declarator", "assignment_expression"] else import_statement_node

            # ==== [ Named dynamic import ] ====
            if name_node.type == "property_identifier":
                # If the type import is being stored into a variable, get the alias
                if import_statement_node.type in ["type_alias_declaration", "variable_declarator"]:
                    alias_node = import_statement_node.child_by_field_name("name")
                elif import_statement_node.type == "assignment_expression":
                    alias_node = import_statement_node.child_by_field_name("left")
                else:
                    alias_node = name_node
                import_type = ImportType.DEFAULT_EXPORT if name_node.text.decode("utf-8") == "default" else ImportType.NAMED_EXPORT
                imp = cls(ts_node=statement_node, file_node_id=file_node_id, ctx=ctx, parent=parent, module_node=module_node, name_node=name_node, alias_node=alias_node, import_type=import_type)
                imports.append(imp)
            elif name_node.type == "identifier":
                # ==== [ Aliased module import ] ====
                # Imports both default and named exports (e.g. const moduleImp = await import('./module');)
                imp = cls(ts_node=statement_node, file_node_id=file_node_id, ctx=ctx, parent=parent, module_node=module_node, name_node=name_node, alias_node=name_node, import_type=ImportType.MODULE)
                imports.append(imp)
            elif name_node.type == "object_pattern":
                # ==== [ Deconstructed import ] ====
                for imported_symbol in name_node.named_children:
                    if imported_symbol.type == "shorthand_property_identifier_pattern":
                        # ==== [ Named export import ] ====
                        # e.g. const { symbol } = await import('./module')
                        imp = cls(
                            ts_node=statement_node,
                            file_node_id=file_node_id,
                            ctx=ctx,
                            parent=parent,
                            module_node=module_node,
                            name_node=imported_symbol,
                            alias_node=imported_symbol,
                            import_type=ImportType.NAMED_EXPORT,
                        )
                        imports.append(imp)
                    elif imported_symbol.type == "pair_pattern":
                        # ==== [ Aliased named export import ] ====
                        # e.g. const { symbol: aliasedSymbol } = await import('./module')
                        name_node = imported_symbol.child_by_field_name("key")
                        alias_node = imported_symbol.child_by_field_name("value")
                        imp = cls(
                            ts_node=statement_node,
                            file_node_id=file_node_id,
                            ctx=ctx,
                            parent=parent,
                            module_node=module_node,
                            name_node=name_node,
                            alias_node=alias_node,
                            import_type=ImportType.NAMED_EXPORT,
                        )
                        imports.append(imp)
                    else:
                        continue
                        # raise ValueError(f"Unexpected alias name node type {imported_symbol.type}")
        return imports

    @property
    @reader
    def import_specifier(self) -> Editable:
        """Retrieves the import specifier node for this import.

        Finds and returns the import specifier node containing this import's name and optional alias.
        For named imports, this is the import_specifier or export_specifier node.
        For other imports, this is the identifier node containing the import name.

        Returns:
            Editable: The import specifier node containing this import's name and alias.
                For named imports, returns the import_specifier/export_specifier node.
                For other imports, returns the identifier node containing the import name.
                Returns None if no matching specifier is found.
        """
        import_specifiers = find_all_descendants(self.ts_node, {"import_specifier", "export_specifier"})
        for import_specifier in import_specifiers:
            alias = import_specifier.child_by_field_name("alias")
            if alias is not None:
                is_match = self.alias.source == alias.text.decode("utf-8")
            else:
                name = import_specifier.child_by_field_name("name")
                is_match = self.symbol_name.source == name.text.decode("utf-8")
            if is_match:
                return Name(import_specifier, self.file_node_id, self.ctx, self)
        if named := next(iter(find_all_descendants(self.ts_node, {"identifier"})), None):
            if named.text.decode("utf-8") == self.symbol_name.source:
                return Name(named, self.file_node_id, self.ctx, self)

    @reader
    def get_import_string(self, alias: str | None = None, module: str | None = None, import_type: ImportType = ImportType.UNKNOWN, is_type_import: bool = False) -> str:
        """Generates an import string for an import statement.

        Generates a string representation of an import statement with optional type and alias information.

        Args:
            alias (str | None): Alias name for the imported symbol. Defaults to None.
            module (str | None): Module name to import from. Defaults to None. If not provided, uses the file's import module name.
            import_type (ImportType): Type of import (e.g. WILDCARD, NAMED_EXPORT). Defaults to ImportType.UNKNOWN.
            is_type_import (bool): Whether this is a type import. Defaults to False.

        Returns:
            str: A string representation of the import statement.
        """
        type_prefix = "type " if is_type_import else ""
        import_module = module if module is not None else self.file.import_module_name

        if import_type == ImportType.WILDCARD:
            file_as_module = self.file.name
            return f"import {type_prefix}* as {file_as_module} from {import_module};"
        elif alias is not None and alias != self.name:
            return f"import {type_prefix}{{ {self.name} as {alias} }} from {import_module};"
        else:
            return f"import {type_prefix}{{ {self.name} }} from {import_module};"

    @property
    @noapidoc
    @override
    def names(self) -> Generator[tuple[str, Self | WildcardImport[Self]], None, None]:
        if self.import_type == ImportType.SIDE_EFFECT:
            return
        yield from super().names

    @override
    def set_import_module(self, new_module: str) -> None:
        """Sets the module of an import.

        Updates the module of an import statement while maintaining the import symbol.
        Uses single quotes by default (TypeScript standard), falling back to double quotes
        only if the path contains single quotes.

        Args:
            new_module (str): The new module path to import from.

        Returns:
            None
        """
        if self.module is None:
            return

        # If already quoted, use as is
        if (new_module.startswith('"') and new_module.endswith('"')) or (new_module.startswith("'") and new_module.endswith("'")):
            self.module.source = new_module
            return

        # Use double quotes if path contains single quotes, otherwise use single quotes (TypeScript standard)
        quote = '"' if "'" in new_module else "'"
        self.module.source = f"{quote}{new_module}{quote}"
