from __future__ import annotations

from enum import StrEnum

from codegen.sdk.core.autocommit import commiter, reader
from codegen.sdk.core.statements.comment import Comment, lowest_indentation
from codegen.sdk.shared.decorators.docs import noapidoc, py_apidoc


@py_apidoc
class PyCommentType(StrEnum):
    """Enum representing different types of comments.

    Attributes:
        SINGLE_LINE: Represents a single line comment.
        MULTI_LINE_QUOTE: Represents a multi-line comment using single quotes.
        MULTI_LINE_DOUBLE_QUOTE: Represents a multi-line comment using double quotes.
        UNKNOWN: Represents an unknown type of comment.
    """

    SINGLE_LINE = "SINGLE_LINE"
    MULTI_LINE_QUOTE = "MULTI_LINE_QUOTE"
    MULTI_LINE_DOUBLE_QUOTE = "MULTI_LINE_DOUBLE_QUOTE"
    UNKNOWN = "UNKNOWN"


@py_apidoc
class PyComment(Comment):
    """Abstract representation of python comments"""

    @property
    @reader
    def comment_type(self) -> PyCommentType:
        """Determines the type of Python comment based on its syntax.

        Parses the comment and determines its type based on the leading characters.
        For Python comments, it identifies if it is a single-line comment (#),
        a multi-line comment with single quotes ('''), or a multi-line comment with double quotes (\"\"\").

        Returns:
            PyCommentType: The type of comment, one of:
                - SINGLE_LINE: For comments starting with '#'
                - MULTI_LINE_QUOTE: For comments wrapped in '''
                - MULTI_LINE_DOUBLE_QUOTE: For comments wrapped in \"\"\"
                - UNKNOWN: If the comment type cannot be determined
        """
        if self.source.startswith("#"):
            return PyCommentType.SINGLE_LINE
        elif self.source.startswith("'''"):
            return PyCommentType.MULTI_LINE_QUOTE
        elif self.source.startswith('"""'):
            return PyCommentType.MULTI_LINE_DOUBLE_QUOTE
        return PyCommentType.UNKNOWN

    @property
    @reader
    def google_style(self) -> bool:
        """Determines if a Python docstring follows Google style formatting.

        Checks if a multi-line docstring follows Google style conventions by starting with descriptive text
        immediately after the opening quotes rather than on a new line.

        Returns:
            bool: True if the docstring follows Google style formatting, False otherwise.
        """
        if self.comment_type == PyCommentType.MULTI_LINE_QUOTE or self.comment_type == PyCommentType.MULTI_LINE_DOUBLE_QUOTE:
            return (self.source.startswith('"""') and not self.source.startswith('"""\n')) or (self.source.startswith("'''") and not self.source.startswith("'''\n"))
        return False

    @noapidoc
    @commiter
    def _parse_comment(self) -> str:
        """Parse out the comment block into its text content"""
        if self.comment_type == PyCommentType.SINGLE_LINE:
            if self.source.startswith("# "):
                return self.source[2:]
            elif self.source.startswith("#"):
                return self.source[1:]
            else:
                return self.source
        elif self.comment_type == PyCommentType.MULTI_LINE_QUOTE or self.comment_type == PyCommentType.MULTI_LINE_DOUBLE_QUOTE:
            # Handle edge case with google style docstrings
            skip_lines = 1 if self.google_style else 0
            # Remove the triple quotes and extract the text content
            text_block = self.source[3:-3]
            # Parse the text block into lines
            text_lines = []
            for line in text_block.lstrip("\n").split("\n"):
                text_lines.append(line)
            # Get indentation level
            padding = lowest_indentation(text_lines, skip_lines=skip_lines)
            # Remove indentation
            formatted_lines = text_lines[:skip_lines] + [line[padding:] for line in text_lines[skip_lines:]]
            return "\n".join(formatted_lines).rstrip()
        else:
            # Return the source if the comment type is unknown
            return self.source

    @noapidoc
    @reader
    def _unparse_comment(self, new_src: str):
        """Unparses cleaned text content into a comment block"""
        return self.generate_comment(new_src, self.comment_type, google_style=self.google_style)

    @staticmethod
    def generate_comment(new_src: str, comment_type: PyCommentType, force_multiline: bool = False, google_style: bool = True) -> str:
        """Converts text content into a Python comment block.

        Takes a string of text content and converts it into a Python comment block based on the specified comment type.
        Supports single-line comments and multi-line comments with either single or double quotes.

        Args:
            new_src (str): The text content to be converted into a comment.
            comment_type (PyCommentType): The type of comment to generate (SINGLE_LINE, MULTI_LINE_QUOTE, or MULTI_LINE_DOUBLE_QUOTE).
            force_multiline (bool, optional): When True, forces multi-line format even for single-line content. Defaults to False.
            google_style (bool, optional): When True, formats multi-line comments in Google style without newline after opening quotes. Defaults to True.

        Returns:
            str: The formatted comment block with appropriate comment syntax.
        """
        # Generate the comment block based on the comment type
        if comment_type.value == PyCommentType.SINGLE_LINE.value:
            # Add the comment character to each line
            new_src = "\n".join([f"# {line}" for line in new_src.split("\n")])
        elif comment_type.value == PyCommentType.MULTI_LINE_DOUBLE_QUOTE.value:
            # Add triple quotes to the text
            if "\n" in new_src or force_multiline:
                new_src = '"""' + ("" if google_style else "\n") + new_src + '\n"""'
            else:
                new_src = '"""' + new_src + '"""'
        elif comment_type.value == PyCommentType.MULTI_LINE_QUOTE.value:
            # Add triple quotes to the text
            if "\n" in new_src or force_multiline:
                new_src = "'''" + ("" if google_style else "\n") + new_src + "\n'''"
            else:
                new_src = "'''" + new_src + "'''"
        return new_src

    @staticmethod
    def clean_comment(comment: str) -> str:
        """Cleans a comment block by removing comment symbols, leading/trailing whitespace, and standardizing indentation.

        Takes a comment string and processes it to extract just the content by removing comment symbols (# or triple quotes),
        adjusting indentation, and stripping excess whitespace.

        Args:
            comment (str): The raw comment block to be cleaned. Can be a single-line comment or multi-line docstring.

        Returns:
            str: The cleaned comment text with comment symbols and excess whitespace removed.
        """
        # Remove leading whitespace
        indent = lowest_indentation(comment.split("\n"))
        comment = ("\n".join([line[indent:] for line in comment.split("\n")])).strip()

        if comment.startswith("#"):
            comment = comment[1:]
        if comment.startswith("'''") or comment.startswith('"""'):
            comment = comment[3:]
        if comment.endswith("'''") or comment.endswith('"""'):
            comment = comment[:-3]
        return comment.strip()
