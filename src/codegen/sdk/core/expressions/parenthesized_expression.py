from typing import Generic, TypeVar, override

from codegen.sdk.codebase.transactions import TransactionPriority
from codegen.sdk.core.autocommit import writer
from codegen.sdk.core.detached_symbols.function_call import FunctionCall
from codegen.sdk.core.expressions import Expression
from codegen.sdk.core.interfaces.editable import Editable
from codegen.sdk.core.interfaces.has_value import HasValue
from codegen.sdk.core.interfaces.unwrappable import Unwrappable
from codegen.sdk.core.interfaces.wrapper_expression import IWrapper
from codegen.sdk.extensions.autocommit import reader
from codegen.sdk.typescript.statements.if_block_statement import TSIfBlockStatement
from codegen.shared.decorators.docs import apidoc

Parent = TypeVar("Parent", bound="Editable")


@apidoc
class ParenthesizedExpression(Unwrappable[Parent], HasValue, IWrapper, Generic[Parent]):
    """An expression surrounded in a set of parenthesis.

    Example:
        ```typescript
        (5 + 5)
        ```
    """

    def __init__(self, ts_node, file_node_id, ctx, parent: Parent):
        super().__init__(ts_node, file_node_id, ctx, parent=parent)
        value_node = self.ts_node.named_children[0]
        self._value_node = self.ctx.parser.parse_expression(value_node, self.file_node_id, self.ctx, self) if value_node else None

    @property
    @reader
    def function_calls(self) -> list[FunctionCall]:
        """Retrieves a list of function calls within a parenthesized expression.

        Gets all function calls from the resolved value of this parenthesized expression.

        Returns:
            list[FunctionCall]: A list of FunctionCall objects representing all function calls within the parenthesized expression.
        """
        return self.resolve().function_calls

    @writer
    @override
    def unwrap(self, node: Expression | None = None) -> None:
        """Removes the parentheses from a parenthesized expression node.

        Modifies the AST by removing the parentheses from a ParenthesizedExpression node, leaving only the inner expression.

        Args:
            node (Expression | None, optional): The node to unwrap. Defaults to None.

        Returns:
            None
        """
        if isinstance(self.parent, TSIfBlockStatement):
            return
        if node is None:
            remaining = list(
                child
                for child in self.value.children
                if not self.transaction_manager.get_transactions_at_range(self.file.path, start_byte=child.start_byte, end_byte=child.end_byte, transaction_order=TransactionPriority.Remove)
            )
            if len(remaining) == 1:
                node = remaining[0]
            else:
                return
        if node.start_point[0] == node.end_point[0]:
            for child in self._anonymous_children:
                child.remove()
            if isinstance(self.parent, Unwrappable):
                self.parent.unwrap(node)

    @writer
    def reduce_condition(self, bool_condition: bool, node: Editable) -> None:
        """Simplifies an expression based on a boolean condition.

        Args:
            bool_condition (bool): The boolean value to reduce the condition to.
            node (Editable): The node to be simplified.

        Returns:
            None
        """
        self.unwrap()
        self.parent.reduce_condition(bool_condition, self)
