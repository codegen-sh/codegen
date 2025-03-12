from __future__ import annotations

from typing import TYPE_CHECKING

from codegen.sdk.core.expressions.multi_expression import MultiExpression
from codegen.sdk.core.statements.assignment_statement import AssignmentStatement
from codegen.sdk.extensions.utils import find_all_descendants
from codegen.sdk.python.assignment import PyAssignment
from codegen.shared.decorators.docs import py_apidoc
from codegen.shared.logging.get_logger import get_logger

if TYPE_CHECKING:
    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.node_id_factory import NodeId
    from codegen.sdk.python.detached_symbols.code_block import PyCodeBlock
    from codegen.sdk.python.interfaces.has_block import PyHasBlock


logger = get_logger(__name__)


@py_apidoc
class PyAssignmentStatement(AssignmentStatement["PyCodeBlock", PyAssignment]):
    """A class that represents a Python assignment statement in a codebase, such as `x = 1` or `a, b = 1, 2`.

    This includes potentially multiple Assignments via `statement.assignments`, which represent each assignment of a value to a variable within this statement.
    """

    assignment_types = {"assignment", "augmented_assignment", "named_expression"}

    def __init__(self, ts_node, file_node_id, ctx, parent, pos, assignment_node):
        super().__init__(ts_node, file_node_id, ctx, parent, pos, assignment_node)
        self._values_scheduled_for_removal = []

    @classmethod
    def from_assignment(cls, ts_node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: PyCodeBlock, pos: int, assignment_node: TSNode) -> PyAssignmentStatement:
        """Creates a PyAssignmentStatement instance from a TreeSitter assignment node.

        Factory method to create appropriate assignment statement objects based on the node type and parent context.
        If the parent is a PyClass, creates a PyAttribute, otherwise creates a PyAssignmentStatement.

        Args:
            ts_node (TSNode): The TreeSitter node representing the entire statement.
            file_node_id (NodeId): The ID of the file containing this node.
            ctx (CodebaseContext): The codebase context instance.
            parent (PyHasBlock): The parent block containing this statement.
            code_block (PyCodeBlock): The code block containing this statement.
            pos (int): The position of this statement within its code block.
            assignment_node (TSNode): The TreeSitter node representing the assignment operation.

        Returns:
            PyAssignmentStatement: A new assignment statement instance, either PyAttribute or PyAssignmentStatement.

        Raises:
            ValueError: If the assignment_node type is not one of the supported assignment types.
        """
        if assignment_node.type not in cls.assignment_types:
            msg = f"Invalid assignment node type: {assignment_node.type}"
            raise ValueError(msg)

        from codegen.sdk.python.class_definition import PyClass

        if isinstance(parent, PyClass):
            from codegen.sdk.python.statements.attribute import PyAttribute

            return PyAttribute(ts_node, file_node_id, ctx, parent, pos, assignment_node=assignment_node)
        return cls(ts_node, file_node_id, ctx, parent, pos, assignment_node=assignment_node)

    def _parse_assignments(self, assignment_node: TSNode) -> MultiExpression[PyHasBlock, PyAssignment]:
        if assignment_node.type in ["assignment", "augmented_assignment"]:
            return PyAssignment.from_assignment(assignment_node, self.file_node_id, self.ctx, self.parent)
        elif assignment_node.type == "named_expression":
            return PyAssignment.from_named_expression(assignment_node, self.file_node_id, self.ctx, self.parent)

        logger.info(f"Unknown assignment type: {assignment_node.type}")
        return MultiExpression(assignment_node, self.file_node_id, self.ctx, self.parent, [self.parent._parse_expression(assignment_node)])

    def _DEPRECATED_parse_assignments(self) -> MultiExpression[PyHasBlock, PyAssignment]:
        assignments = []
        for assignment in find_all_descendants(self.ts_node, {"assignment", "augmented_assignment"}, max_depth=5):
            left = assignment.child_by_field_name("left")
            right = assignment.child_by_field_name("right")
            if left.type == "pattern_list":
                for identifier in find_all_descendants(left, {"identifier", "attribute"}):
                    assignments.append(PyAssignment(assignment, self.file_node_id, self.ctx, self, left, right, identifier))
            else:
                assignments.append(PyAssignment(assignment, self.file_node_id, self.ctx, self, left, right, left))

        return MultiExpression(self.ts_node, self.file_node_id, self.ctx, self.parent, assignments)
