from functools import cached_property
from typing import Self, TypeVar

from codegen.sdk.core.expressions import Expression
from codegen.sdk.core.expressions.binary_expression import BinaryExpression
from codegen.sdk.core.symbol_groups.expression_group import ExpressionGroup
from codegen.shared.decorators.docs import apidoc

Parent = TypeVar("Parent")


@apidoc
class ComparisonExpression(BinaryExpression):
    """Any comparison expression in the code.

    Includes all set of `<`, `<=`, `>`, `>=`, `==`, `!=` etc.
    """

    def __init__(self, ts_node, file_node_id, ctx, parent: Parent) -> None:
        super().__init__(ts_node, file_node_id, ctx, parent=parent)
        self.left = self.elements[0]
        self.right = self.elements[-1]

    @property
    def operators(self) -> list[ExpressionGroup[Expression[Self], Self]]:
        """Returns a list of operator expressions in a comparison expression.

        Extracts and groups the non-named operators (e.g., <, <=, >, >=, ==, !=) from the
        comparison expression's tree-sitter node. Each group of operators is wrapped in an
        ExpressionGroup.

        Returns:
            list[ExpressionGroup[Expression[Self], Self]]: A list of ExpressionGroups
            containing one or more expression operators that appear between the compared
            elements.
        """
        elements = set(self.ts_node.named_children)
        operators = []
        operator_group = []
        for n in self.ts_node.children:
            if n not in elements:
                operator_group.append(n)
            elif operator_group:
                operator = ExpressionGroup(self.file_node_id, self.ctx, self, children=[self._parse_expression(op) for op in operator_group])
                operators.append(operator)
                operator_group.clear()
        return operators

    @cached_property
    def elements(self) -> list[Expression[Self]]:
        """Returns a list of expressions for named child nodes.

        Args:
            None

        Returns:
            list[Expression[Self]]: A list of Expression objects for each named child node.
        """
        return [self._parse_expression(node) for node in self.ts_node.named_children]
