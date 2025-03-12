from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

from codegen.sdk.core.autocommit import reader, writer
from codegen.sdk.core.expressions import Expression
from codegen.sdk.core.statements.comment import Comment
from codegen.sdk.extensions.sort import sort_editables
from codegen.shared.decorators.docs import apidoc

if TYPE_CHECKING:
    from tree_sitter import Node as TSNode

    from codegen.sdk.core.detached_symbols.code_block import CodeBlock
    from codegen.sdk.core.detached_symbols.decorator import Decorator
    from codegen.sdk.core.detached_symbols.function_call import FunctionCall
    from codegen.sdk.core.symbol_groups.comment_group import CommentGroup

TCodeBlock = TypeVar("TCodeBlock", bound="CodeBlock")
TDecorator = TypeVar("TDecorator", bound="Decorator")


@apidoc
class HasBlock(Expression, Generic[TCodeBlock, TDecorator]):
    """An interface for any code object that has a block of code, e.g. a function, class, etc.

    Attributes:
        code_block: The block of code associated with the code object.
    """

    code_block: TCodeBlock

    # =======[ CODE BLOCK ]======
    def _parse_code_block(self, body_node: TSNode | None = None) -> TCodeBlock | None:
        """Returns the code block of the function."""
        body_node = body_node or self.ts_node.child_by_field_name("body")
        if not body_node:
            return None
        parent_block = None
        level = 0  # Level 0 is reserved for files
        parent = self.parent
        while parent is not None and parent is not parent.parent:
            if isinstance(parent, HasBlock) and hasattr(parent, "code_block"):
                parent_block = parent.code_block
                level = parent_block.level + 1
                break
            parent = parent.parent

        return self.ctx.node_classes.code_block_cls(body_node, level, parent_block, self)

    @property
    @reader
    def function_calls(self) -> list[FunctionCall]:
        """Returns all function calls within the code block and its decorators.

        Args:
            None

        Returns:
            list[FunctionCall]: A sorted list of FunctionCall objects representing all
            function calls in the code block and its decorators. The list may contain
            duplicates.
        """
        fcalls = self.code_block.function_calls
        for dec in self.decorators:
            fcalls.extend(dec.function_calls)
        return sort_editables(fcalls, dedupe=False)

    # =======[ DECORATORS ]=======

    @property
    @abstractmethod
    def is_decorated(self) -> bool:
        """Check if the symbol has decorators.

        A helper method to determine if a function, class, or method has any
        applied decorators.

        Returns:
            bool: True if the symbol has one or more decorators, False otherwise.
        """

    # TODO: class def + function are almost copied of this function? just use the HasBlock definition?
    @property
    @abstractmethod
    def decorators(self) -> list[TDecorator]:
        """Returns list of all decorators on this Symbol.

        Gets all decorators associated with a code entity (function, class, method).

        Returns:
            list[TDecorator]: A list of Decorator objects. Empty list if no decorators are present.
        """

    @writer
    def add_decorator(self, new_decorator: str, skip_if_exists: bool = False) -> bool:
        """Adds a decorator to a function or method.

        Adds a new decorator to the symbol's definition before the first non-comment extended node with proper indentation.

        Args:
            new_decorator (str): The decorator to add, including the '@' symbol.
            skip_if_exists (bool, optional): If True, skips adding if the decorator exists.

        Returns:
            bool: True if the decorator was added, False if skipped.
        """
        if skip_if_exists:
            if new_decorator in self.decorators:
                return False
        # Get the top most extended ts_node that excludes docstrings
        extended_ts_nodes = self.extended_nodes
        # Iterate through the extended nodes and find the first node that is not a comment
        for node in extended_ts_nodes:
            if not isinstance(node, Comment):
                break
        node.insert_before(new_decorator, fix_indentation=True)
        return True

    @property
    @abstractmethod
    @reader
    def docstring(self) -> CommentGroup | None:
        """Retrieves the docstring of the expression.

        Args:
            None

        Returns:
            CommentGroup | None: The docstring as a CommentGroup if it exists, None otherwise.
        """

    @abstractmethod
    @writer
    def set_docstring(self, docstring: str) -> None:
        """Sets or updates the docstring for the current entity.

        Modifies the entity's docstring by either replacing an existing one or creating a new one.

        Args:
            docstring (str): The new docstring content to set.

        Returns:
            None: This method doesn't return anything.
        """
