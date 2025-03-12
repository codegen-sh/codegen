from __future__ import annotations

import re
from typing import TYPE_CHECKING

from docstring_parser import Docstring, DocstringStyle, parse

from codegen.sdk.core.autocommit import reader
from codegen.sdk.core.statements.statement import StatementType
from codegen.sdk.core.symbol_groups.comment_group import CommentGroup
from codegen.sdk.enums import SymbolType
from codegen.sdk.python.statements.comment import PyComment
from codegen.shared.decorators.docs import noapidoc, py_apidoc

if TYPE_CHECKING:
    from tree_sitter import Node as TSNode

    from codegen.sdk.python.function import PyFunction
    from codegen.sdk.python.symbol import PySymbol


@py_apidoc
class PyCommentGroup(CommentGroup):
    """A group of related symbols that represent a comment or docstring in Python

    For example:
    ```
    # Comment 1
    # Comment 2
    # Comment 3
    ```
    would be 3 individual comments (accessible via `symbols`), but together they form a `CommentGroup` (accessible via `self`).
    """

    _text: str  # Actual text content of the comment

    @classmethod
    @noapidoc
    def from_symbol_comments(cls, symbol: PySymbol):
        siblings = symbol.parent.parent.statements
        comments = []
        # Iterate backwards from the function node to collect all preceding comment nodes
        for i in range(symbol.parent.index - 1, -1, -1):
            if siblings[i].statement_type == StatementType.COMMENT:
                # Check if the comment is directly above each other
                if siblings[i].end_point[0] == siblings[i + 1].start_point[0] - 1:
                    comments.insert(0, siblings[i])
                else:
                    break  # Stop if there is a break in the comments
            else:
                break  # Stop if a non-comment node is encountered

        from codegen.sdk.python.class_definition import PyClass

        # Check if the function node is a method
        if symbol.symbol_type == SymbolType.Function:
            if isinstance(symbol.parent_class, PyClass):
                # Filter out the class docstring if it exists
                if symbol.parent_class.docstring:
                    docstring_comments = set(symbol.parent_class.docstring.symbols)
                    comments = [c for c in comments if c not in docstring_comments]

        if not comments:
            return None

        return cls(comments, symbol.file_node_id, symbol.ctx, symbol)

    @classmethod
    @noapidoc
    def from_symbol_inline_comments(cls, symbol: PySymbol, node: TSNode | None = None):
        statement = symbol.parent
        index = statement.index
        siblings = statement.parent.statements
        comment_nodes = []
        # Check if there are any comments after the function node
        if index + 1 < len(siblings):
            if siblings[index + 1].statement_type == StatementType.COMMENT:
                # Check if the comment is on the same line
                if siblings[index].end_point[0] == siblings[index + 1].start_point[0]:
                    comment_nodes.append(siblings[index + 1])

        if not comment_nodes:
            return None

        return cls(comment_nodes, symbol.file_node_id, symbol.ctx, symbol)

    @classmethod
    @noapidoc
    def from_docstring(cls, symbol: PySymbol):
        # Check if there is an expression node above the symbol
        top_child = symbol.code_block.ts_node.children[0]
        if top_child.type == "expression_statement":
            string_node = top_child.children[0]
            if string_node.type == "string":
                text = string_node.text.decode("utf-8")
                comment_node = PyComment.from_code_block(string_node, symbol)
                return cls([comment_node], symbol.file_node_id, symbol.ctx, symbol)
        return None

    def to_google_docstring(self, function: PyFunction) -> str:  # pragma: no cover
        """Convert a comment group into a Google-style docstring.

        Processes the text content of the comment group and converts it into a properly formatted Google-style docstring,
        incorporating existing function signature information and merging any existing docstring content with the new format.

        Args:
            function (PyFunction): The Python function whose signature will be used to extract parameter and return type information.

        Returns:
            str: A formatted Google-style docstring string that includes the function's description, parameters, and return value information.
        """
        NAME_OF_PARAMETERS_SECTION = "Parameters:"
        NAME_OF_ARGS_SECTION = "Args:"
        NAME_OF_RETURNS_SECTION = "Returns:"

        def parse_google_block(section_header: str, first_line: str, docstring_iter) -> str:
            """Parse the parameters section of the docstring"""
            unrelated_strings = []
            parameters = {}

            # Catch edge case where there is content in the first line
            if first_line_formatted := first_line.replace(section_header, "").strip():
                unrelated_strings.append(first_line_formatted)

            param_pattern = re.compile(r"^\s*(\w+)(\s+\([^)]+\))?:\s*(.+)$")

            while line := next(docstring_iter, None):
                match = param_pattern.match(line)
                if match:
                    param_name = match.group(1)
                    param_type = match.group(2).strip("() ") if match.group(2) else None
                    description = match.group(3).strip()
                    parameters[param_name] = (param_type, description)
                else:
                    unrelated_strings.append(line.strip())

            return unrelated_strings, parameters

        def merge_codebase_docstring(codebase_doc, parsed_doc):
            """Merge the codebase docstring with the parsed docstring"""
            for param_name, (param_type, param_description) in codebase_doc.items():
                if param_name in parsed_doc:
                    # Merge the types and descriptions
                    parsed_type, parsed_description = parsed_doc[param_name]
                    if not param_type:
                        param_type = parsed_type
                    if not param_description:
                        param_description = parsed_description
                    # Update the codebase docstring
                    codebase_doc[param_name] = (param_type, param_description)
            return codebase_doc

        # Build the new docstring
        new_docstring = ""
        # Parse the docstring
        parsed_parameters_unrelated_strings, parsed_parameters = [], {}
        parsed_args_unrelated_strings, parsed_args = [], {}
        parsed_returns_unrelated_strings, parsed_returns = [], {}

        # Iterate over the docstring
        docstring_iter = iter(self.text.split("\n"))
        while (line := next(docstring_iter, None)) is not None:
            # Check if the line is a section header
            if line.strip().lower().startswith(NAME_OF_PARAMETERS_SECTION.lower()):
                parsed_parameters_unrelated_strings, parsed_parameters = parse_google_block(NAME_OF_PARAMETERS_SECTION, line, docstring_iter)
            elif line.strip().lower().startswith(NAME_OF_ARGS_SECTION.lower()):
                parsed_args_unrelated_strings, parsed_args = parse_google_block(NAME_OF_ARGS_SECTION, line, docstring_iter)
            elif line.strip().lower().startswith(NAME_OF_RETURNS_SECTION.lower()):
                parsed_returns_unrelated_strings, parsed_returns = parse_google_block(NAME_OF_RETURNS_SECTION, line, docstring_iter)
            else:
                # Add the line to the new docstring
                new_docstring += line + "\n"

        # Remove extra newlines
        new_docstring = new_docstring.rstrip()

        # Merge parameters and args together
        parsed_args_unrelated_strings += parsed_parameters_unrelated_strings
        parsed_args.update(parsed_parameters)

        # Create args section
        if (args := [param for param in function.parameters if param.name != "self"]) or parsed_args_unrelated_strings or parsed_args:
            args_doc = {param.name: (param.type, None) for param in args}
            # Merge codebase args with parsed parameters
            args_doc = merge_codebase_docstring(args_doc, parsed_args)

            new_docstring += f"\n\n{NAME_OF_ARGS_SECTION}\n"
            # Generate and add the args section
            if args_doc:
                for arg_name, (arg_type, arg_description) in args_doc.items():
                    # Add the arg to the docstring
                    # Add Padding and name
                    new_docstring += f"    {arg_name}"
                    # Add type if it exists
                    if arg_type:
                        new_docstring += f" ({arg_type})"
                    # Add description if it exists
                    if arg_description:
                        new_docstring += f": {arg_description}"
                    # Add newline
                    new_docstring += "\n"
                # Add a newline if there are unrelated strings
                if parsed_args_unrelated_strings:
                    new_docstring += "\n"
            # Add the unrelated strings
            if parsed_args_unrelated_strings:
                for unrelated_string in parsed_args_unrelated_strings:
                    new_docstring += f"    {unrelated_string}\n"

        # Create returns section
        if ((return_type := function.return_type) and return_type.source != "None") or parsed_returns_unrelated_strings or parsed_returns:
            new_docstring += f"\n{NAME_OF_RETURNS_SECTION}\n"

            # Merge codebase return type with parsed return type
            if (return_type := function.return_type) and return_type.source != "None":
                ret_doc = {return_type: (None, None)}
                ret_doc = merge_codebase_docstring(ret_doc, parsed_returns)
            else:
                ret_doc = parsed_returns

            # Generate and add the returns section
            if ret_doc:
                ret_name, (ret_type, ret_description) = next(iter(ret_doc.items()))
                # Edge case: If there is no description, and parsed_returns_unrelated_strings is one line, add it to the description
                if not ret_description and len(parsed_returns_unrelated_strings) == 1:
                    ret_description = parsed_returns_unrelated_strings.pop()

                # Add the return to the docstring
                # Add Padding and name
                new_docstring += f"    {ret_name}"
                # Add description if it exists
                if ret_description:
                    new_docstring += f": {ret_description}"
                # Add newline
                new_docstring += "\n"

                # Add a newline if there are unrelated strings
                if parsed_returns_unrelated_strings:
                    new_docstring += "\n"
            # Add the unrelated strings
            if parsed_returns_unrelated_strings:
                for unrelated_string in parsed_returns_unrelated_strings:
                    new_docstring += f"    {unrelated_string}\n"

        return new_docstring

    @noapidoc
    @reader
    def parse(self) -> Docstring:
        return parse(self.source, style=DocstringStyle.GOOGLE)
