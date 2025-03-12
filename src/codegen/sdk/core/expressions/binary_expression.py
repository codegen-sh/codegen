import itertools
from collections import deque
from collections.abc import Generator
from functools import cached_property
from typing import Generic, Self, TypeVar, override

from codegen.sdk.codebase.resolution_stack import ResolutionStack
from codegen.sdk.core.autocommit import writer
from codegen.sdk.core.dataclasses.usage import UsageKind
from codegen.sdk.core.expressions import Expression
from codegen.sdk.core.interfaces.chainable import Chainable
from codegen.sdk.core.interfaces.editable import Editable
from codegen.sdk.core.interfaces.has_name import HasName
from codegen.sdk.core.interfaces.importable import Importable
from codegen.sdk.core.interfaces.unwrappable import Unwrappable
from codegen.sdk.core.symbol_groups.expression_group import ExpressionGroup
from codegen.sdk.extensions.autocommit import commiter, reader
from codegen.sdk.extensions.sort import sort_editables
from codegen.shared.decorators.docs import apidoc, noapidoc

Parent = TypeVar("Parent", bound="Editable")


@apidoc
class BinaryExpression(Expression[Parent], Chainable, Generic[Parent]):
    """Represents binary expressions, e.g. all of +,-,*,/, as well as boolean operations (and, or) etc.

    Attributes:
        left: The left operand of the binary expression.
        right: The right operand of the binary expression.
    """

    left: Expression[Self] | None
    right: Expression[Self] | None

    def __init__(self, ts_node, file_node_id, ctx, parent: Parent) -> None:
        super().__init__(ts_node, file_node_id, ctx, parent=parent)
        self.left = self.child_by_field_name("left")
        self.right = self.child_by_field_name("right")

    @property
    @noapidoc
    def operator(self) -> ExpressionGroup[Expression[Self], Self]:
        """Returns the operator of the binary expression."""
        operator_nodes = self.ts_node.children[1:-1]
        return ExpressionGroup(self.file_node_id, self.ctx, self, children=[self._parse_expression(node) for node in operator_nodes])

    @property
    def operators(self) -> list[ExpressionGroup[Expression[Self], Self]]:
        """Returns a list of operators in a chain of binary operations.

        Returns all operators found in a chain of binary operations, maintaining the order in which they appear. For example,
        in the expression "a + b - c * d / e", it would return the operators [+, -, *, /] in that order.

        Returns:
            list[ExpressionGroup[Expression[Self], Self]]: The list of operators in the binary expression chain, ordered as they appear in the code.
        """
        operators = [self.operator]
        nodes_to_process = deque([self.left, self.right])
        while nodes_to_process:
            node = nodes_to_process.popleft()
            if isinstance(node, BinaryExpression):
                operators.append(node.operator)
                nodes_to_process.extend([node.left, node.right])
        return sort_editables(operators, dedupe=False)

    @cached_property
    def elements(self) -> list[Expression[Self]]:
        """Returns all elements in a binary expression chain.

        Retrieves all elements that appear in a chain of binary operations in the expression,
        traversing through nested binary expressions to extract individual elements.

        Args:
            None

        Returns:
            list[Expression[Self]]: A sorted list of non-binary expression elements in the chain.
            For example, in the expression 'a + b - c * d / e', returns [a, b, c, d, e] in order.
        """
        elements = []
        nodes_to_process = deque([self.left, self.right])
        while nodes_to_process:
            node = nodes_to_process.popleft()
            if isinstance(node, BinaryExpression):
                nodes_to_process.extend([node.left, node.right])
            else:
                elements.append(node)
        return sort_editables(elements, dedupe=False)

    @reader
    @noapidoc
    @override
    def _resolved_types(self) -> Generator[ResolutionStack[Self], None, None]:
        for e in self.elements:
            yield from self.with_resolution_frame(e)

    @property
    @noapidoc
    def descendant_symbols(self) -> list[Importable]:
        return list(itertools.chain.from_iterable(elem.descendant_symbols for elem in self.elements))

    @noapidoc
    @commiter
    def _compute_dependencies(self, usage_type: UsageKind | None = None, dest: HasName | None = None) -> None:
        self.left._compute_dependencies(usage_type, dest)
        self.right._compute_dependencies(usage_type, dest)

    @writer
    def reduce_condition(self, bool_condition: bool, node: Editable) -> None:
        """Simplifies a binary expression by reducing it based on a boolean condition.


        Args:
            bool_condition (bool): The boolean value to reduce the condition to.

        """
        reduce_operator = False
        if "and" in self.operator or "&&" in self.operator:
            reduce_operator = not bool_condition
            # We can inline the entire operator if the condition if False.
            # a and b evaluates to False if either a or b is False
        elif "or" in self.operator or "||" in self.operator:
            reduce_operator = bool_condition  # We can inline the entire operator if the condition is True
            # a or b evaluates to True if either a or b is True
        if reduce_operator:
            self.parent.reduce_condition(bool_condition, self)
        else:
            node.remove()
            if isinstance(self.parent, Unwrappable):
                other_node = self.left if node == self.right else self.right
                self.parent.unwrap(other_node)
