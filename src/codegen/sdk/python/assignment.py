from __future__ import annotations

from collections.abc import Collection
from typing import TYPE_CHECKING

from codegen.sdk.codebase.transactions import RemoveTransaction, TransactionPriority
from codegen.sdk.core.assignment import Assignment
from codegen.sdk.core.autocommit.decorators import remover
from codegen.sdk.core.expressions.multi_expression import MultiExpression
from codegen.sdk.core.statements.assignment_statement import AssignmentStatement
from codegen.sdk.extensions.autocommit import reader
from codegen.sdk.python.symbol import PySymbol
from codegen.sdk.python.symbol_groups.comment_group import PyCommentGroup
from codegen.shared.decorators.docs import noapidoc, py_apidoc
from codegen.shared.logging.get_logger import get_logger

if TYPE_CHECKING:
    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.node_id_factory import NodeId
    from codegen.sdk.python.statements.assignment_statement import PyAssignmentStatement

logger = get_logger(__name__)


@py_apidoc
class PyAssignment(Assignment["PyAssignmentStatement"], PySymbol):
    """An abstract representation of a assignment in python.

    This includes assignments of variables to functions, other variables, class instantiations, etc.
    """

    @noapidoc
    @classmethod
    def from_assignment(cls, ts_node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: PyAssignmentStatement) -> MultiExpression[PyAssignmentStatement, PyAssignment]:
        if ts_node.type not in ["assignment", "augmented_assignment"]:
            msg = f"Unknown assignment type: {ts_node.type}"
            raise ValueError(msg)

        left_node = ts_node.child_by_field_name("left")
        right_node = ts_node.child_by_field_name("right")
        assignments = cls._from_left_and_right_nodes(ts_node, file_node_id, ctx, parent, left_node, right_node)
        return MultiExpression(ts_node, file_node_id, ctx, parent, assignments)

    @classmethod
    def from_named_expression(cls, ts_node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: PyAssignmentStatement) -> MultiExpression[PyAssignmentStatement, PyAssignment]:
        """Creates a MultiExpression from a Python named expression.

        Creates assignments from a named expression node ('walrus operator' :=) by parsing its name and value fields.

        Args:
            ts_node (TSNode): The TreeSitter node representing the named expression.
            file_node_id (NodeId): The identifier of the file containing this node.
            ctx (CodebaseContext): The codebase context instance.
            parent (Parent): The parent node that contains this expression.

        Returns:
            MultiExpression[Parent, PyAssignment]: A MultiExpression containing the assignments created from the named expression.

        Raises:
            ValueError: If the provided ts_node is not of type 'named_expression'.
        """
        if ts_node.type != "named_expression":
            msg = f"Unknown assignment type: {ts_node.type}"
            raise ValueError(msg)

        left_node = ts_node.child_by_field_name("name")
        right_node = ts_node.child_by_field_name("value")
        assignments = cls._from_left_and_right_nodes(ts_node, file_node_id, ctx, parent, left_node, right_node)
        return MultiExpression(ts_node, file_node_id, ctx, parent, assignments)

    @property
    @reader
    def comment(self) -> PyCommentGroup | None:
        """Returns the comment group associated with the symbol.

        Retrieves and returns any comments associated with the symbol. These comments are typically
        located above or adjacent to the symbol in the source code.

        Args:
            self: The symbol instance to retrieve comments for.

        Returns:
            PyCommentGroup | None: A comment group object containing the symbol's comments if they exist,
            None otherwise.
        """
        # HACK: This is a temporary solution until comments are fixed
        return PyCommentGroup.from_symbol_comments(self)

    @property
    @reader
    def inline_comment(self) -> PyCommentGroup | None:
        """A property that retrieves the inline comment group associated with a symbol.

        Retrieves any inline comments that are associated with this symbol. Inline comments are comments that appear on the same line as the code.

        Args:
            None

        Returns:
            PyCommentGroup | None: The inline comment group associated with the symbol, if one exists. Returns None if there are no inline comments.
        """
        # HACK: This is a temporary solution until comments are fixed
        return PyCommentGroup.from_symbol_inline_comments(self, self.ts_node.parent)

    @noapidoc
    def _partial_remove_when_tuple(self, name, delete_formatting: bool = True, priority: int = 0, dedupe: bool = True):
        idx = self.parent.left.index(name)
        value = self.value[idx]
        self.parent._values_scheduled_for_removal.append(value)
        # Special case for removing brackets of value
        if len(self.value) - len(self.parent._values_scheduled_for_removal) == 1:
            remainder = str(next(x for x in self.value if x not in self.parent._values_scheduled_for_removal and x != value))
            r_t = RemoveTransaction(self.value.start_byte, self.value.end_byte, self.file, priority=priority)
            self.transaction_manager.add_transaction(r_t)
            self.value.insert_at(self.value.start_byte, remainder, priority=priority)
        else:
            # Normal just remove one value
            value.remove(delete_formatting=delete_formatting, priority=priority, dedupe=dedupe)
        # Remove assignment name
        name.remove(delete_formatting=delete_formatting, priority=priority, dedupe=dedupe)

    @noapidoc
    def _active_transactions_on_assignment_names(self, transaction_order: TransactionPriority) -> int:
        return [
            any(self.transaction_manager.get_transactions_at_range(self.file.path, start_byte=asgnmt.get_name().start_byte, end_byte=asgnmt.get_name().end_byte, transaction_order=transaction_order))
            for asgnmt in self.parent.assignments
        ].count(True)

    @remover
    def remove(self, delete_formatting: bool = True, priority: int = 0, dedupe: bool = True) -> None:
        """Deletes this assignment and its related extended nodes (e.g. decorators, comments).


        Removes the current node and its extended nodes (e.g. decorators, comments) from the codebase.
        After removing the node, it handles cleanup of any surrounding formatting based on the context.

        Args:
            delete_formatting (bool): Whether to delete surrounding whitespace and formatting. Defaults to True.
            priority (int): Priority of the removal transaction. Higher priority transactions are executed first. Defaults to 0.
            dedupe (bool): Whether to deduplicate removal transactions at the same location. Defaults to True.

        Returns:
            None
        """
        if self.ctx.config.unpacking_assignment_partial_removal:
            if isinstance(self.parent, AssignmentStatement) and len(self.parent.assignments) > 1:
                # Unpacking assignments
                name = self.get_name()
                if isinstance(self.value, Collection):
                    if len(self.parent._values_scheduled_for_removal) < len(self.parent.assignments) - 1:
                        self._partial_remove_when_tuple(name, delete_formatting, priority, dedupe)
                        return
                    else:
                        self.parent._values_scheduled_for_removal = []
                else:
                    if name.source == "_":
                        logger.warning("Attempting to remove '_' in unpacking, command will be ignored. If you wish to remove the statement, remove the other remaining variable(s)!")
                        return
                    transaction_count = self._active_transactions_on_assignment_names(TransactionPriority.Edit)
                    throwaway = [asgnmt.name == "_" for asgnmt in self.parent.assignments].count(True)
                    # Only edit if we didn't already omit all the other assignments, otherwise just remove the whole thing
                    if transaction_count + throwaway < len(self.parent.assignments) - 1:
                        name.edit("_", priority=priority, dedupe=dedupe)
                        return

        super().remove(delete_formatting=delete_formatting, priority=priority, dedupe=dedupe)
