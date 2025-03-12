from __future__ import annotations

from typing import TYPE_CHECKING, Self, Unpack

from codegen.sdk.core.autocommit import reader, writer
from codegen.sdk.core.symbol import Symbol
from codegen.sdk.enums import ImportType
from codegen.sdk.python.statements.comment import PyComment, PyCommentType
from codegen.sdk.python.symbol_groups.comment_group import PyCommentGroup
from codegen.shared.decorators.docs import noapidoc, py_apidoc

if TYPE_CHECKING:
    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.codebase.flagging.code_flag import CodeFlag
    from codegen.sdk.codebase.flagging.enums import FlagKwargs
    from codegen.sdk.core.interfaces.has_block import HasBlock
    from codegen.sdk.core.node_id_factory import NodeId
    from codegen.sdk.python.detached_symbols.code_block import PyCodeBlock
    from codegen.sdk.python.interfaces.has_block import PyHasBlock


@py_apidoc
class PySymbol(Symbol["PyHasBlock", "PyCodeBlock"]):
    """Extends `Symbol` for Python codebases."""

    @classmethod
    @noapidoc
    def from_decorated_definition(cls, ts_node: TSNode, file_id: NodeId, ctx: CodebaseContext, parent: HasBlock) -> Symbol:
        definition = ts_node.child_by_field_name("definition")
        return ctx.parser.parse_expression(definition, file_id, ctx, parent, decorated_node=ts_node)

    @property
    @reader
    def is_exported(self) -> bool:
        """Indicates whether a Python symbol is exported.

        In Python, all symbols are exported by default, so this property always returns True.

        Returns:
            bool: Always True, as Python symbols are exported by default.
        """
        return True

    @reader
    def get_import_string(
        self,
        alias: str | None = None,
        module: str | None = None,
        import_type: ImportType = ImportType.UNKNOWN,
        is_type_import: bool = False,
    ) -> str:
        """Generates an import string for a Python symbol.

        Returns a string representation of how to import this symbol, with support for different import types and aliasing.

        Args:
            alias (str | None): Optional alias name for the import. If provided and different from symbol name, creates aliased import.
            module (str | None): Optional module name to import from. If not provided, uses the symbol's file's module name.
            import_type (ImportType): Type of import to generate. If WILDCARD, generates star import. Defaults to UNKNOWN.
            is_type_import (bool): Whether this is a type import. Currently unused. Defaults to False.

        Returns:
            str: The formatted import string. Will be one of:
                - "from {module} import * as {file_name}" (for WILDCARD imports)
                - "from {module} import {name} as {alias}" (for aliased imports)
                - "from {module} import {name}" (for standard imports)
        """
        import_module = module if module is not None else self.file.import_module_name
        if import_type == ImportType.WILDCARD:
            file_as_module = self.file.name
            return f"from {import_module} import * as {file_as_module}"
        elif alias is not None and alias != self.name:
            return f"from {import_module} import {self.name} as {alias}"
        else:
            return f"from {import_module} import {self.name}"

    @property
    @reader
    def comment(self) -> PyCommentGroup | None:
        """Retrieves the comment group associated with a Python symbol.

        A read-only property that returns the non-inline comment group (if any) that is associated with this symbol.
        Comments are considered associated with a symbol if they appear immediately before the symbol's definition.

        Returns:
            PyCommentGroup | None: A comment group object containing the symbol's comments, or None if no comments exist.
        """
        return PyCommentGroup.from_symbol_comments(self)

    @property
    @reader
    def inline_comment(self) -> PyCommentGroup | None:
        """Returns the inline comment group associated with this symbol.

        Retrieves any inline comments attached to this symbol. An inline comment appears on the same line as the code it comments on.

        Args:
            self (PySymbol): The Python symbol to check for inline comments.

        Returns:
            PyCommentGroup | None: A comment group containing the inline comments if they exist, None otherwise.
        """
        return PyCommentGroup.from_symbol_inline_comments(self)

    @writer
    def set_comment(self, comment: str, auto_format: bool = True, clean_format: bool = True, comment_type: PyCommentType = PyCommentType.SINGLE_LINE) -> None:
        """Sets a comment for the Python symbol.

        Adds or modifies a comment associated with the Python symbol. If a comment already exists,
        it will be edited. If no comment exists, a new comment group will be created.

        Args:
            comment (str): The comment text to be added or set.
            auto_format (bool, optional): If True, automatically formats the text as a comment.
                Defaults to True.
            clean_format (bool, optional): If True, cleans the format of the comment before
                inserting. Defaults to True.
            comment_type (PyCommentType, optional): Type of comment to add (e.g., single line,
                multi line). Defaults to PyCommentType.SINGLE_LINE.

        Returns:
            None: This method modifies the symbol's comment in place.
        """
        if clean_format:
            comment = PyComment.clean_comment(comment)

        # If comment already exists, add the comment to the existing comment group
        if self.comment:
            if auto_format:
                self.comment.edit_text(comment)
            else:
                self.comment.edit(comment, fix_indentation=True)
        else:
            if auto_format:
                comment = PyComment.generate_comment(comment, comment_type)
            self.insert_before(comment, fix_indentation=True)

    @writer
    def add_comment(self, comment: str, auto_format: bool = True, clean_format: bool = True, comment_type: PyCommentType = PyCommentType.SINGLE_LINE) -> None:
        """Adds a new comment to the symbol.

        Appends a comment to the symbol either adding it to an existing comment group or creating a new one.

        Args:
            comment (str): The comment text to be added.
            auto_format (bool): Whether to automatically format the text into a proper comment format.
                Defaults to True.
            clean_format (bool): Whether to clean and normalize the comment text before adding.
                Defaults to True.
            comment_type (PyCommentType): The style of comment to add (e.g., single-line, multi-line).
                Defaults to PyCommentType.SINGLE_LINE.

        Returns:
            None

        Raises:
            None
        """
        if clean_format:
            comment = PyComment.clean_comment(comment)
        if auto_format:
            comment = PyComment.generate_comment(comment, comment_type)

        # If comment already exists, add the comment to the existing comment group
        if self.comment:
            self.comment.insert_after(comment, fix_indentation=True)
        else:
            self.insert_before(comment, fix_indentation=True)

    @writer
    def set_inline_comment(self, comment: str, auto_format: bool = True, clean_format: bool = True) -> None:
        """Sets an inline comment to the symbol.

        Adds or replaces an inline comment for a Python symbol. If an inline comment exists,
        it will be replaced with the new comment. If no inline comment exists, a new one
        will be created at the end of the line.

        Args:
            comment (str): The inline comment text to add.
            auto_format (bool, optional): If True, formats the text into a proper inline
                comment with appropriate prefixes and spacing. Defaults to True.
            clean_format (bool, optional): If True, cleans the comment text before insertion
                by removing extra whitespace and comment markers. Defaults to True.

        Returns:
            None
        """
        if clean_format:
            comment = PyComment.clean_comment(comment)

        if self.comment:
            if auto_format:
                self.comment.edit_text(comment)
            else:
                self.comment.edit(comment)
        else:
            if auto_format:
                comment = "  " + PyComment.generate_comment(comment, PyCommentType.SINGLE_LINE)
            self.insert_after(comment, fix_indentation=False, newline=False)

    @writer
    def flag(self, **kwargs: Unpack[FlagKwargs]) -> CodeFlag[Self]:
        """Flags a Python symbol by adding a flag comment and returning a CodeFlag.

        This implementation first creates the CodeFlag through the standard flagging system,
        then adds a Python-specific comment to visually mark the flagged code.

        Args:
            **kwargs: Flag keyword arguments including optional 'message'

        Returns:
            CodeFlag[Self]: The code flag object for tracking purposes
        """
        # First create the standard CodeFlag through the base implementation
        code_flag = super().flag(**kwargs)

        # Add a Python comment to visually mark the flag
        message = kwargs.get("message", "")
        if message:
            self.set_inline_comment(f"🚩 {message}")

        return code_flag
