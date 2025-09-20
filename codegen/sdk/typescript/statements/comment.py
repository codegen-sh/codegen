from __future__ import annotations

from enum import StrEnum

from codegen.sdk.core.autocommit import commiter, reader
from codegen.sdk.core.statements.comment import Comment, lowest_indentation
from codegen.sdk.shared.decorators.docs import noapidoc, ts_apidoc


@ts_apidoc
class TSCommentType(StrEnum):
    """An enumeration representing different types of comments in TypeScript.

    Represents the possible types of comments that can be used in TypeScript code,
    including double slash comments (//), slash star comments (/* */), and unknown
    comment types.

    Attributes:
        DOUBLE_SLASH (str): Represents a single-line comment starting with //.
        SLASH_STAR (str): Represents a multi-line comment enclosed in /* */.
        UNKNOWN (str): Represents an unknown or unrecognized comment type.
    """

    DOUBLE_SLASH = "DOUBLE_SLASH"
    SLASH_STAR = "SLASH_STAR"
    UNKNOWN = "UNKNOWN"


@ts_apidoc
class TSComment(Comment):
    """Abstract representation of typescript comments"""

    @property
    @reader
    def comment_type(self) -> TSCommentType:
        """Determines the type of comment in a TypeScript source code.

        Parses the comment markers to determine if it's a single-line comment (//) or a multi-line comment (/* */). If no known comment markers are found, returns UNKNOWN.

        Args:
            self: The TSComment instance.

        Returns:
            TSCommentType: The type of the comment. Can be DOUBLE_SLASH for single-line comments,
                SLASH_STAR for multi-line comments, or UNKNOWN if no known comment markers are found.
        """
        if self.source.startswith("//"):
            return TSCommentType.DOUBLE_SLASH
        elif self.source.startswith("/*"):
            return TSCommentType.SLASH_STAR
        return TSCommentType.UNKNOWN

    @noapidoc
    @commiter
    def _parse_comment(self) -> str:
        """Parse out the comment into its text content"""
        # Remove comment markers
        if self.comment_type == TSCommentType.DOUBLE_SLASH:
            if self.source.startswith("// "):
                return self.source[3:]
            elif self.source.startswith("//"):
                return self.source[2:]
            else:
                return self.source
        elif self.comment_type == TSCommentType.SLASH_STAR:
            formatted_text = self.source
            # Remove comment markers
            if self.source.startswith("/** "):
                formatted_text = self.source[4:]
            elif self.source.startswith("/**"):
                formatted_text = self.source[3:]
            elif self.source.startswith("/* "):
                formatted_text = self.source[3:]
            elif self.source.startswith("/*"):
                formatted_text = self.source[2:]
            if formatted_text.endswith(" */"):
                formatted_text = formatted_text[:-3]
            elif formatted_text.endswith("*/"):
                formatted_text = formatted_text[:-2]
            formatted_text = formatted_text.strip("\n")
            formatted_split = formatted_text.split("\n")
            # Get indentation level
            padding = lowest_indentation(formatted_split)
            # Remove indentation
            formatted_text = "\n".join([line[padding:] for line in formatted_split])
            # Remove leading "* " from each line
            text_lines = []
            for line in formatted_text.split("\n"):
                if line.lstrip().startswith("* "):
                    text_lines.append(line.lstrip()[2:])
                elif line.lstrip().startswith("*"):
                    text_lines.append(line.lstrip()[1:])
                else:
                    text_lines.append(line)
            return "\n".join(text_lines).rstrip()
        else:
            # Return the source if the comment type is unknown
            return self.source

    @noapidoc
    @reader
    def _unparse_comment(self, new_src: str):
        """Unparses cleaned text content into a comment block"""
        should_add_leading_star = any([line.lstrip().startswith("*") for line in self.source.split("\n")[:-1]]) if len(self.source.split("\n")) > 1 else True
        return self.generate_comment(new_src, self.comment_type, leading_star=should_add_leading_star)

    @staticmethod
    def generate_comment(new_src: str, comment_type: TSCommentType, leading_star: bool = True, force_multiline: bool = False) -> str:
        """Generates a TypeScript comment block from the given text content.

        Creates a comment block in either single-line (//) or multi-line (/* */) format based on the specified comment type.

        Args:
            new_src (str): The text content to be converted into a comment.
            comment_type (TSCommentType): The type of comment to generate (DOUBLE_SLASH or SLASH_STAR).
            leading_star (bool, optional): Whether to add leading "*" to each line in multi-line comments. Defaults to True.
            force_multiline (bool, optional): Whether to force multi-line format for single-line content. Defaults to False.

        Returns:
            str: The formatted comment block as a string.
        """
        # Generate the comment block based on the comment type
        if comment_type == TSCommentType.DOUBLE_SLASH:
            # Add the comment character to each line
            new_src = "\n".join([f"// {line}" for line in new_src.split("\n")])
        elif comment_type == TSCommentType.SLASH_STAR:
            # Add triple quotes to the text
            if "\n" in new_src or force_multiline:
                # Check if we should add leading "* " to each line
                if leading_star:
                    new_src = "\n".join([(" * " + x).rstrip() for x in new_src.split("\n")])
                    new_src = "/**\n" + new_src + "\n */"
                else:
                    new_src = "/*\n" + new_src + "\n*/"
            else:
                new_src = "/* " + new_src + " */"
        return new_src

    @staticmethod
    def clean_comment(comment: str) -> str:
        """Cleans comment markers and whitespace from a comment string.

        Removes various types of comment markers ('/', '/*', '/**', '*/') and trims whitespace
        from the beginning and end of the comment text.

        Args:
            comment (str): The raw comment string to be cleaned.

        Returns:
            str: The cleaned comment text with comment markers and excess whitespace removed.
        """
        comment = comment.lstrip()
        if comment.startswith("//"):
            comment = comment[2:]
        if comment.startswith("/**"):
            comment = comment[3:]
        if comment.startswith("/*"):
            comment = comment[2:]
        if comment.endswith("*/"):
            comment = comment[:-2]
        return comment.strip()
