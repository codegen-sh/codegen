from typing import TYPE_CHECKING, TypeVar

from tree_sitter import Node as TSNode

from codegen.sdk.core.expressions.builtin import Builtin
from codegen.sdk.core.expressions.expression import Expression
from codegen.sdk.core.interfaces.editable import Editable
from codegen.sdk.core.node_id_factory import NodeId
from codegen.sdk.core.symbol_groups.collection import Collection
from codegen.shared.decorators.docs import apidoc

if TYPE_CHECKING:
    from codegen.sdk.codebase.codebase_context import CodebaseContext
Parent = TypeVar("Parent", bound=Editable)


@apidoc
class Tuple(Collection["Expression[Self, None]", Parent], Expression[Parent], Builtin):
    """A tuple object.

    You can use standard operations to operate on this list (IE len, del, append, insert, etc)
    """

    def __init__(self, ts_node: TSNode, file_node_id: NodeId, ctx: "CodebaseContext", parent: Parent) -> None:
        super().__init__(ts_node, file_node_id, ctx, parent)
        self._init_children([self._parse_expression(child) for child in ts_node.named_children if child.type])

    @property
    def __class__(self):
        return tuple
