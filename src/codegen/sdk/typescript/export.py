from __future__ import annotations

from typing import TYPE_CHECKING, Generic, Literal, Self, TypeVar, override

from codegen.sdk.core.autocommit import commiter, reader
from codegen.sdk.core.autocommit.decorators import writer
from codegen.sdk.core.dataclasses.usage import UsageKind, UsageType
from codegen.sdk.core.export import Export
from codegen.sdk.core.expressions.name import Name
from codegen.sdk.core.external_module import ExternalModule
from codegen.sdk.core.import_resolution import Import
from codegen.sdk.core.interfaces.chainable import Chainable
from codegen.sdk.core.interfaces.has_value import HasValue
from codegen.sdk.core.interfaces.importable import Importable
from codegen.sdk.enums import EdgeType, ImportType, NodeType
from codegen.sdk.extensions.utils import cached_property
from codegen.sdk.typescript.assignment import TSAssignment
from codegen.sdk.typescript.class_definition import TSClass
from codegen.sdk.typescript.enum_definition import TSEnum
from codegen.sdk.typescript.enums import TSFunctionTypeNames
from codegen.sdk.typescript.function import TSFunction
from codegen.sdk.typescript.import_resolution import TSImport
from codegen.sdk.typescript.interface import TSInterface
from codegen.sdk.typescript.namespace import TSNamespace
from codegen.sdk.typescript.statements.assignment_statement import TSAssignmentStatement
from codegen.sdk.typescript.type_alias import TSTypeAlias
from codegen.sdk.utils import find_all_descendants
from codegen.shared.decorators.docs import noapidoc, ts_apidoc

if TYPE_CHECKING:
    from collections.abc import Generator

    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.codebase.resolution_stack import ResolutionStack
    from codegen.sdk.core.interfaces.exportable import Exportable
    from codegen.sdk.core.interfaces.has_name import HasName
    from codegen.sdk.core.node_id_factory import NodeId
    from codegen.sdk.core.statements.export_statement import ExportStatement
    from codegen.sdk.core.symbol_groups.collection import Collection
    from codegen.sdk.typescript.symbol import TSSymbol


