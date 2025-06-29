"""Markdown to ADF (Atlassian Document Format) Adapter

This module provides the main adapter class for converting Markdown text to ADF format.
"""

import re
from typing import Optional
from xml.etree.ElementTree import Element

from markdown import Markdown

try:
    from .adf_types import (
        ADFCodeBlockNode,
        ADFDocument,
        ADFHeadingNode,
        ADFListItemNode,
        ADFListNode,
        ADFMark,
        ADFMarkType,
        ADFNode,
        ADFNodeType,
        ADFParagraphNode,
        ADFTextNode,
    )
except ImportError:
    # Fallback for direct execution
    from adf_types import (
        ADFCodeBlockNode,
        ADFDocument,
        ADFHeadingNode,
        ADFListItemNode,
        ADFListNode,
        ADFMark,
        ADFMarkType,
        ADFNode,
        ADFNodeType,
        ADFParagraphNode,
        ADFTextNode,
    )


class MarkdownToADFAdapter:
    r"""Converts Markdown text to Atlassian Document Format (ADF).

    This adapter parses Markdown using Python's markdown library and converts
    the resulting HTML/XML tree to ADF JSON structure.

    Example:
        adapter = MarkdownToADFAdapter()
        adf_doc = adapter.convert("# Hello World\\n\\nThis is **bold** text.")
    """

    def __init__(self):
        """Initialize the adapter with markdown parser."""
        self.md = Markdown(
            extensions=[
                "fenced_code",
                "codehilite",
                "tables",
                "nl2br",
            ],
            extension_configs={
                "codehilite": {
                    "use_pygments": False,
                    "noclasses": True,
                }
            },
        )

    def convert(self, markdown_text: str) -> ADFDocument:
        """Convert markdown text to ADF document.

        Args:
            markdown_text: The markdown text to convert

        Returns:
            ADFDocument: The converted ADF document structure
        """
        # Parse markdown to HTML/XML tree
        html = self.md.convert(markdown_text)

        # Parse the HTML back to XML tree for processing
        from xml.etree.ElementTree import fromstring

        # Wrap in a root element to handle multiple top-level elements
        wrapped_html = f"<root>{html}</root>"
        try:
            root = fromstring(wrapped_html)
        except Exception as e:
            # Fallback for malformed HTML - create a simple paragraph
            return self._create_document([self._create_paragraph([self._create_text(markdown_text)])])

        # Convert XML tree to ADF nodes
        content_nodes = []
        for child in root:
            node = self._convert_element_to_adf(child)
            if node:
                content_nodes.append(node)

        # If no content was generated, create a simple paragraph
        if not content_nodes:
            content_nodes = [self._create_paragraph([self._create_text(markdown_text or "")])]

        return self._create_document(content_nodes)

    def _create_document(self, content: list[ADFNode]) -> ADFDocument:
        """Create an ADF document with the given content."""
        return {"version": 1, "type": ADFNodeType.DOC, "content": content}

    def _convert_element_to_adf(self, element: Element) -> Optional[ADFNode]:
        """Convert an XML element to an ADF node."""
        tag = element.tag.lower()

        if tag == "p":
            return self._convert_paragraph(element)
        elif tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            return self._convert_heading(element, int(tag[1]))
        elif tag == "pre":
            return self._convert_code_block(element)
        elif tag == "code" and element.getparent() is not None and element.getparent().tag != "pre":
            # Inline code - this should be handled as a mark, not a separate node
            return None
        elif tag == "ul":
            return self._convert_bullet_list(element)
        elif tag == "ol":
            return self._convert_ordered_list(element)
        elif tag == "li":
            return self._convert_list_item(element)
        elif tag == "blockquote":
            return self._convert_blockquote(element)
        elif tag == "hr":
            return self._create_rule()
        elif tag == "br":
            return self._create_hard_break()
        else:
            # For unknown elements, try to extract text content
            text_content = self._extract_text_with_marks(element)
            if text_content:
                return self._create_paragraph(text_content)
            return None

    def _convert_paragraph(self, element: Element) -> ADFParagraphNode:
        """Convert a paragraph element to ADF paragraph node."""
        content = self._extract_text_with_marks(element)
        return self._create_paragraph(content)

    def _convert_heading(self, element: Element, level: int) -> ADFHeadingNode:
        """Convert a heading element to ADF heading node."""
        content = self._extract_text_with_marks(element)
        return {"type": ADFNodeType.HEADING, "attrs": {"level": level}, "content": content}

    def _convert_code_block(self, element: Element) -> ADFCodeBlockNode:
        """Convert a code block element to ADF code block node."""
        # Extract language from class attribute if present
        language = None
        code_element = element.find(".//code")
        if code_element is not None:
            class_attr = code_element.get("class", "")
            if class_attr:
                # Extract language from class like "language-python" or "python"
                lang_match = re.search(r"(?:language-)?([a-zA-Z0-9_+-]+)", class_attr)
                if lang_match:
                    language = lang_match.group(1)

        # Get the text content
        text_content = element.text or ""
        if code_element is not None:
            text_content = code_element.text or ""

        # Clean up the text content
        text_content = text_content.strip()

        node: ADFCodeBlockNode = {"type": ADFNodeType.CODE_BLOCK, "content": [self._create_text(text_content)]}

        if language:
            node["attrs"] = {"language": language}

        return node

    def _convert_bullet_list(self, element: Element) -> ADFListNode:
        """Convert a bullet list element to ADF bullet list node."""
        content = []
        for li in element.findall("li"):
            list_item = self._convert_list_item(li)
            if list_item:
                content.append(list_item)

        return {"type": ADFNodeType.BULLET_LIST, "content": content}

    def _convert_ordered_list(self, element: Element) -> ADFListNode:
        """Convert an ordered list element to ADF ordered list node."""
        content = []
        for li in element.findall("li"):
            list_item = self._convert_list_item(li)
            if list_item:
                content.append(list_item)

        return {"type": ADFNodeType.ORDERED_LIST, "content": content}

    def _convert_list_item(self, element: Element) -> ADFListItemNode:
        """Convert a list item element to ADF list item node."""
        content = []

        # Process child elements
        for child in element:
            child_node = self._convert_element_to_adf(child)
            if child_node:
                content.append(child_node)

        # If no child elements, create a paragraph with the text content
        if not content:
            text_content = self._extract_text_with_marks(element)
            if text_content:
                content = [self._create_paragraph(text_content)]

        return {"type": ADFNodeType.LIST_ITEM, "content": content}

    def _convert_blockquote(self, element: Element) -> ADFNode:
        """Convert a blockquote element to ADF blockquote node."""
        content = []
        for child in element:
            child_node = self._convert_element_to_adf(child)
            if child_node:
                content.append(child_node)

        # If no child elements, create a paragraph with the text content
        if not content:
            text_content = self._extract_text_with_marks(element)
            if text_content:
                content = [self._create_paragraph(text_content)]

        return {"type": ADFNodeType.BLOCKQUOTE, "content": content}

    def _extract_text_with_marks(self, element: Element) -> list[ADFNode]:
        """Extract text content with inline formatting marks."""
        result = []

        # Handle text before first child
        if element.text:
            result.append(self._create_text(element.text))

        # Process child elements
        for child in element:
            if child.tag.lower() in ["strong", "b"]:
                # Bold text
                child_text = self._get_element_text(child)
                if child_text:
                    result.append(self._create_text(child_text, [self._create_strong_mark()]))
            elif child.tag.lower() in ["em", "i"]:
                # Italic text
                child_text = self._get_element_text(child)
                if child_text:
                    result.append(self._create_text(child_text, [self._create_em_mark()]))
            elif child.tag.lower() == "code":
                # Inline code
                child_text = self._get_element_text(child)
                if child_text:
                    result.append(self._create_text(child_text, [self._create_code_mark()]))
            elif child.tag.lower() == "a":
                # Link
                href = child.get("href", "")
                child_text = self._get_element_text(child)
                if child_text and href:
                    result.append(self._create_text(child_text, [self._create_link_mark(href)]))
                elif child_text:
                    result.append(self._create_text(child_text))
            elif child.tag.lower() in ["del", "s", "strike"]:
                # Strikethrough
                child_text = self._get_element_text(child)
                if child_text:
                    result.append(self._create_text(child_text, [self._create_strike_mark()]))
            else:
                # For other elements, just extract text
                child_text = self._get_element_text(child)
                if child_text:
                    result.append(self._create_text(child_text))

            # Handle tail text after child element
            if child.tail:
                result.append(self._create_text(child.tail))

        # If no content was extracted, create empty text node
        if not result:
            result = [self._create_text("")]

        return result

    def _get_element_text(self, element: Element) -> str:
        """Get all text content from an element and its children."""
        text_parts = []
        if element.text:
            text_parts.append(element.text)
        for child in element:
            text_parts.append(self._get_element_text(child))
            if child.tail:
                text_parts.append(child.tail)
        return "".join(text_parts)

    def _create_paragraph(self, content: list[ADFNode]) -> ADFParagraphNode:
        """Create an ADF paragraph node."""
        return {"type": ADFNodeType.PARAGRAPH, "content": content}

    def _create_text(self, text: str, marks: Optional[list[ADFMark]] = None) -> ADFTextNode:
        """Create an ADF text node."""
        node: ADFTextNode = {"type": ADFNodeType.TEXT, "text": text}
        if marks:
            node["marks"] = marks
        return node

    def _create_rule(self) -> ADFNode:
        """Create an ADF rule (horizontal line) node."""
        return {"type": ADFNodeType.RULE}

    def _create_hard_break(self) -> ADFNode:
        """Create an ADF hard break node."""
        return {"type": ADFNodeType.HARD_BREAK}

    def _create_strong_mark(self) -> ADFMark:
        """Create a strong (bold) mark."""
        return {"type": ADFMarkType.STRONG}

    def _create_em_mark(self) -> ADFMark:
        """Create an emphasis (italic) mark."""
        return {"type": ADFMarkType.EM}

    def _create_code_mark(self) -> ADFMark:
        """Create a code mark."""
        return {"type": ADFMarkType.CODE}

    def _create_link_mark(self, href: str) -> ADFMark:
        """Create a link mark."""
        return {"type": ADFMarkType.LINK, "attrs": {"href": href}}

    def _create_strike_mark(self) -> ADFMark:
        """Create a strikethrough mark."""
        return {"type": ADFMarkType.STRIKE}
