from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from codegen.sdk.core.autocommit import reader, writer
from codegen.sdk.core.statements.if_block_statement import IfBlockStatement
from codegen.sdk.core.statements.statement import StatementType
from codegen.shared.decorators.docs import apidoc

if TYPE_CHECKING:
    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.node_id_factory import NodeId
    from codegen.sdk.python.detached_symbols.code_block import PyCodeBlock

Parent = TypeVar("Parent", bound="PyCodeBlock")


@apidoc
class PyIfBlockStatement(IfBlockStatement[Parent, "PyIfBlockStatement"], Generic[Parent]):
    """Pythons implementation of the if/elif/else statement block.

    For example, if there is a code block like:
    if condition1:
        block1
    elif condition2:
        block2
    else:
        block3
    This class represents the entire block, including the conditions and nested code blocks.
    """

    statement_type = StatementType.IF_BLOCK_STATEMENT

    def __init__(self, ts_node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: Parent, pos: int, main_if_block: PyIfBlockStatement | None = None) -> None:
        super().__init__(ts_node, file_node_id, ctx, parent, pos)
        self._main_if_block = main_if_block
        self.condition = self.child_by_field_name("condition")
        self.consequence_block = self._parse_consequence_block()
        self._alternative_blocks = self._parse_alternative_blocks() if self.is_if_statement else None
        self.consequence_block.parse()

    @reader
    def _parse_consequence_block(self) -> PyCodeBlock:
        from codegen.sdk.python.detached_symbols.code_block import PyCodeBlock

        body_node = self.ts_node.child_by_field_name("body") if self.is_else_statement else self.ts_node.child_by_field_name("consequence")
        return PyCodeBlock(body_node, self.parent.level + 1, self.parent, self)

    @reader
    def _parse_alternative_blocks(self) -> list[PyIfBlockStatement]:
        # If the current block is the top main if block, iterate through all the children alternative blocks
        alt_blocks = []
        if self.is_if_statement:
            for alt_node in self.ts_node.children_by_field_name("alternative"):
                alt_block = PyIfBlockStatement(alt_node, self.file_node_id, self.ctx, self.parent, self.index, main_if_block=self._main_if_block or self)
                alt_blocks.append(alt_block)
        return alt_blocks

    @property
    @reader
    def is_if_statement(self) -> bool:
        """Check if the current block is an if statement.

        Returns:
            bool: True if the current block is an if statement, False otherwise.
        """
        return self.ts_node.type == "if_statement"

    @property
    @reader
    def is_else_statement(self) -> bool:
        """Determines if the current block is an else block.

        A property that checks if the current TreeSitter node represents an else clause in an if-elif-else statement chain.

        Returns:
            bool: True if the current block is an else block, False otherwise.
        """
        return self.ts_node.type == "else_clause"

    @property
    @reader
    def is_elif_statement(self) -> bool:
        """Determines if the current block is an 'elif' clause.

        Returns:
            bool: True if the current block is an 'elif' clause, False otherwise.
        """
        return self.ts_node.type == "elif_clause"

    @writer
    def _else_if_to_if(self) -> None:
        """Converts an 'elif' block to an 'if' block if applicable.

        Args:
            None

        Returns:
            None
        """
        if not self.is_elif_statement:
            return

        self.remove_byte_range(self.ts_node.start_byte, self.ts_node.start_byte + len("el"))
