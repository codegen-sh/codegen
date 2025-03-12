from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

from codegen.sdk.core.dataclasses.usage import UsageKind
from codegen.sdk.core.expressions.name import Name
from codegen.sdk.core.interfaces.has_value import HasValue
from codegen.sdk.core.statements.statement import Statement, StatementType
from codegen.sdk.extensions.autocommit import commiter
from codegen.shared.decorators.docs import apidoc, noapidoc

if TYPE_CHECKING:
    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.assignment import Assignment
    from codegen.sdk.core.detached_symbols.code_block import CodeBlock
    from codegen.sdk.core.expressions import Expression
    from codegen.sdk.core.expressions.multi_expression import MultiExpression
    from codegen.sdk.core.interfaces.has_block import HasBlock
    from codegen.sdk.core.interfaces.has_name import HasName
    from codegen.sdk.core.interfaces.importable import Importable
    from codegen.sdk.core.node_id_factory import NodeId


TCodeBlock = TypeVar("TCodeBlock", bound="CodeBlock")
TAssignment = TypeVar("TAssignment", bound="Assignment")


@apidoc
class AssignmentStatement(Statement[TCodeBlock], HasValue, Generic[TCodeBlock, TAssignment]):
    """A class that represents an assignment statement in a codebase, such as `x = 1`, `a, b = 1, 2`, `const {a: b} = myFunc(),`, etc.

    This includes potentially multiple Assignments via `statement.assignments`, which represent each assignment of a value to a variable within this statement.

    For example, assigning to a destructured object, or assigning multiple values to multiple variables in a single statement.

    Attributes:
        assignments: A list of assignments within the statement.
        left: The left-hand side expression of the first assignment.
        right: The right-hand side expression of the first assignment, or None if not applicable.
    """

    statement_type = StatementType.ASSIGNMENT
    assignments: list[TAssignment]
    left: Expression[TAssignment]
    right: Expression[TAssignment] | None

    def __init__(self, ts_node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: TCodeBlock, pos: int, assignment_node: TSNode) -> None:
        super().__init__(ts_node, file_node_id, ctx, parent, pos=pos)
        self.assignments = self._DEPRECATED_parse_assignments().expressions
        if len(self.assignments) == 0:
            msg = f"No assignments found: {self.ts_node}\n\n{self.source}"
            raise ValueError(msg)

        first_assignment: TAssignment = self.assignments[0]
        self._name_node = self.ctx.parser.parse_expression(first_assignment.ts_node, self.file_node_id, self.ctx, parent, default=Name)
        self.left = first_assignment.left
        self.right = first_assignment.value
        self._value_node = self.right

    @abstractmethod
    def _parse_assignments(self, ts_node: TSNode) -> MultiExpression[HasBlock, TAssignment]: ...

    @abstractmethod
    def _DEPRECATED_parse_assignments(self) -> MultiExpression[HasBlock, TAssignment]: ...

    @noapidoc
    @commiter
    def _compute_dependencies(self, usage_type: UsageKind = UsageKind.BODY, dest: HasName | None = None) -> None:
        # We compute assignment dependencies separately
        pass

    @property
    @noapidoc
    def descendant_symbols(self) -> list[Importable]:
        """Returns the nested symbols of the importable object."""
        symbols = []
        for assignment in self.assignments:
            symbols.extend(assignment.descendant_symbols)
        return symbols
