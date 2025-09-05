from functools import cached_property

from codegen.sdk.core.autocommit import reader, writer
from codegen.sdk.core.interfaces.has_block import HasBlock
from codegen.sdk.python.detached_symbols.code_block import PyCodeBlock
from codegen.sdk.python.detached_symbols.decorator import PyDecorator
from codegen.sdk.python.statements.comment import PyComment, PyCommentType
from codegen.sdk.python.symbol_groups.comment_group import PyCommentGroup
from codegen.sdk.shared.decorators.docs import py_apidoc


@py_apidoc
class PyHasBlock(HasBlock[PyCodeBlock, PyDecorator]):
    """Extends HasBlock for Python codebases."""

    @property
    @reader
    def is_decorated(self) -> bool:
        """Returns whether the symbol is decorated with decorators.

        Checks if the symbol has a parent and if that parent's type is a decorated definition.

        Returns:
            bool: True if the symbol has decorators, False otherwise.
        """
        if self.parent is None:
            return False
        return self.ts_node.parent.type == "decorated_definition"

    @property
    @reader
    def decorators(self) -> list[PyDecorator]:
        """Returns a list of decorators associated with this symbol.

        Retrieves all decorator nodes from the symbol's parent TreeSitter node and converts them into PyDecorator objects.

        Args:
            None

        Returns:
            list[PyDecorator]: A list of PyDecorator objects representing the decorators on the symbol. Returns an empty list if the symbol is not decorated.

        Note:
            This property should be used in conjunction with is_decorated to check if the symbol has any decorators.
        """
        if self.is_decorated:
            decorators = [x for x in self.ts_node.parent.children if x.type == "decorator"]
            return [PyDecorator(x, self) for x in decorators]
        return []

    @cached_property
    @reader
    def docstring(self) -> PyCommentGroup | None:
        """Gets the function's docstring.

        Retrieves the docstring of the function as a PyCommentGroup object. If the function has no docstring, returns None.

        Returns:
            PyCommentGroup | None: The docstring of the function as a PyCommentGroup, or None if no docstring exists.
        """
        return PyCommentGroup.from_docstring(self)

    @writer
    def set_docstring(self, docstring: str, auto_format: bool = True, clean_format: bool = True, force_multiline: bool = False) -> None:
        """Sets or updates a docstring for a Python function or class.

        Updates the existing docstring if one exists, otherwise creates a new docstring. The docstring can be automatically formatted and cleaned before being set.

        Args:
            docstring (str): The docstring content to set.
            auto_format (bool, optional): Whether to format the text into a proper docstring format. Defaults to True.
            clean_format (bool, optional): Whether to clean and normalize the docstring format before insertion. Defaults to True.
            force_multiline (bool, optional): Whether to force single-line comments to be converted to multi-line format. Defaults to False.

        Returns:
            None
        """
        # Clean the docstring if needed
        if clean_format:
            docstring = PyComment.clean_comment(docstring)

        # Add the docstring to the function
        if self.docstring:
            if auto_format:
                self.docstring.edit_text(docstring)
            else:
                self.docstring.edit(docstring)
        else:
            if auto_format:
                docstring = PyComment.generate_comment(docstring, PyCommentType.MULTI_LINE_DOUBLE_QUOTE, force_multiline=force_multiline)
            self.code_block.insert_before(docstring)
