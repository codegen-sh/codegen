from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from codegen.sdk.core.autocommit import commiter, reader, writer
from codegen.sdk.core.dataclasses.usage import UsageKind
from codegen.sdk.core.statements.statement import Statement, StatementType
from codegen.shared.decorators.docs import apidoc, noapidoc

if TYPE_CHECKING:
    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.detached_symbols.code_block import CodeBlock
    from codegen.sdk.core.interfaces.has_name import HasName
    from codegen.sdk.core.node_id_factory import NodeId


def lowest_indentation(text_blocks, skip_lines: int = 0):
    if not text_blocks:
        return 0

    # Filter out empty strings and strings with only whitespace
    non_empty_blocks = [block for block in text_blocks if block.strip()]

    # Skip the first n lines
    non_empty_blocks = non_empty_blocks[skip_lines:]

    if not non_empty_blocks:
        return 0

    # Count leading spaces for each non-empty block
    indentations = [len(block) - len(block.lstrip()) for block in non_empty_blocks]

    # Return the minimum indentation
    return min(indentations)


TCodeBlock = TypeVar("TCodeBlock", bound="CodeBlock")


@apidoc
class Comment(Statement[TCodeBlock], Generic[TCodeBlock]):
    """Abstract representation of comment statements."""

    statement_type = StatementType.COMMENT

    @property
    @reader
    def nested_code_blocks(self: Statement[TCodeBlock]) -> list[TCodeBlock]:
        """Returns a list of nested code blocks within the statement.

        A property that returns an empty list as comments, by default, do not have any nested code blocks.

        Args:
            self: The statement instance.

        Returns:
            list[TCodeBlock]: An empty list, as comments do not contain nested code blocks.
        """
        return []

    @noapidoc
    @classmethod
    @reader
    def from_expression_statement(cls, ts_node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: Statement, code_block: TCodeBlock, pos: int, comment_node: TSNode) -> Comment:
        return cls(ts_node, file_node_id, ctx, code_block, pos)

    @property
    @reader
    def text(self) -> str:
        """Returns the text content of the comment.

        Returns the actual text content of the comment without any comment delimiters (e.g., '#', '/* */'). For accessing
        the complete comment including delimiters, use the `source` property instead.

        Returns:
            str: The text content of the comment with delimiters removed.
        """
        return self._parse_comment()

    @text.setter
    @writer
    def text(self, new_text: str) -> None:
        """Replace the text content of a comment while preserving the comment delimiters and
        autoformatting.

        Args:
            new_text (str): The new text content to replace the existing comment. This should be
                the raw text without comment delimiters.

        Returns:
            None
        """
        self.edit_text(new_text)

    @writer
    def edit_text(self, new_text: str) -> None:
        """Replace the text of a comment with new text.

        Updates the comment text while maintaining proper comment delimiters (e.g., `#` or `/* */`) and formatting.

        Args:
            new_text (str): The new text content to replace the existing comment text.

        Returns:
            None
        """
        # Generate comment block with new source
        new_src = self._unparse_comment(new_text)
        super().edit(new_src, fix_indentation=True, dedupe=True)

    @noapidoc
    @commiter
    def _parse_comment(self) -> str:
        """Parse out the comment into its text content."""
        msg = "This method should be implemented by the subclass"
        raise NotImplementedError(msg)

    @noapidoc
    @commiter
    def _unparse_comment(self, new_src: str):
        """Unparses cleaned text content into a comment block."""
        msg = "This method should be implemented by the subclass"
        raise NotImplementedError(msg)

    @commiter
    @noapidoc
    def _compute_dependencies(self, usage_type: UsageKind = UsageKind.BODY, dest: HasName | None = None) -> None:
        pass
