from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from codegen.sdk.core.autocommit import reader, writer
from codegen.sdk.core.statements.comment import Comment
from codegen.sdk.core.symbol_group import SymbolGroup
from codegen.shared.decorators.docs import apidoc, noapidoc

if TYPE_CHECKING:
    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.node_id_factory import NodeId

Parent = TypeVar("Parent")


@apidoc
class CommentGroup(SymbolGroup[Comment, Parent]):
    """A group of comments that form a larger comment block."""

    _indentation: int  # Indentation level of the comment block

    def __init__(self, children: list[Comment], file_node_id: NodeId, ctx: CodebaseContext, parent: Parent) -> None:
        assert len(children) > 0, "CommentGroup must have at least one symbol"
        super().__init__(file_node_id, ctx, parent, node=children[0].ts_node, children=children)
        self._indentation = self._calculate_indentation()

    @property
    @reader
    def text(self) -> str:
        """Return the text content of all comments in the comment block.

        Combines multiple comment lines with newlines, excluding comment delimiters.

        Returns:
            str: The concatenated text content of all comments in the block.
        """
        return "\n".join([comment.text for comment in self.symbols])

    @text.setter
    @writer
    def text(self, new_text: str) -> None:
        """Replace the text of a CommentGroup with new text.

        Updates the text of all comments in the group, maintaining proper comment delimiters like `#` or `/* */`.
        After updating the first comment's text, all subsequent comments in the group are removed.

        Args:
            new_text (str): The new text content to replace the existing comment text. Will be formatted with appropriate comment delimiters.

        Returns:
            None
        """
        self.edit_text(new_text)

    @writer
    def edit_text(self, new_text: str) -> None:
        """Replace the text content of a comment group with new text.

        Updates the comment text while preserving and auto-formatting comment delimiters.
        Removes any additional comment lines from the comment group, leaving only the
        first line with the new text.

        Args:
            new_text (str): The new text content to replace the existing comment text.
                The text should not include comment delimiters.

        Returns:
            None
        """
        # Generate comment block with new source
        self.symbols[0].edit_text(new_text)
        for symbol in self.symbols[1:]:
            symbol.remove()

    @noapidoc
    @reader
    def _calculate_indentation(self) -> int:
        """Calculate the indentation level of the comment block."""
        return self.symbols[0].ts_node.start_point[1]
