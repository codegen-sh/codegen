from __future__ import annotations

from typing import TYPE_CHECKING

from codegen.sdk.core.statements.catch_statement import CatchStatement
from codegen.sdk.python.detached_symbols.code_block import PyCodeBlock
from codegen.sdk.python.statements.block_statement import PyBlockStatement
from codegen.shared.decorators.docs import noapidoc, py_apidoc

if TYPE_CHECKING:
    from tree_sitter import Node as PyNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.interfaces.conditional_block import ConditionalBlock
    from codegen.sdk.core.node_id_factory import NodeId


@py_apidoc
class PyCatchStatement(CatchStatement[PyCodeBlock], PyBlockStatement):
    """Python catch clause.

    Attributes:
        code_block: The code block that may trigger an exception
        condition: The condition which triggers this clause
    """

    def __init__(self, ts_node: PyNode, file_node_id: NodeId, ctx: CodebaseContext, parent: PyCodeBlock, pos: int | None = None) -> None:
        super().__init__(ts_node, file_node_id, ctx, parent, pos)
        self.condition = self.children[0]

    @property
    @noapidoc
    def other_possible_blocks(self) -> list[ConditionalBlock]:
        return [clause for clause in self.parent.except_clauses if clause != self] + [self.parent]
