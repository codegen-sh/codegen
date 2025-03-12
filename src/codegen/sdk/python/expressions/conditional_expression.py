from typing import TYPE_CHECKING, TypeVar

from codegen.sdk.core.expressions.ternary_expression import TernaryExpression
from codegen.shared.decorators.docs import py_apidoc

if TYPE_CHECKING:
    from codegen.sdk.core.interfaces.editable import Editable

Parent = TypeVar("Parent", bound="Editable")


@py_apidoc
class PyConditionalExpression(TernaryExpression[Parent]):
    """Conditional Expressions (A if condition else B)"""

    def __init__(self, ts_node, file_node_id, ctx, parent: Parent) -> None:
        super().__init__(ts_node, file_node_id, ctx, parent=parent)
        self.consequence = self.children[0]
        self.condition = self.children[1]
        self.alternative = self.children[2]
