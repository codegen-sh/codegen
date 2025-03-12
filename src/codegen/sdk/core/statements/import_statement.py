from __future__ import annotations

from typing import TYPE_CHECKING, Generic, Self, TypeVar

from codegen.sdk.core.dataclasses.usage import UsageKind
from codegen.sdk.core.statements.statement import Statement
from codegen.sdk.extensions.autocommit import commiter
from codegen.shared.decorators.docs import apidoc, noapidoc

if TYPE_CHECKING:
    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.detached_symbols.code_block import CodeBlock
    from codegen.sdk.core.file import SourceFile
    from codegen.sdk.core.import_resolution import Import
    from codegen.sdk.core.interfaces.has_name import HasName
    from codegen.sdk.core.node_id_factory import NodeId
    from codegen.sdk.core.symbol_groups.collection import Collection


TSourceFile = TypeVar("TSourceFile", bound="SourceFile")
TImport = TypeVar("TImport", bound="Import")
TCodeBlock = TypeVar("TCodeBlock", bound="CodeBlock")


@apidoc
class ImportStatement(Statement[TCodeBlock], Generic[TSourceFile, TImport, TCodeBlock]):
    """Abstract representation of a single import statement that appears in a file. One import
    statement can import multiple symbols from a single source.

    Attributes:
        imports: A collection of the individual imports this statement represents
    """

    imports: Collection[TImport, Self]

    def __init__(self, ts_node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: TCodeBlock, pos: int) -> None:
        super().__init__(ts_node, file_node_id, ctx, parent, pos)

    @noapidoc
    @commiter
    def _compute_dependencies(self, usage_type: UsageKind = UsageKind.BODY, dest: HasName | None = None) -> None:
        # Skip computing dependencies for import statements, since it is done during import resolution step
        pass

    def _smart_remove(self, child, *args, **kwargs) -> bool:
        if self.imports.uncommitted_len == 1 and child.ts_node.is_named:
            self.remove()
            return True
        return super()._smart_remove(child, *args, **kwargs)
