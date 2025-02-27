from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING, Self

from codegen.sdk.core.expressions.multi_expression import MultiExpression
from codegen.sdk.core.statements.assignment_statement import AssignmentStatement
from codegen.sdk.extensions.autocommit import reader
from codegen.sdk.typescript.assignment import TSAssignment
from codegen.shared.decorators.docs import noapidoc, ts_apidoc
from codegen.shared.logging.get_logger import get_logger

if TYPE_CHECKING:
    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.node_id_factory import NodeId
    from codegen.sdk.typescript.detached_symbols.code_block import TSCodeBlock
    from codegen.sdk.typescript.interfaces.has_block import TSHasBlock


logger = get_logger(__name__)


@ts_apidoc
class TSAssignmentStatement(AssignmentStatement["TSCodeBlock", TSAssignment]):
    """A class that represents a TypeScript assignment statement in a codebase, such as `const x = 1` or `const { a: b } = myFunc()`."""

    assignment_types = {"assignment_expression", "augmented_assignment_expression", "variable_declarator", "public_field_definition", "property_signature"}

    @classmethod
    @reader
    @noapidoc
    def from_assignment(cls, ts_node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: TSCodeBlock, pos: int, assignment_node: TSNode) -> TSAssignmentStatement:
        """Creates an assignment statement node from a TreeSitter assignment node.

        This class method constructs a TSAssignmentStatement from a TreeSitter node representing an assignment. The method validates that the assignment node type is
        one of the supported types: assignment_expression, augmented_assignment_expression, variable_declarator, public_field_definition, or property_signature.

        Args:
            ts_node (TSNode): The TreeSitter node representing the entire statement.
            file_node_id (NodeId): The identifier for the file containing this node.
            ctx (CodebaseContext): The codebase context being constructed.
            parent (TSHasBlock): The parent block containing this statement.
            code_block (TSCodeBlock): The code block containing this statement.
            pos (int): The position of this statement within its code block.
            assignment_node (TSNode): The TreeSitter node representing the assignment.

        Returns:
            TSAssignmentStatement: A new assignment statement node.

        Raises:
            ValueError: If the assignment_node.type is not one of the supported assignment types.
        """
        if assignment_node.type not in cls.assignment_types:
            msg = f"Invalid assignment node type: {assignment_node.type}"
            raise ValueError(msg)

        return cls(ts_node, file_node_id, ctx, parent, pos, assignment_node=assignment_node)

    def _parse_assignments(self, assignment_node: TSNode) -> MultiExpression[Self, TSAssignment]:
        if assignment_node.type in ["assignment_expression", "augmented_assignment_expression"]:
            return TSAssignment.from_assignment(assignment_node, self.file_node_id, self.ctx, self)
        elif assignment_node.type in ["variable_declarator", "public_field_definition", "property_signature"]:
            return TSAssignment.from_named_expression(assignment_node, self.file_node_id, self.ctx, self)

        logger.info(f"Unknown assignment type: {assignment_node.type}")
        return MultiExpression(assignment_node, self.file_node_id, self.ctx, self.parent, [self.parent._parse_expression(assignment_node)])

    def _DEPRECATED_parse_assignments(self) -> MultiExpression[TSHasBlock, TSAssignment]:
        if self.ts_node.type in ["lexical_declaration", "variable_declaration"]:
            return MultiExpression(self.ts_node, self.file_node_id, self.ctx, self.parent, self._DEPRECATED_parse_assignment_declarations())
        elif self.ts_node.type in ["expression_statement"]:
            return MultiExpression(self.ts_node, self.file_node_id, self.ctx, self.parent, self._DEPRECATED_parse_assignment_expression())
        elif self.ts_node.type in ["public_field_definition", "property_signature", "enum_assignment"]:
            return MultiExpression(self.ts_node, self.file_node_id, self.ctx, self.parent, self._DEPRECATED_parse_attribute_assignments())
        else:
            msg = f"Unknown assignment type: {self.ts_node.type}"
            raise ValueError(msg)

    def _DEPRECATED_parse_attribute_assignments(self) -> list[TSAssignment]:
        left = self.ts_node.child_by_field_name("name")
        right = self.ts_node.child_by_field_name("value")
        return [TSAssignment(self.ts_node, self.file_node_id, self.ctx, self, left, right, left)]

    def _DEPRECATED_parse_assignment_declarations(self) -> list[TSAssignment]:
        assignments = []
        for variable_declarator in self.ts_node.named_children:
            if variable_declarator.type != "variable_declarator":
                continue
            left = variable_declarator.child_by_field_name("name")
            type_node = variable_declarator.child_by_field_name("type")
            right = variable_declarator.child_by_field_name("value")
            if len(left.named_children) > 0:
                to_parse: deque[tuple[TSNode, TSNode | None]] = deque([(left, type_node)])
                while to_parse:
                    child, _type = to_parse.popleft()
                    for identifier in child.named_children:
                        if identifier.type == "pair_pattern":
                            value = identifier.child_by_field_name("value")
                            to_parse.append((value, _type))  # TODO:CG-10064
                            if value.type == "identifier":
                                # TODO: Support type resolution for aliased object unpacks
                                assignments.append(TSAssignment(variable_declarator, self.file_node_id, self.ctx, self, left, right, value))
                            else:
                                key = identifier.child_by_field_name("key")
                                assignments.append(TSAssignment(variable_declarator, self.file_node_id, self.ctx, self, left, right, key))
                        else:
                            assignments.append(TSAssignment(variable_declarator, self.file_node_id, self.ctx, self, left, right, identifier))

            else:
                assignments.append(TSAssignment(variable_declarator, self.file_node_id, self.ctx, self, left, right, left))
                while right and right.type == "assignment_expression":
                    left = right.child_by_field_name("left")
                    right = right.child_by_field_name("right")
                    assignments.append(TSAssignment(variable_declarator, self.file_node_id, self.ctx, self, left, right, left))

        return assignments

    def _DEPRECATED_parse_assignment_expression(self) -> list[TSAssignment]:
        assignments = []
        for child in self.ts_node.named_children:
            if child.type not in ["assignment_expression", "augmented_assignment_expression"]:
                continue
            left = child.child_by_field_name("left")
            right = child.child_by_field_name("right")
            assignments.append(TSAssignment(child, self.file_node_id, self.ctx, self, left, right, left))

        return assignments
