from typing import TYPE_CHECKING, Generic, TypeVar

from codegen.sdk.core.detached_symbols.function_call import FunctionCall
from codegen.sdk.core.expressions import Expression
from codegen.sdk.core.interfaces.has_value import HasValue
from codegen.sdk.core.interfaces.wrapper_expression import IWrapper
from codegen.sdk.extensions.autocommit import reader
from codegen.shared.decorators.docs import apidoc

if TYPE_CHECKING:
    from codegen.sdk.core.interfaces.editable import Editable

Parent = TypeVar("Parent", bound="Editable")


@apidoc
class AwaitExpression(Expression[Parent], HasValue, IWrapper, Generic[Parent]):
    """An awaited expression, only found in asynchronous contexts, e.g. await(foo(bar))"""

    def __init__(self, ts_node, file_node_id, ctx, parent: Parent):
        super().__init__(ts_node, file_node_id, ctx, parent=parent)
        value_node = self.ts_node.named_children[0]
        self._value_node = self.ctx.parser.parse_expression(value_node, self.file_node_id, self.ctx, parent) if value_node else None

    @property
    @reader
    def function_calls(self) -> list[FunctionCall]:
        """Gets all function calls within the await expression.

        Returns:
            list[FunctionCall]: A list of function call nodes contained within the await expression's value.
        """
        return self.resolve().function_calls
