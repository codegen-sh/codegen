from __future__ import annotations

from typing import TYPE_CHECKING

from codegen.sdk.core.assignment import Assignment
from codegen.sdk.core.autocommit import writer
from codegen.sdk.core.expressions.multi_expression import MultiExpression
from codegen.sdk.typescript.symbol import TSSymbol
from codegen.shared.decorators.docs import noapidoc, ts_apidoc

if TYPE_CHECKING:
    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.node_id_factory import NodeId
    from codegen.sdk.core.statements.export_statement import ExportStatement
    from codegen.sdk.typescript.statements.assignment_statement import TSAssignmentStatement


@ts_apidoc
class TSAssignment(Assignment["TSAssignmentStatement | ExportStatement"], TSSymbol):
    """A class representing TypeScript assignments, including variable declarations and property assignments.

    Handles various types of TypeScript assignments including variable declarators, assignment expressions,
    augmented assignments, property signatures, and public field definitions. It provides functionality
    for manipulating assignments and managing their associated types and comments.
    """

    assignment_types: list[str] = ["variable_declarator", "assignment_expression", "augmented_assignment_expression", "property_signature", "public_field_definition"]

    @noapidoc
    @classmethod
    def from_assignment(cls, ts_node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: TSAssignmentStatement) -> MultiExpression[TSAssignmentStatement, TSAssignment]:
        if ts_node.type not in ["assignment_expression", "augmented_assignment_expression"]:
            msg = f"Unknown assignment type: {ts_node.type}"
            raise ValueError(msg)

        left_node = ts_node.child_by_field_name("left")
        right_node = ts_node.child_by_field_name("right")
        assignments = cls._from_left_and_right_nodes(ts_node, file_node_id, ctx, parent, left_node, right_node)
        return MultiExpression(ts_node, file_node_id, ctx, parent, assignments)

    @classmethod
    def from_named_expression(cls, ts_node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: TSAssignmentStatement) -> MultiExpression[TSAssignmentStatement, TSAssignment]:
        """Creates a MultiExpression object from a TypeScript named expression node.

        Constructs assignments from a TypeScript named expression node (variable declarator, public field definition, or property signature) by extracting the left (name) and right (value) nodes.

        Args:
            ts_node (TSNode): The TypeScript node representing the named expression.
            file_node_id (NodeId): The unique identifier for the file containing this node.
            ctx (CodebaseContext): The graph representation of the codebase.
            parent (Parent): The parent node containing this expression.

        Returns:
            MultiExpression[Parent, TSAssignment]: A MultiExpression object containing the constructed assignments.

        Raises:
            ValueError: If the node type is not one of: "variable_declarator", "public_field_definition", or "property_signature".
        """
        if ts_node.type not in ["variable_declarator", "public_field_definition", "property_signature"]:
            msg = f"Unknown assignment type: {ts_node.type}"
            raise ValueError(msg)

        left_node = ts_node.child_by_field_name("name")
        right_node = ts_node.child_by_field_name("value")
        assignments = cls._from_left_and_right_nodes(ts_node, file_node_id, ctx, parent, left_node, right_node)
        return MultiExpression(ts_node, file_node_id, ctx, parent, assignments)

    @writer
    def set_inline_comment(self, comment: str, auto_format: bool = True, clean_format: bool = True) -> None:
        """Sets an inline comment for an assignment node.

        This method adds or updates an inline comment on the parent statement of the assignment node.

        Args:
            comment (str): The comment text to set.
            auto_format (bool, optional): Whether to automatically format the comment. Defaults to True.
            clean_format (bool, optional): Whether to clean existing formatting. Defaults to True.

        Returns:
            None
        """
        super().set_inline_comment(comment, auto_format=auto_format, clean_format=clean_format, node=self.parent.ts_node)
