from typing import TYPE_CHECKING, Generic, Self, TypeVar

from codegen.sdk.core.autocommit import reader, writer
from codegen.sdk.core.detached_symbols.code_block import CodeBlock
from codegen.sdk.core.interfaces.editable import Editable
from codegen.sdk.core.statements.statement import Statement
from codegen.sdk.core.symbol_groups.multi_line_collection import MultiLineCollection
from codegen.sdk.extensions.utils import find_line_start_and_end_nodes
from codegen.shared.decorators.docs import noapidoc, ts_apidoc

if TYPE_CHECKING:
    from codegen.sdk.typescript.assignment import TSAssignment
    from codegen.sdk.typescript.interfaces.has_block import TSHasBlock


Parent = TypeVar("Parent", bound="TSHasBlock")


@ts_apidoc
class TSCodeBlock(CodeBlock[Parent, "TSAssignment"], Generic[Parent]):
    """Extends the CodeBlock class to provide TypeScript-specific functionality."""

    @noapidoc
    @reader
    def _parse_statements(self) -> MultiLineCollection[Statement, Self]:
        statements: list[Statement] = self.ctx.parser.parse_ts_statements(self.ts_node, self.file_node_id, self.ctx, self)
        line_nodes = find_line_start_and_end_nodes(self.ts_node)
        start_node = line_nodes[1][0] if len(line_nodes) > 1 else line_nodes[0][0]
        end_node = line_nodes[-2][1] if len(line_nodes) > 1 else line_nodes[-1][1]
        indent_size = start_node.start_point[1]
        collection = MultiLineCollection(
            children=statements,
            file_node_id=self.file_node_id,
            ctx=self.ctx,
            parent=self,
            node=self.ts_node,
            indent_size=indent_size,
            leading_delimiter="",
            start_byte=start_node.start_byte - indent_size,
            end_byte=end_node.end_byte + 1,
        )
        return collection

    @reader
    @noapidoc
    def _get_line_starts(self) -> list[Editable]:
        """Returns an ordered list of first Editable for each non-empty line within the code block"""
        line_start_nodes = super()._get_line_starts()
        if len(line_start_nodes) >= 3 and line_start_nodes[0].source == "{" and line_start_nodes[-1].source == "}":
            # Remove the first and last line of the code block as they are opening and closing braces.
            return line_start_nodes[1:-1]
        return line_start_nodes

    @reader
    @noapidoc
    def _get_line_ends(self) -> list[Editable]:
        """Returns an ordered list of last Editable for each non-empty line within the code block"""
        line_end_nodes = super()._get_line_ends()
        # Remove the first and last line of the code block as they are opening and closing braces.
        return line_end_nodes[1:-1]

    @writer
    def unwrap(self) -> None:
        """Unwraps a code block by removing its opening and closing braces.

        This method removes both the opening and closing braces of a code block, including any trailing whitespace
        up to the next sibling node if it exists, or up to the closing brace of the last line if no sibling exists.
        This is commonly used to flatten nested code structures like if statements, with statements, and function bodies.

        Returns:
            None
        """
        super().unwrap()
        # Also remove the closing brace of the last line.
        next_sibling = self.ts_node.next_sibling
        if next_sibling:
            self.remove_byte_range(self.ts_node.end_byte - 1, next_sibling.start_byte)
        else:
            # If there is no next sibling, remove up to the closing brace of the last line
            self.remove_byte_range(self._get_line_ends()[-1].end_byte, self.ts_node.end_byte)
