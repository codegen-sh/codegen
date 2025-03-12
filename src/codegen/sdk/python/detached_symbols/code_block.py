from __future__ import annotations

from typing import TYPE_CHECKING, Generic, Self, TypeVar

from codegen.sdk.core.autocommit import reader
from codegen.sdk.core.detached_symbols.code_block import CodeBlock
from codegen.sdk.core.statements.block_statement import BlockStatement
from codegen.sdk.core.statements.import_statement import ImportStatement
from codegen.sdk.core.statements.statement import Statement, StatementType
from codegen.sdk.core.symbol_groups.multi_line_collection import MultiLineCollection
from codegen.shared.decorators.docs import noapidoc, py_apidoc

if TYPE_CHECKING:
    from codegen.sdk.python.assignment import PyAssignment
    from codegen.sdk.python.interfaces.has_block import PyHasBlock
    from codegen.sdk.python.statements.with_statement import WithStatement


Parent = TypeVar("Parent", bound="PyHasBlock")


@py_apidoc
class PyCodeBlock(CodeBlock[Parent, "PyAssignment"], Generic[Parent]):
    """Extends CodeBlock for Python codebases."""

    @noapidoc
    @reader
    def _parse_statements(self) -> MultiLineCollection[Statement, Self]:
        statements: list[Statement] = self.ctx.parser.parse_py_statements(self.ts_node, self.file_node_id, self.ctx, self)
        collection = MultiLineCollection(
            children=statements,
            file_node_id=self.file_node_id,
            ctx=self.ctx,
            parent=self,
            node=self.ts_node,
            indent_size=self.start_point[1],
            leading_delimiter="",
            start_byte=self.start_byte - self.start_point[1],
        )
        return collection

    @property
    @reader
    def with_statements(self) -> list[WithStatement]:
        """Returns a list of all 'with' statements within the code block.

        Retrieves all with statements in the code block, including those at all nested levels.

        Returns:
            A list of with statement objects found within this code block.
        """
        return [x for x in self.statements if x.statement_type == StatementType.WITH_STATEMENT]

    @reader
    def get_with_statements(self, level: int) -> list[WithStatement]:
        """Gets with statements at a specific block level.

        Filters the with statements in this code block to only include those at the specified block level.

        Args:
            level (int): The block level to filter by. 0 represents the top level.

        Returns:
            list[WithStatement]: A list of WithStatement objects at the specified block level.
        """
        return [x for x in self.with_statements if x.parent.level == level]

    def _smart_remove(self, child, *args, **kwargs) -> bool:
        if len(self.statements) <= 1 and not isinstance(child, ImportStatement):
            if isinstance(self.parent, BlockStatement):
                self.parent.remove(*args, **kwargs)
                return True
            else:
                self.remove_byte_range(self.start_byte, self.end_byte)
                self.parent.insert_after("pass", newline=False)
                return True
        return False
