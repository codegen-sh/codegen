from __future__ import annotations

from typing import TYPE_CHECKING, Generic, Self, TypeVar

from codegen.sdk.core.dataclasses.usage import UsageKind
from codegen.sdk.core.statements.statement import Statement, StatementType
from codegen.sdk.core.symbol_groups.collection import Collection
from codegen.sdk.extensions.autocommit import commiter
from codegen.sdk.typescript.export import TSExport
from codegen.sdk.typescript.statements.import_statement import TSImportStatement
from codegen.sdk.utils import find_first_ancestor
from codegen.shared.decorators.docs import apidoc, noapidoc

if TYPE_CHECKING:
    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.export import Export
    from codegen.sdk.core.interfaces.has_name import HasName
    from codegen.sdk.core.node_id_factory import NodeId
    from codegen.sdk.typescript.detached_symbols.code_block import TSCodeBlock

TExport = TypeVar("TExport", bound="Export")


@apidoc
class ExportStatement(Statement["TSCodeBlock"], Generic[TExport]):
    """Abstract representation of a single export statement that appears in a file. One export
    statement can export multiple symbols from a single source.

    Attributes:
        exports: A list of the individual exports this statement represents
    """

    exports: Collection[TExport, Self]
    statement_type = StatementType.EXPORT_STATEMENT

    def __init__(self, ts_node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: TSCodeBlock, pos: int):
        super().__init__(ts_node, parent.file_node_id, parent.ctx, parent, pos)
        export_node = self.ts_node
        if node := self.child_by_field_types(["export_clause", "export_statement"]):
            export_node = node.ts_node
        self.exports = Collection(export_node, self.file_node_id, self.ctx, self, bracket_size=2)
        if declaration := ts_node.child_by_field_name("declaration"):
            exports = TSExport.from_export_statement_with_declaration(ts_node, declaration, file_node_id, ctx, self, pos)
        elif value := ts_node.child_by_field_name("value"):
            exports = TSExport.from_export_statement_with_value(self.ts_node, value, self.file_node_id, self.ctx, self, self.index)
        else:
            exports = []
            if source_node := ts_node.child_by_field_name("source"):
                # ==== [ Re-export ] ====
                # e.g. export { name1, name2 } from './other-module';
                import_statement = TSImportStatement(ts_node, file_node_id, ctx, parent, pos, source_node=source_node)
                for imp in import_statement.imports:
                    name_node = imp.alias.ts_node if imp.alias else None
                    export = TSExport(
                        ts_node=find_first_ancestor(imp._name_node.ts_node, ["export_statement", "export_clause", "export_specifier"]) if imp._name_node else imp.ts_node,
                        file_node_id=file_node_id,
                        ctx=ctx,
                        name_node=name_node,
                        declared_symbol=imp,
                        parent=self.exports,
                    )
                    exports.append(export)
            elif export_clause := next((child for child in ts_node.named_children if child.type == "export_clause"), None):
                export_node = export_clause
                # ==== [ Named export ] ====
                # e.g. export { variable, functionName, ClassName };
                for export_specifier in export_clause.named_children:
                    if export_specifier.type == "comment":
                        continue
                    name_node = export_specifier.child_by_field_name("name")
                    alias_node = export_specifier.child_by_field_name("alias") or name_node
                    export = TSExport(ts_node=export_specifier, file_node_id=file_node_id, ctx=ctx, name_node=alias_node, exported_symbol=name_node, parent=self.exports)
                    exports.append(export)
            else:
                # ==== [ Export assignment ] ====
                # Examples: `export = XYZ;`, `export = function foo() {}`, `export = function() {}`, `export = { f1, f2 }`
                # No other named exports can exist alongside this type of export in the file
                exports.extend(TSExport.from_export_statement_with_value(self.ts_node, ts_node.named_children[0], self.file_node_id, self.ctx, self, self.index))
        self.exports._init_children(exports)
        for exp in self.exports:
            exp.export_statement = self

    @noapidoc
    @commiter
    def _compute_dependencies(self, usage_type: UsageKind = UsageKind.BODY, dest: HasName | None = None) -> None:
        # We compute export dependencies separately
        pass

    def _removed_child(self) -> None:
        self.exports._removed_child()

    def _removed_child_commit(self) -> None:
        self.exports._removed_child_commit()

    @property
    def reexports(self) -> list[TSExport]:
        """Retrieves a list of re-exported symbols from this export statement.

        Returns:
            list[TSExport]: A list of re-exported symbols within the current export context,
                           excluding external exports.
        """
        reexports = []
        for export in self.exports:
            if export.is_reexport() and not export.is_external_export:
                reexports.append(export)
        return reexports

    def _smart_remove(self, child, *args, **kwargs) -> bool:
        if self.exports.uncommitted_len == 1 and child.ts_node.is_named:
            self.remove()
            return True
        return super()._smart_remove(child, *args, **kwargs)
