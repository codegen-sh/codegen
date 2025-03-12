from __future__ import annotations

from typing import TYPE_CHECKING

from codegen.sdk.core.symbol_groups.comment_group import CommentGroup
from codegen.sdk.typescript.statements.comment import TSComment, TSCommentType
from codegen.shared.decorators.docs import noapidoc, ts_apidoc

if TYPE_CHECKING:
    from codegen.sdk.typescript.symbol import TSSymbol


@ts_apidoc
class TSCommentGroup(CommentGroup):
    """A group of related symbols that represent a comment or docstring in TypeScript

    For example:
    ```
    // Comment 1
    // Comment 2
    // Comment 3
    ```
    would be 3 individual comments (accessible via `symbols`), but together they form a `CommentGroup` (accessible via `self).
    """

    @staticmethod
    @noapidoc
    def _get_sibbling_comments(symbol: TSSymbol) -> list[TSComment]:
        # Locate the body that contains the comment nodes
        current_node = symbol.ts_node
        parent_node = symbol.ts_node.parent
        while parent_node and parent_node.type not in ["program", "class_body", "block", "statement_block"]:
            current_node = parent_node
            parent_node = parent_node.parent

        if not parent_node:
            return None

        # Find the correct index of function_node in parent_node's children
        function_index = parent_node.children.index(current_node)

        if function_index is None:
            return None  # function_node is not a child of parent_node

        if function_index == 0:
            return None  # No nodes before this function, hence no comments

        comment_nodes = []
        # Iterate backwards from the function node to collect all preceding comment nodes
        for i in range(function_index - 1, -1, -1):
            if parent_node.children[i].type == "comment":
                # Check if the comment is directly above each other
                if parent_node.children[i].end_point[0] == parent_node.children[i + 1].start_point[0] - 1:
                    comment = TSComment.from_code_block(parent_node.children[i], symbol)
                    comment_nodes.insert(0, comment)
                else:
                    break  # Stop if there is a break in the comments
            else:
                break  # Stop if a non-comment node is encountered

        return comment_nodes

    @classmethod
    @noapidoc
    def from_symbol_comments(cls, symbol: TSSymbol):
        comment_nodes = cls._get_sibbling_comments(symbol)
        if not comment_nodes:
            return None
        return cls(comment_nodes, symbol.file_node_id, symbol.ctx, symbol)

    @classmethod
    @noapidoc
    def from_symbol_inline_comments(cls, symbol: TSSymbol):
        # Locate the body that contains the comment nodes
        current_node = symbol.ts_node
        parent_node = symbol.ts_node.parent
        while parent_node and parent_node.type not in ["program", "class_body", "block", "statement_block"]:
            current_node = parent_node
            parent_node = parent_node.parent

        if not parent_node:
            return None

        # Find the correct index of function_node in parent_node's children
        function_index = parent_node.children.index(current_node)

        if function_index is None:
            return None  # function_node is not a child of parent_node

        comment_nodes = []
        # Check if there are any comments after the function node
        if function_index + 1 < len(parent_node.children):
            if parent_node.children[function_index + 1].type == "comment":
                # Check if the comment is on the same line
                if parent_node.children[function_index].end_point[0] == parent_node.children[function_index + 1].start_point[0]:
                    comment = TSComment.from_code_block(parent_node.children[function_index + 1], symbol)
                    comment_nodes.append(comment)

        if not comment_nodes:
            return None

        return cls(comment_nodes, symbol.file_node_id, symbol.ctx, symbol)

    @classmethod
    @noapidoc
    def from_docstring(cls, symbol: TSSymbol) -> TSCommentGroup | None:
        """Returns the docstring of the function"""
        comment_nodes = cls._get_sibbling_comments(symbol)
        if not comment_nodes:
            return None
        # Docstring comments are filtered by SLASH_STAR comments
        docstring_nodes = [comment for comment in comment_nodes if comment.comment_type == TSCommentType.SLASH_STAR]
        if not docstring_nodes:
            return None
        return cls(docstring_nodes, symbol.file_node_id, symbol.ctx, symbol)

    @classmethod
    @noapidoc
    def from_comment_nodes(cls, comment_nodes: list[TSComment], symbol: TSSymbol):
        if not comment_nodes:
            return None

        # Docstring comments are filtered by SLASH_STAR comments
        docstring_nodes = [comment for comment in comment_nodes if comment.comment_type == TSCommentType.SLASH_STAR]
        if not docstring_nodes:
            return None
        return cls(docstring_nodes, symbol.file_node_id, symbol.ctx, symbol)
