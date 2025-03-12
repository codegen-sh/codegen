from typing import TYPE_CHECKING

from tree_sitter import Node as PyNode

from codegen.sdk.core.node_id_factory import NodeId
from codegen.sdk.core.statements.switch_case import SwitchCase
from codegen.sdk.python.detached_symbols.code_block import PyCodeBlock
from codegen.sdk.python.statements.block_statement import PyBlockStatement
from codegen.shared.decorators.docs import noapidoc, py_apidoc

if TYPE_CHECKING:
    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.interfaces.conditional_block import ConditionalBlock
    from codegen.sdk.python.statements.match_statement import PyMatchStatement


@py_apidoc
class PyMatchCase(SwitchCase[PyCodeBlock["PyMatchStatement"]], PyBlockStatement):
    """Python match case."""

    def __init__(self, ts_node: PyNode, file_node_id: NodeId, ctx: "CodebaseContext", parent: PyCodeBlock, pos: int | None = None) -> None:
        super().__init__(ts_node, file_node_id, ctx, parent, pos)
        self.condition = self.child_by_field_name("alternative")

    @property
    @noapidoc
    def other_possible_blocks(self) -> list["ConditionalBlock"]:
        return [case for case in self.parent.cases if case != self]
