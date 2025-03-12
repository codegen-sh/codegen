from typing import TYPE_CHECKING

from tree_sitter import Node as TSNode

from codegen.sdk.core.node_id_factory import NodeId
from codegen.sdk.core.statements.switch_case import SwitchCase
from codegen.sdk.typescript.detached_symbols.code_block import TSCodeBlock
from codegen.sdk.typescript.statements.block_statement import TSBlockStatement
from codegen.shared.decorators.docs import ts_apidoc

if TYPE_CHECKING:
    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.typescript.statements.switch_statement import TSSwitchStatement


@ts_apidoc
class TSSwitchCase(SwitchCase[TSCodeBlock["TSSwitchStatement"]], TSBlockStatement):
    """Typescript switch case.

    Attributes:
        default: is this a default case?
    """

    default: bool

    def __init__(self, ts_node: TSNode, file_node_id: NodeId, ctx: "CodebaseContext", parent: TSCodeBlock, pos: int | None = None) -> None:
        super().__init__(ts_node, file_node_id, ctx, parent, pos)
        self.condition = self.child_by_field_name("value")
        self.default = self.ts_node.type == "switch_default"
