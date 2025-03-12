from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from codegen.sdk.core.autocommit import commiter, reader
from codegen.sdk.core.dataclasses.usage import UsageKind
from codegen.sdk.core.interface import Interface
from codegen.sdk.core.symbol_groups.parents import Parents
from codegen.sdk.typescript.detached_symbols.code_block import TSCodeBlock
from codegen.sdk.typescript.expressions.type import TSType
from codegen.sdk.typescript.function import TSFunction
from codegen.sdk.typescript.interfaces.has_block import TSHasBlock
from codegen.sdk.typescript.statements.attribute import TSAttribute
from codegen.sdk.typescript.symbol import TSSymbol
from codegen.shared.decorators.docs import noapidoc, ts_apidoc

if TYPE_CHECKING:
    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.detached_symbols.code_block import CodeBlock
    from codegen.sdk.core.interfaces.has_name import HasName
    from codegen.sdk.core.node_id_factory import NodeId
    from codegen.sdk.core.statements.statement import Statement

Parent = TypeVar("Parent", bound="TSHasBlock")


@ts_apidoc
class TSInterface(Interface[TSCodeBlock, TSAttribute, TSFunction, TSType], TSSymbol, TSHasBlock):
    """Representation of an Interface in TypeScript

    Attributes:
        parent_interfaces: All the interfaces that this interface extends.
        code_block: The code block that contains the interface's body.
    """

    def __init__(
        self,
        ts_node: TSNode,
        file_id: NodeId,
        ctx: CodebaseContext,
        parent: Statement[CodeBlock[Parent, ...]],
    ) -> None:
        from codegen.sdk.typescript.detached_symbols.code_block import TSCodeBlock

        super().__init__(ts_node, file_id, ctx, parent)
        body_node = ts_node.child_by_field_name("body")

        # Find the nearest parent with a code_block
        current_parent = parent
        while not hasattr(current_parent, "code_block"):
            current_parent = current_parent.parent

        self.code_block = TSCodeBlock(body_node, current_parent.code_block.level + 1, current_parent.code_block, self)
        self.code_block.parse()

    @commiter
    @noapidoc
    def parse(self, ctx: CodebaseContext) -> None:
        # =====[ Extends ]=====
        # Look for parent interfaces in the "extends" clause
        if extends_clause := self.child_by_field_types("extends_type_clause"):
            self.parent_interfaces = Parents(extends_clause.ts_node, self.file_node_id, self.ctx, self)
        super().parse(ctx)

    @noapidoc
    @commiter
    def _compute_dependencies(self, usage_type: UsageKind | None = None, dest: HasName | None = None) -> None:
        dest = dest or self.self_dest

        # =====[ Extends ]=====
        if self.parent_interfaces is not None:
            self.parent_interfaces._compute_dependencies(UsageKind.SUBCLASS, dest)

        # =====[ Body ]=====
        # Look for type references in the interface body
        self.code_block._compute_dependencies(usage_type, dest)

    @staticmethod
    @noapidoc
    def _get_name_node(ts_node: TSNode) -> TSNode | None:
        if ts_node.type == "interface_declaration":
            return ts_node.child_by_field_name("name")
        return None

    @property
    @reader
    def attributes(self) -> list[TSAttribute]:
        """Retrieves the list of attributes defined in the TypeScript interface.

        Args:
            None

        Returns:
            list[TSAttribute]: A list of the interface's attributes stored in the code block.
        """
        return self.code_block.attributes