@ts_apidoc
class TSExport(Export["Collection[TSExport, ExportStatement[TSExport]]"], HasValue, Chainable):
    """Represents a single exported symbol.

    There is a 1:M relationship between an ExportStatement and an Export

    Attributes:
        node_type: The type of the node, set to NodeType.EXPORT.
    """

    _declared_symbol: TSSymbol | TSImport | None
    _exported_symbol: Name | None
    _name_node: Name | None
    node_type: Literal[NodeType.EXPORT] = NodeType.EXPORT

    def __init__(
        self,
        ts_node: TSNode,
        file_node_id: NodeId,
        parent: Collection[TSExport, ExportStatement[TSExport]],
        ctx: CodebaseContext,
        name_node: TSNode | None = None,
        declared_symbol: TSSymbol | TSImport | None = None,
        exported_symbol: TSNode | None = None,
        value_node: TSNode | None = None,
    ) -> None:
        """Given an `export_statement` tree sitter node, parses all implicit export symbols."""
        if declared_symbol and exported_symbol and declared_symbol.name != exported_symbol.text.decode("utf-8"):
            msg = "The exported symbol name must match the declared symbol name"
            raise ValueError(msg)

        super().__init__(ts_node, file_node_id, ctx, parent)
        self._name_node = self._parse_expression(name_node, default=Name)
        self._declared_symbol = declared_symbol
        self._exported_symbol = self._parse_expression(exported_symbol, default=Name)
        # if self.is_wildcard_export():
        #     self.node_id = NodeIdFactory.export_node_id(name=f"wildcard_export_<{self._declared_symbol.node_id}>", file_id=self.file_node_id, is_default=self.is_default_export())
        # else:
        #     self.node_id = NodeIdFactory.export_node_id(name=self.name, file_id=self.file_node_id, is_default=self.is_default_export())
        self.parse(ctx)
        self._value_node = self._parse_expression(value_node)

    @classmethod
    @noapidoc
    def from_export_statement_with_declaration(
        cls,
        export_statement: TSNode,
        declaration: TSNode,
        file_id: NodeId,
        ctx: CodebaseContext,
        parent: ExportStatement[TSExport],
        pos: int,
    ) -> list[TSExport]:
        declared_symbols = []

        # =====[ Symbol Definitions ]=====
        if declaration.type in ["function_declaration", "generator_function_declaration"]:
            # e.g. export function* namedGenerator() {}
            declared_symbols.append(TSFunction(declaration, file_id, ctx, parent))
        elif declaration.type == "class_declaration":
            # e.g. export class NamedClass {}
            declared_symbols.append(TSClass(declaration, file_id, ctx, parent))
        elif declaration.type in ["variable_declaration", "lexical_declaration"]:
            if len(arrow_functions := find_all_descendants(declaration, {"arrow_function"}, max_depth=2)) > 0:
                # e.g. export const arrowFunction = () => {}, but not export const a = { func: () => null }
                for arrow_func in arrow_functions:
                    declared_symbols.append(TSFunction.from_function_type(arrow_func, file_id, ctx, parent))
            else:
                # e.g. export const a = value;
                for child in declaration.named_children:
                    if child.type in TSAssignmentStatement.assignment_types:
                        s = TSAssignmentStatement.from_assignment(declaration, file_id, ctx, parent.parent, pos, assignment_node=child)
                        declared_symbols.extend(s.assignments)
        elif declaration.type == "interface_declaration":
            # e.g. export interface MyInterface {}
            declared_symbols.append(TSInterface(declaration, file_id, ctx, parent))
        elif declaration.type == "type_alias_declaration":
            # e.g. export type MyType = {}
            declared_symbols.append(TSTypeAlias(declaration, file_id, ctx, parent))
        elif declaration.type == "enum_declaration":
            # e.g. export enum MyEnum {}
            declared_symbols.append(TSEnum(declaration, file_id, ctx, parent))
        elif declaration.type == "internal_module":
            # e.g. export namespace MyNamespace {}
            declared_symbols.append(TSNamespace(declaration, file_id, ctx, parent))
        else:
            declared_symbols.append(None)

        exports = []
        for declared_symbol in declared_symbols:
            name_node = declared_symbol._name_node.ts_node if declared_symbol and declared_symbol._name_node else declaration
            export = cls(ts_node=declaration, file_node_id=file_id, ctx=ctx, name_node=name_node, declared_symbol=declared_symbol, parent=parent.exports)
            exports.append(export)
        return exports

    @classmethod
    @noapidoc
    def from_export_statement_with_value(cls, export_statement: TSNode, value: TSNode, file_id: NodeId, ctx: CodebaseContext, parent: ExportStatement[TSExport], pos: int) -> list[TSExport]:
        declared_symbols = []
        exported_name_and_symbol = []  # tuple of export name node and export symbol name
        detached_value_node = None

        # =====[ Symbol Definitions ]=====
        if value.type in [function_type.value for function_type in TSFunctionTypeNames]:
            # e.g. export default async function() {}
            declared_symbols.append(parent._parse_expression(value))
        elif value.type == "class":
            # e.g. export default class {}
            declared_symbols.append(parent._parse_expression(value, default=TSClass))
        elif value.type == "object":
            # e.g. export default { a, b, c }, export = { a, b, c }
            # Export symbol usage will get resolved in _compute_dependencies based on identifiers in value
            # TODO: parse as TSDict
            detached_value_node = value
            for child in value.named_children:
                if child.type == "pair":
                    key_value = child.child_by_field_name("key")
                    pair_value = child.child_by_field_name("value")
                    if pair_value.type in [function_type.value for function_type in TSFunctionTypeNames]:
                        declared_symbols.append(TSFunction(pair_value, file_id, ctx, parent))
                    elif pair_value.type == "class":
                        declared_symbols.append(TSClass(pair_value, file_id, ctx, parent))
                    else:
                        exported_name_and_symbol.append((key_value, pair_value))
                elif child.type == "shorthand_property_identifier":
                    exported_name_and_symbol.append((child, child))
        elif value.type == "assignment_expression":
            left = value.child_by_field_name("left")
            right = value.child_by_field_name("right")
            assignment = TSAssignment(value, file_id, ctx, parent, left, right, left)
            declared_symbols.append(assignment)
        else:
            # Other values are detached symbols: array, number, string, true, null, undefined, new_expression, call_expression
            # Export symbol usage will get resolved in _compute_dependencies based on identifiers in value
            detached_value_node = value
            declared_symbols.append(None)

        exports = []
        for declared_symbol in declared_symbols:
            if declared_symbol is None:
                name_node = value
            else:
                name_node = declared_symbol._name_node.ts_node if declared_symbol._name_node else declared_symbol.ts_node
            export = cls(ts_node=export_statement, file_node_id=file_id, ctx=ctx, name_node=name_node, declared_symbol=declared_symbol, value_node=detached_value_node, parent=parent.exports)
            exports.append(export)
        for name_node, symbol_name_node in exported_name_and_symbol:
            exports.append(cls(ts_node=export_statement, file_node_id=file_id, ctx=ctx, name_node=name_node, exported_symbol=symbol_name_node, value_node=detached_value_node, parent=parent.exports))
        return exports

    @noapidoc
    @commiter
    def parse(self, ctx: CodebaseContext) -> None:
        pass

    @noapidoc
    @commiter
    def _compute_dependencies(self, usage_type: UsageKind | None = None, dest: HasName | None = None) -> None:
        if self.exported_symbol:
            for frame in self.resolved_type_frames:
                if frame.parent_frame:
                    frame.parent_frame.add_usage(self._name_node or self, UsageKind.EXPORTED_SYMBOL, self, self.ctx)
        elif self._exported_symbol:
            if not next(self.resolve_name(self._exported_symbol.source), None):
                self._exported_symbol._compute_dependencies(UsageKind.BODY, dest=dest or self)
        elif self.value:
            self.value._compute_dependencies(UsageKind.EXPORTED_SYMBOL, self)

    @noapidoc
    @commiter
    def compute_export_dependencies(self) -> None:
        """Create Export edges from this export to it's used symbols"""
        if self.declared_symbol is not None:
            assert self.ctx.has_node(self.declared_symbol.node_id)
            self.ctx.add_edge(self.node_id, self.declared_symbol.node_id, type=EdgeType.EXPORT)
        elif self._exported_symbol is not None:
            symbol_name = self._exported_symbol.source
            if (used_node := next(self.resolve_name(symbol_name), None)) and isinstance(used_node, Importable) and self.ctx.has_node(used_node.node_id):
                self.ctx.add_edge(self.node_id, used_node.node_id, type=EdgeType.EXPORT)
        elif self.value is not None:
            if isinstance(self.value, Chainable):
                for resolved in self.value.resolved_types:
                    if self.ctx.has_node(getattr(resolved, "node_id", None)):
                        self.ctx.add_edge(self.node_id, resolved.node_id, type=EdgeType.EXPORT)
        elif self.name is None:
            # This is the export *; case
            self.ctx.add_edge(self.node_id, self.file_node_id, type=EdgeType.EXPORT)
        if self.is_wildcard_export():
            for file in self.file.importers:
                file.__dict__.pop("valid_symbol_names", None)
                file.__dict__.pop("valid_import_names", None)

    @reader
    def is_named_export(self) -> bool:
        """Determines whether this export is a named export.

        Named exports are exports that are not default exports. For example, `export const foo = 'bar'` is a named export,
        while `export default foo` is not.

        Returns:
            bool: True if this is a named export, False if it is a default export.
        """
        return not self.is_default_export()

    @reader
    def is_default_export(self) -> bool:
        """Determines if an export is the default export for a file.

        This function checks if the export is a default export by examining the export source code and the export's symbol. It handles various cases of default exports including:
        - Re-exports as default (`export { foo as default }`)
        - Default exports (`export default foo`)
        - Module exports (`export = foo`)

        Returns:
            bool: True if this is a default export, False otherwise.
        """
        exported_symbol = self.exported_symbol
        if exported_symbol and isinstance(exported_symbol, TSImport) and exported_symbol.is_default_import():
            return True

        # ==== [ Case: Named re-export as default ] ====
        # e.g. export { foo as default } from './other-module';
        exported_symbol = self.exported_symbol
        if exported_symbol is not None and exported_symbol.node_type == NodeType.IMPORT and exported_symbol.source == self.source:
            return self.name == "default"

        # ==== [ Case: Default export ] ====
        # e.g. export default foo; export default { foo }; export = foo; export = { foo };
        return self.parent.parent.source.startswith("export default ") or self.parent.parent.source.startswith("export = ")

    @reader
    def is_default_symbol_export(self) -> bool:
        """Returns True if this is exporting a default symbol, as opposed to a default object export.

        This method checks if an export is a default symbol export (e.g. 'export default foo') rather than a default object export (e.g. 'export default { foo }').
        It handles both direct exports and re-exports.

        Args:
            self (TSExport): The export object being checked.

        Returns:
            bool: True if this is a default symbol export, False otherwise.
        """
        if not self.is_default_export():
            return False

        # ==== [ Case: Default import re-export ] ====
        exported_symbol = self.exported_symbol
        if exported_symbol is not None and exported_symbol.node_type == NodeType.IMPORT and exported_symbol.source == self.source:
            return self.name == "default"

        # === [ Case: Default symbol export ] ====
        export_object = next((x for x in self.ts_node.children if x.type == "object"), None)
        return export_object is None

    @reader
    def is_type_export(self) -> bool:
        """Determines if this export is exclusively exporting a type.

        Checks if this export starts with "export type" to identify if it's only exporting a type definition.
        This method is used to distinguish between value exports and type exports in TypeScript.

        Returns:
            bool: True if this is a type-only export, False otherwise.
        """
        # TODO: do this more robustly
        return self.source.startswith("export type ")

    @reader
    def is_reexport(self) -> bool:
        """Returns whether the export is re-exporting an import or export.

        Checks if this export node is re-exporting a symbol that was originally imported from another module or exported from another location. This includes wildcard re-exports of entire modules.

        Args:
            self (TSExport): The export node being checked.

        Returns:
            bool: True if this export re-exports an imported/exported symbol or entire module, False otherwise.
        """
        if exported_symbol := self.exported_symbol:
            return exported_symbol.node_type == NodeType.IMPORT or exported_symbol.node_type == NodeType.EXPORT or exported_symbol == self.file
        return False

    @reader
    def is_wildcard_export(self) -> bool:
        """Determines if the export is a wildcard export.

        Checks if the export statement contains a wildcard export pattern 'export *' or 'export *;'. A wildcard export exports all symbols from a module.

        Returns:
            bool: True if the export is a wildcard export (e.g. 'export * from "./module"'), False otherwise.
        """
        return "export * " in self.source or "export *;" in self.source

    @reader
    def is_module_export(self) -> bool:
        """Determines if the export is exporting a module rather than a symbol.

        Returns True if the export is a wildcard export (e.g. 'export *') or if it is a default export but not of a symbol (e.g. 'export default { foo }').

        Returns:
            bool: True if the export represents a module export, False otherwise.
        """
        return self.is_wildcard_export() or (self.is_default_export() and not self.is_default_symbol_export())

    @property
    @reader(cache=False)
    def declared_symbol(self) -> TSSymbol | TSImport | None:
        """Returns the symbol that was defined in this export.

        Returns the symbol that was directly declared within this export statement. For class, function,
        interface, type alias, enum declarations or assignments, returns the declared symbol.
        For re-exports or exports without declarations, returns None.

        Returns:
            Union[TSSymbol, TSImport, None]: The symbol declared within this export statement,
                or None if no symbol was declared.
        """
        return self._declared_symbol

    @property
    @reader
    def exported_symbol(self) -> Exportable | None:
        """Returns the symbol, file, or import being exported from this export object.

        Retrieves the symbol or module being exported by this export node by finding the node connected via an EXPORT edge.
        This method is the inverse of Import.imported_symbol.

        Args:
            None

        Returns:
            Exportable | None: The exported symbol, file, or import, or None if no symbol is exported.
        """
        return next(iter(self.ctx.successors(self.node_id, edge_type=EdgeType.EXPORT)), None)

    @property
    @reader
    def resolved_symbol(self) -> Exportable | None:
        """Returns the Symbol, SourceFile or External module that this export resolves to.

        Recursively traverses through indirect imports and exports to find the final resolved symbol.
        This is useful for determining what symbol an export ultimately points to, particularly in cases of re-exports and import-export chains.

        Returns:
            Exportable | None: The final resolved Symbol, SourceFile or External module, or None if the resolution fails. The resolution follows this chain:
                - If the symbol is an Import, resolves to its imported symbol
                - If the symbol is an Export, resolves to its exported symbol
                - Otherwise returns the symbol itself

        Note:
            Handles circular references by tracking visited symbols to prevent infinite loops.
        """
        ix_seen = set()
        resolved_symbol = self.exported_symbol

        while resolved_symbol is not None and (resolved_symbol.node_type == NodeType.IMPORT or resolved_symbol.node_type == NodeType.EXPORT):
            if resolved_symbol in ix_seen:
                return resolved_symbol

            ix_seen.add(resolved_symbol)
            if resolved_symbol.node_type == NodeType.IMPORT:
                resolved_symbol = resolved_symbol.resolved_symbol
            else:
                resolved_symbol = resolved_symbol.exported_symbol

        return resolved_symbol

    @writer
    def make_non_default(self) -> None:
        """Converts the export to a named export.

        Transforms default exports into named exports by modifying the export syntax and updating any corresponding export/import usages.
        For default exports, it removes the 'default' keyword and adjusts all import statements that reference this export.

        Args:
            None

        Returns:
            None
        """
        if self.is_default_export():
            # Default node is:
            # export default foo = ...
            #        ^^^^^^^
            default_node = self.parent.parent._anonymous_children[1]

            if default_node.ts_node.type == "default":
                if isinstance(self.declared_symbol, TSAssignment):
                    # Converts `export default foo` to `export const foo`
                    default_node.edit("const")
                else:
                    # Converts `export default foo` to `export { foo }`
                    default_node.remove()
                    if name_node := self.get_name():
                        name_node.insert_before("{ ", newline=False)
                        name_node.insert_after(" }", newline=False)

                # Update all usages of this export
                for usage in self.usages(usage_types=UsageType.DIRECT):
                    if usage.match is not None and usage.kind == UsageKind.IMPORTED:
                        # === [ Case: Exported Symbol ] ===
                        # Fixes Exports of the form `export { ... } from ...`
                        if usage.usage_symbol.source.startswith("export") and usage.match.source == "default":
                            # Export clause is:
                            # export { default as foo } from ...
                            #        ^^^^^^^^^^^^^^^^^^
                            export_clause = usage.usage_symbol.children[0]
                            for export_specifier in export_clause.children:
                                # This is the case where `export { ... as ... }`
                                if len(export_specifier.children) == 2 and export_specifier.children[0] == usage.match:
                                    if export_specifier.children[1].source == self.name:
                                        # Converts `export { default as foo }` to `export { foo }`
                                        export_specifier.edit(self.name)
                                    else:
                                        # Converts `export { default as renamed_foo }` to `export { foo as renamed_foo }`
                                        usage.match.edit(self.name)
                                # This is the case where `export { ... } from ...`, (specifically `export { default }`)
                                elif len(export_specifier.children) == 1 and export_specifier.children[0] == usage.match:
                                    # Converts `export { default }` to `export { foo }`
                                    export_specifier.edit(self.name)

                        # === [ Case: Imported Symbol ] ===
                        # Fixes Imports of the form `import { default as foo }`
                        else:
                            # Import clause is:
                            # import A, { B } from ...
                            #        ^^^^^^^^
                            import_clause = usage.usage_symbol.children[0]

                            # Fixes imports of the form `import foo, { ... } from ...`
                            if len(import_clause.children) > 1 and import_clause.children[0] == usage.match:
                                # This is a terrible hack :skull:

                                # Named imports are:
                                # import foo, { ... }
                                #             ^^^^^^^
                                named_imports = import_clause.children[1]

                                # This converts `import foo, { bar, baz as waz }` to `import { foo, bar, baz as waz }`
                                import_clause.children[0].remove()  # Remove `foo, `
                                named_imports.children[0].insert_before(f"{self.name}, ", newline=False)  # Add the `foo, `
                            # Fixes imports of the form `import foo from ...`
                            else:
                                # This converts `import foo` to `import { foo }`
                                usage.match.insert_before("{ ", newline=False)
                                usage.match.insert_after(" }", newline=False)

    @cached_property
    @noapidoc
    @reader
    def _wildcards(self) -> dict[str, WildcardExport[Self]]:
        if self.is_wildcard_export() and isinstance(self.exported_symbol, Import):
            res = {}
            for name, symbol in self.exported_symbol._wildcards.items():
                res[name] = WildcardExport(self, symbol)
            return res
        return {}

    @reader
    @noapidoc
    @override
    def _resolved_types(self) -> Generator[ResolutionStack[Self], None, None]:
        aliased = self.is_aliased()
        if self.exported_symbol is not None:
            yield from self.with_resolution_frame(self.exported_symbol, direct=True, aliased=aliased)
        elif self.value is not None:
            yield from self.with_resolution_frame(self.value, direct=True, aliased=aliased)

    @property
    @noapidoc
    def names(self) -> Generator[tuple[str, Self | WildcardExport[Self]], None, None]:
        if self.exported_name is None:
            if self.is_wildcard_export():
                yield from self._wildcards.items()
        else:
            yield self.exported_name, self

    @property
    def descendant_symbols(self) -> list[Importable]:
        """Returns a list of all descendant symbols from this export's declared symbol.

        Returns all child symbols that are contained within the declared symbol of this export. For example,
        if the declared symbol is a class, this will return all methods, properties and nested classes.
        If the export has no declared symbol, returns an empty list.

        Returns:
            list[Importable]: List of descendant symbols. Empty list if no declared symbol exists.
        """
        if self.declared_symbol:
            return [self, *self.declared_symbol.descendant_symbols]
        return [self]

    def __hash__(self):
        if self._hash is None:
            self._hash = hash((self.filepath, self.range, self.ts_node.kind_id, self.name))
        return self._hash

    @reader
    def __eq__(self, other: object):
        if isinstance(other, TSExport):
            return super().__eq__(other) and self.name == other.name
        return super().__eq__(other)

    @property
    @reader
    def source(self) -> str:
        """Returns the source code of the symbol.

        Gets the source code of the symbol from its extended representation, which includes the export statement.

        Returns:
            str: The complete source code of the symbol including any extended nodes.
        """
        return self.parent.parent.source

    @property
    @reader
    def is_external_export(self) -> bool:
        """Determines if this export is exporting a symbol from an external (non-relative) module.

        An external module is one that comes from outside the project's codebase.

        Returns:
            bool: True if the export is from an external module, False otherwise.
        """
        if self.is_reexport():
            if isinstance(self.exported_symbol, TSImport):
                for resolved in self.exported_symbol.resolved_types:
                    if isinstance(resolved, ExternalModule):
                        return True
        return False

    @reader
    def to_import_string(self) -> str:
        """Converts this export into its equivalent import string representation.

        This is primarily used for handling re-exports, converting them into their
        equivalent import statements.

        Returns:
            str: The import string representation of this export.

        Examples:
            - For `export { foo } from './bar'` -> `import { foo } from './bar'`
            - For `export * from './bar'` -> `import * as _namespace from './bar'`
            - For `export { default as foo } from './bar'` -> `import foo from './bar'`
        """
        module_path = self.exported_symbol.module.source.strip("'\"") if self.exported_symbol.module is not None else ""
        type_prefix = "type " if self.is_type_export() else ""

        if self.is_wildcard_export():
            namespace = self.name or module_path.split("/")[-1].split(".")[0]
            return f"import * as {namespace} from '{module_path}';"

        if self.is_default_export():
            if self.is_type_export() and self.is_aliased():
                original_name = self.exported_symbol.symbol_name.source if self.exported_symbol.symbol_name is not None else self.exported_symbol.name
                print(original_name)
                if original_name == "default":
                    return f"import {type_prefix}{{ default as {self.name} }} from '{module_path}';"
                else:
                    return f"import {type_prefix}{{ {original_name} as default }} from '{module_path}';"

        # Handle mixed type and value exports
        if "type" in self.source and "," in self.source and "{" in self.source and "}" in self.source:
            content = self.source[self.source.index("{") + 1 : self.source.index("}")].strip()
            return f"import {{ {content} }} from '{module_path}';"

        original_name = self.exported_symbol.symbol_name.source if self.exported_symbol.symbol_name is not None else self.exported_symbol.name
        return f"import {{ {original_name} as {self.name} }} from '{module_path}';"

    @reader
    def get_import_string(self, alias: str | None = None, module: str | None = None, import_type: ImportType = ImportType.UNKNOWN, is_type_import: bool = False) -> str:
        """Returns the import string for this export.

        Args:
            alias (str | None): Optional alias to use when importing the symbol.
            module (str | None): Optional module name to import from.
            import_type (ImportType): The type of import to generate.
            is_type_import (bool): Whether this is a type-only import.

        Returns:
            str: The formatted import string.
        """
        if self.is_reexport():
            return self.to_import_string()

        module_path = self.file.import_module_name.strip("'\"")
        type_prefix = "type " if is_type_import else ""

        if import_type == ImportType.WILDCARD:
            namespace = alias or module_path.split("/")[-1].split(".")[0]
            return f"import * as {namespace} from '{module_path}';"

        # Handle default exports
        if self.is_default_export():
            name = alias or self.name
            return f"import {name} from '{module_path}';"

        # Handle named exports
        original_name = self.name
        if alias and alias != original_name:
            return f"import {type_prefix}{{ {original_name} as {alias} }} from '{module_path}';"
        return f"import {type_prefix}{{ {original_name} }} from '{module_path}';"

    @reader
    def reexport_symbol(self) -> TSImport | None:
        """Returns the import object that is re-exporting this symbol.

        For re-exports like:
        - `export { foo } from './bar'`  # Direct re-export
        - `export { default as baz } from './bar'`  # Direct default re-export
        - `export * from './bar'`  # Direct wildcard re-export
        - `import { foo } from './bar'; export { foo }`  # Local re-export

        This returns the corresponding import object that's being re-exported.

        Returns:
            TSImport | None: The import object being re-exported, or None if this
            is not a re-export or no import was found.
        """
        # Only exports can have re-export sources
        if not self.is_reexport():
            return None

        # For direct re-exports (export { x } from './y'), use declared_symbol
        if self.declared_symbol is not None:
            return self.declared_symbol

        # For local re-exports (import x; export { x }), use exported_symbol
        if self.exported_symbol is not None and self.exported_symbol.node_type == NodeType.IMPORT:
            return self.exported_symbol

        return None


TExport = TypeVar("TExport", bound="Export")


class WildcardExport(Chainable, Generic[TExport]):
    """Class to represent one of many wildcard exports."""

    exp: TExport
    symbol: Exportable

    def __init__(self, exp: TExport, symbol: Exportable):
        self.exp = exp
        self.symbol = symbol

    @reader
    @noapidoc
    @override
    def _resolved_types(self) -> Generator[ResolutionStack[Self], None, None]:
        """Resolve the types used by this import."""
        yield from self.exp.with_resolution_frame(self.symbol, direct=False)

    @noapidoc
    @reader
    def _compute_dependencies(self, usage_type: UsageKind, dest: HasName | None = None) -> None:
        pass
