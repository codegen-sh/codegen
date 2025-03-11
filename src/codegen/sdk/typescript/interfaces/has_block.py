from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Self

from codegen.sdk.core.autocommit import reader, writer
from codegen.sdk.core.detached_symbols.code_block import CodeBlock
from codegen.sdk.core.interfaces.has_block import HasBlock
from codegen.sdk.core.statements.statement import StatementType
from codegen.sdk.extensions.utils import find_all_descendants
from codegen.sdk.typescript.detached_symbols.decorator import TSDecorator
from codegen.sdk.typescript.statements.comment import TSComment, TSCommentType
from codegen.sdk.typescript.symbol_groups.comment_group import TSCommentGroup
from codegen.sdk.utils import find_index
from codegen.shared.decorators.docs import ts_apidoc

if TYPE_CHECKING:
    from codegen.sdk.typescript.detached_symbols.code_block import TSCodeBlock
    from codegen.sdk.typescript.detached_symbols.jsx.element import JSXElement


@ts_apidoc
class TSHasBlock(HasBlock["TSCodeBlock", TSDecorator]):
    """A TypeScript base class that provides block-level code organization and decorator handling capabilities.

    This class extends the concept of block scoping for TypeScript code elements like classes and functions.
    It provides functionality for managing code blocks, decorators, JSX elements, and documentation within
    those blocks. The class supports operations such as retrieving and manipulating docstrings,
    handling JSX components, and managing TypeScript decorators.
    """

    @property
    @reader
    def is_decorated(self) -> bool:
        """Checks if the current symbol has a decorator.

        Determines if the symbol has a preceding decorator node.

        Returns:
            bool: True if the symbol has a decorator node as its previous named sibling,
                False otherwise.
        """
        previous_sibling = self.ts_node.prev_named_sibling
        # is decorated if it has a previous named sibling (i.e. the text above the function) and it is type=decorator
        return previous_sibling and previous_sibling.type == "decorator"

    @property
    @reader
    def decorators(self) -> list[TSDecorator]:
        """Returns a list of decorators associated with this symbol.

        Retrieves all decorators applied to this symbol by looking at both previous named siblings and decorator fields.
        This includes both inline decorators and standalone decorator statements.

        Returns:
            list[TSDecorator]: A list of TSDecorator objects representing all decorators applied to this symbol.
            Returns an empty list if no decorators are found.
        """
        decorators = []
        # Get all previous named siblings that are decorators, break once we hit a non decorator
        prev_named_sibling = self.ts_node.prev_named_sibling
        while prev_named_sibling and prev_named_sibling.type == "decorator":
            decorators.append(TSDecorator(prev_named_sibling, self))
            prev_named_sibling = prev_named_sibling.prev_named_sibling
        for child in self.ts_node.children_by_field_name("decorator"):
            decorators.append(TSDecorator(child, self))
        return decorators

    @property
    @reader
    def jsx_elements(self) -> list[JSXElement[Self]]:
        """Returns a list of all JSX elements contained within this symbol.

        Searches through the extended nodes of the symbol for any JSX elements or self-closing JSX elements
        and returns them as a list of JSXElement objects.

        Args:
            None

        Returns:
            list[JSXElement[Self]]: A list of JSXElement objects contained within this symbol.
        """
        jsx_elements = []
        for node in self.extended_nodes:
            jsx_element_nodes = find_all_descendants(node.ts_node, {"jsx_element", "jsx_self_closing_element"})
            jsx_elements.extend([self._parse_expression(x) for x in jsx_element_nodes])
        return jsx_elements

    @reader
    def get_component(self, component_name: str, optional: bool = False) -> JSXElement[Self] | None:
        """Returns a specific JSX element from within this symbol's JSX elements.

        Searches through all JSX elements in this symbol's code block and returns the first one that matches
        the given component name.

        Args:
            component_name (str): The name of the JSX component to find.
            optional (bool, optional): If True, return None if the component is not found. Defaults to False.

        Returns:
            JSXElement[Self] | None: The matching JSX element if found, None otherwise.
        """
        for component in self.jsx_elements:
            if component.name == component_name:
                return component
        if not optional:
            msg = f"Component {component_name} not found in symbol {self.name} of file {self.file_path}. Use optional=True to return None instead."
            raise ValueError(msg)
        return None

    @cached_property
    @reader
    def docstring(self) -> TSCommentGroup | None:
        """Retrieves the docstring of a function or class.

        Returns any comments immediately preceding this node as a docstring. For nodes that are children of a HasBlock, it returns consecutive comments that end on the line before the node starts.
        For other nodes, it returns formatted docstring comments.

        Returns:
            TSCommentGroup | None: A CommentGroup representing the docstring if one exists, None otherwise.
        """
        if self.parent.parent.parent and isinstance(self.parent.parent, CodeBlock):
            comments = []
            sibling_statements = self.parent.parent.statements
            index = find_index(self.ts_node, [x.ts_node for x in sibling_statements])
            if index == -1:
                return None

            row = self.start_point[0]
            for statement in reversed(sibling_statements[:index]):
                if statement.end_point[0] != row - 1:
                    break
                row = statement.start_point[0]
                if statement.statement_type == StatementType.COMMENT:
                    comments.append(statement)

            return TSCommentGroup.from_comment_nodes(list(reversed(comments)), self)

        return TSCommentGroup.from_docstring(self)

    @writer
    def set_docstring(self, docstring: str, auto_format: bool = True, clean_format: bool = True, leading_star: bool = True, force_multiline: bool = False) -> None:
        """Sets or updates a docstring for a code element.

        Adds a new docstring if none exists, or updates the existing docstring. Handles formatting and placement
        of the docstring according to the specified parameters.

        Args:
            docstring (str): The docstring text to be added or updated.
            auto_format (bool, optional): Whether to automatically format the text into a docstring format. Defaults to True.
            clean_format (bool, optional): Whether to clean existing formatting from the docstring before inserting. Defaults to True.
            leading_star (bool, optional): Whether to add leading "*" to each line of the comment block. Defaults to True.
            force_multiline (bool, optional): Whether to force single line comments to be multi-line. Defaults to False.

        Returns:
            None
        """
        # Clean existing formatting off docstring
        if clean_format:
            docstring = TSComment.clean_comment(docstring)

        # If the docstring exists, edit it
        if self.docstring:
            if auto_format:
                self.docstring.edit_text(docstring)
            else:
                self.docstring.edit(docstring)
        else:
            if auto_format:
                docstring = TSComment.generate_comment(docstring, TSCommentType.SLASH_STAR, leading_star=leading_star, force_multiline=force_multiline)
            # If a comment exists, insert the docstring after it
            if self.comment:
                self.comment.insert_after(docstring)
            # If no comment exists, insert the docstring before the function
            else:
                self.extended.insert_before(docstring, fix_indentation=True)
