from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from codegen.sdk.core.autocommit import reader, writer
from codegen.sdk.core.statements.if_block_statement import IfBlockStatement
from codegen.sdk.core.statements.statement import StatementType
from codegen.shared.decorators.docs import apidoc
from codegen.shared.logging.get_logger import get_logger

if TYPE_CHECKING:
    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.node_id_factory import NodeId
    from codegen.sdk.typescript.detached_symbols.code_block import TSCodeBlock


logger = get_logger(__name__)


Parent = TypeVar("Parent", bound="TSCodeBlock")


@apidoc
class TSIfBlockStatement(IfBlockStatement[Parent, "TSIfBlockStatement"], Generic[Parent]):
    """Typescript implementation of the if/elif/else statement block.
    For example, if there is a code block like:
    if (condition1) {
        block1
    } else if (condition2) {
        block2
    } else {
        block3
    }
    This class represents the entire block, including the conditions and nested code blocks.
    """

    statement_type = StatementType.IF_BLOCK_STATEMENT
    _else_clause_node: TSNode | None = None

    def __init__(
        self,
        ts_node: TSNode,
        file_node_id: NodeId,
        ctx: CodebaseContext,
        parent: Parent,
        pos: int,
        else_clause_node: TSNode | None = None,
        main_if_block: TSIfBlockStatement | None = None,
    ) -> None:
        super().__init__(ts_node, file_node_id, ctx, parent, pos)
        self._else_clause_node = else_clause_node
        self._main_if_block = main_if_block
        # Call .value to unwrap the parenthesis
        condition = self.child_by_field_name("condition")
        self.condition = condition.value if condition else None
        self.consequence_block = self._parse_consequence_block()
        self._alternative_blocks = self._parse_alternative_blocks() if self.is_if_statement else None
        self.consequence_block.parse()

    @reader
    def _parse_consequence_block(self) -> TSCodeBlock:
        from codegen.sdk.typescript.detached_symbols.code_block import TSCodeBlock

        if self.is_if_statement or self.is_elif_statement:
            consequence_node = self.ts_node.child_by_field_name("consequence")
        else:
            consequence_node = self.ts_node.named_children[0]
        return TSCodeBlock(consequence_node, self.parent.level + 1, self.parent, self)

    @reader
    def _parse_alternative_blocks(self) -> list[TSIfBlockStatement]:
        if self.is_else_statement or self.is_elif_statement:
            return []

        if_blocks = []
        alt_block = self
        while alt_node := alt_block.ts_node.child_by_field_name("alternative"):
            if (if_node := alt_node.named_children[0]).type == "if_statement":
                # Elif statements are represented as if statements with an else clause as the parent node
                alt_block = TSIfBlockStatement(if_node, self.file_node_id, self.ctx, self.parent, self.index, else_clause_node=alt_node, main_if_block=self._main_if_block or self)
            else:
                # Else clause
                alt_block = TSIfBlockStatement(alt_node, self.file_node_id, self.ctx, self.parent, self.index, main_if_block=self._main_if_block or self)
            if_blocks.append(alt_block)
        return if_blocks

    @property
    @reader
    def is_if_statement(self) -> bool:
        """Determines if the current block is a standalone 'if' statement.

        Args:
            None

        Returns:
            bool: True if the current block is a standalone 'if' statement, False otherwise.
        """
        return self.ts_node.type == "if_statement" and self._else_clause_node is None

    @property
    @reader
    def is_else_statement(self) -> bool:
        """Determines if the current block is an else block.

        A property that checks if the current TreeSitter node represents an else clause in an if/elif/else statement structure.

        Returns:
            bool: True if the current block is an else block, False otherwise.
        """
        return self.ts_node.type == "else_clause"

    @property
    @reader
    def is_elif_statement(self) -> bool:
        """Determines if the current block is an elif block.

        This method checks if the current block is an elif block by verifying that it is both an if_statement and has an else clause node associated with it.

        Returns:
            bool: True if the current block is an elif block, False otherwise.
        """
        return self.ts_node.type == "if_statement" and self._else_clause_node is not None

    @writer
    def _else_if_to_if(self) -> None:
        """Converts an elif block to an if block.

        Args:
            None

        Returns:
            None
        """
        if not self.is_elif_statement:
            return

        self.remove_byte_range(self.ts_node.start_byte - len("else "), self.ts_node.start_byte)
