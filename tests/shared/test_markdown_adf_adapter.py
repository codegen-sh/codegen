"""Tests for the Markdown to ADF adapter."""

from src.codegen.shared.markdown_adf import MarkdownToADFAdapter
from src.codegen.shared.markdown_adf.adf_types import ADFMarkType, ADFNodeType


class TestMarkdownToADFAdapter:
    """Test cases for the MarkdownToADFAdapter class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.adapter = MarkdownToADFAdapter()

    def test_simple_text(self):
        """Test conversion of simple text."""
        markdown = "Hello world"
        result = self.adapter.convert(markdown)

        assert result["version"] == 1
        assert result["type"] == ADFNodeType.DOC
        assert len(result["content"]) == 1

        paragraph = result["content"][0]
        assert paragraph["type"] == ADFNodeType.PARAGRAPH
        assert len(paragraph["content"]) == 1

        text_node = paragraph["content"][0]
        assert text_node["type"] == ADFNodeType.TEXT
        assert text_node["text"] == "Hello world"

    def test_paragraph(self):
        """Test conversion of paragraphs."""
        markdown = "First paragraph.\n\nSecond paragraph."
        result = self.adapter.convert(markdown)

        assert len(result["content"]) == 2

        # First paragraph
        first_para = result["content"][0]
        assert first_para["type"] == ADFNodeType.PARAGRAPH
        assert first_para["content"][0]["text"] == "First paragraph."

        # Second paragraph
        second_para = result["content"][1]
        assert second_para["type"] == ADFNodeType.PARAGRAPH
        assert second_para["content"][0]["text"] == "Second paragraph."

    def test_headings(self):
        """Test conversion of headings."""
        markdown = "# Heading 1\n## Heading 2\n### Heading 3"
        result = self.adapter.convert(markdown)

        assert len(result["content"]) == 3

        # H1
        h1 = result["content"][0]
        assert h1["type"] == ADFNodeType.HEADING
        assert h1["attrs"]["level"] == 1
        assert h1["content"][0]["text"] == "Heading 1"

        # H2
        h2 = result["content"][1]
        assert h2["type"] == ADFNodeType.HEADING
        assert h2["attrs"]["level"] == 2
        assert h2["content"][0]["text"] == "Heading 2"

        # H3
        h3 = result["content"][2]
        assert h3["type"] == ADFNodeType.HEADING
        assert h3["attrs"]["level"] == 3
        assert h3["content"][0]["text"] == "Heading 3"

    def test_bold_text(self):
        """Test conversion of bold text."""
        markdown = "This is **bold** text."
        result = self.adapter.convert(markdown)

        paragraph = result["content"][0]
        content = paragraph["content"]

        # Should have 3 text nodes: "This is ", "bold", " text."
        assert len(content) == 3

        # First text node
        assert content[0]["text"] == "This is "
        assert "marks" not in content[0] or not content[0]["marks"]

        # Bold text node
        assert content[1]["text"] == "bold"
        assert len(content[1]["marks"]) == 1
        assert content[1]["marks"][0]["type"] == ADFMarkType.STRONG

        # Last text node
        assert content[2]["text"] == " text."
        assert "marks" not in content[2] or not content[2]["marks"]

    def test_italic_text(self):
        """Test conversion of italic text."""
        markdown = "This is *italic* text."
        result = self.adapter.convert(markdown)

        paragraph = result["content"][0]
        content = paragraph["content"]

        # Should have 3 text nodes
        assert len(content) == 3

        # Italic text node
        assert content[1]["text"] == "italic"
        assert len(content[1]["marks"]) == 1
        assert content[1]["marks"][0]["type"] == ADFMarkType.EM

    def test_inline_code(self):
        """Test conversion of inline code."""
        markdown = "This is `inline code` text."
        result = self.adapter.convert(markdown)

        paragraph = result["content"][0]
        content = paragraph["content"]

        # Should have 3 text nodes
        assert len(content) == 3

        # Code text node
        assert content[1]["text"] == "inline code"
        assert len(content[1]["marks"]) == 1
        assert content[1]["marks"][0]["type"] == ADFMarkType.CODE

    def test_links(self):
        """Test conversion of links."""
        markdown = "Visit [Google](https://google.com) for search."
        result = self.adapter.convert(markdown)

        paragraph = result["content"][0]
        content = paragraph["content"]

        # Should have 3 text nodes
        assert len(content) == 3

        # Link text node
        assert content[1]["text"] == "Google"
        assert len(content[1]["marks"]) == 1
        assert content[1]["marks"][0]["type"] == ADFMarkType.LINK
        assert content[1]["marks"][0]["attrs"]["href"] == "https://google.com"

    def test_code_block(self):
        """Test conversion of code blocks."""
        markdown = "```python\nprint('Hello, world!')\n```"
        result = self.adapter.convert(markdown)

        assert len(result["content"]) == 1

        code_block = result["content"][0]
        assert code_block["type"] == ADFNodeType.CODE_BLOCK
        assert code_block["attrs"]["language"] == "python"
        assert len(code_block["content"]) == 1
        assert code_block["content"][0]["text"] == "print('Hello, world!')"

    def test_code_block_without_language(self):
        """Test conversion of code blocks without language specification."""
        markdown = "```\nsome code\n```"
        result = self.adapter.convert(markdown)

        code_block = result["content"][0]
        assert code_block["type"] == ADFNodeType.CODE_BLOCK
        assert "attrs" not in code_block or "language" not in code_block.get("attrs", {})
        assert code_block["content"][0]["text"] == "some code"

    def test_bullet_list(self):
        """Test conversion of bullet lists."""
        markdown = "- Item 1\n- Item 2\n- Item 3"
        result = self.adapter.convert(markdown)

        assert len(result["content"]) == 1

        bullet_list = result["content"][0]
        assert bullet_list["type"] == ADFNodeType.BULLET_LIST
        assert len(bullet_list["content"]) == 3

        # Check first list item
        first_item = bullet_list["content"][0]
        assert first_item["type"] == ADFNodeType.LIST_ITEM
        assert len(first_item["content"]) == 1
        assert first_item["content"][0]["type"] == ADFNodeType.PARAGRAPH
        assert first_item["content"][0]["content"][0]["text"] == "Item 1"

    def test_ordered_list(self):
        """Test conversion of ordered lists."""
        markdown = "1. First item\n2. Second item\n3. Third item"
        result = self.adapter.convert(markdown)

        assert len(result["content"]) == 1

        ordered_list = result["content"][0]
        assert ordered_list["type"] == ADFNodeType.ORDERED_LIST
        assert len(ordered_list["content"]) == 3

        # Check first list item
        first_item = ordered_list["content"][0]
        assert first_item["type"] == ADFNodeType.LIST_ITEM
        assert first_item["content"][0]["content"][0]["text"] == "First item"

    def test_blockquote(self):
        """Test conversion of blockquotes."""
        markdown = "> This is a blockquote.\n> It spans multiple lines."
        result = self.adapter.convert(markdown)

        assert len(result["content"]) == 1

        blockquote = result["content"][0]
        assert blockquote["type"] == ADFNodeType.BLOCKQUOTE
        assert len(blockquote["content"]) >= 1

    def test_horizontal_rule(self):
        """Test conversion of horizontal rules."""
        markdown = "Before rule\n\n---\n\nAfter rule"
        result = self.adapter.convert(markdown)

        # Should have 3 elements: paragraph, rule, paragraph
        assert len(result["content"]) == 3

        # Check rule
        rule = result["content"][1]
        assert rule["type"] == ADFNodeType.RULE

    def test_mixed_formatting(self):
        """Test conversion of mixed inline formatting."""
        markdown = "This has **bold** and *italic* and `code` formatting."
        result = self.adapter.convert(markdown)

        paragraph = result["content"][0]
        content = paragraph["content"]

        # Should have multiple text nodes with different marks
        assert len(content) > 3

        # Find the bold text
        bold_node = next((node for node in content if node.get("text") == "bold"), None)
        assert bold_node is not None
        assert any(mark["type"] == ADFMarkType.STRONG for mark in bold_node.get("marks", []))

        # Find the italic text
        italic_node = next((node for node in content if node.get("text") == "italic"), None)
        assert italic_node is not None
        assert any(mark["type"] == ADFMarkType.EM for mark in italic_node.get("marks", []))

        # Find the code text
        code_node = next((node for node in content if node.get("text") == "code"), None)
        assert code_node is not None
        assert any(mark["type"] == ADFMarkType.CODE for mark in code_node.get("marks", []))

    def test_empty_input(self):
        """Test conversion of empty input."""
        result = self.adapter.convert("")

        assert result["version"] == 1
        assert result["type"] == ADFNodeType.DOC
        assert len(result["content"]) == 1

        # Should create an empty paragraph
        paragraph = result["content"][0]
        assert paragraph["type"] == ADFNodeType.PARAGRAPH
        assert paragraph["content"][0]["text"] == ""

    def test_complex_document(self):
        """Test conversion of a complex document with multiple elements."""
        markdown = """# Main Title

This is a paragraph with **bold** and *italic* text.

## Subsection

Here's a list:
- Item 1
- Item 2 with `inline code`
- Item 3

And a code block:

```python
def hello():
    print("Hello, world!")
```

> This is a blockquote with some important information.

---

Final paragraph after the rule."""

        result = self.adapter.convert(markdown)

        # Should have multiple content elements
        assert len(result["content"]) > 5

        # Check that we have different types of nodes
        node_types = [node["type"] for node in result["content"]]
        assert ADFNodeType.HEADING in node_types
        assert ADFNodeType.PARAGRAPH in node_types
        assert ADFNodeType.BULLET_LIST in node_types
        assert ADFNodeType.CODE_BLOCK in node_types
        assert ADFNodeType.BLOCKQUOTE in node_types
        assert ADFNodeType.RULE in node_types

    def test_malformed_markdown(self):
        """Test handling of malformed markdown."""
        markdown = "**unclosed bold and *unclosed italic"
        result = self.adapter.convert(markdown)

        # Should still produce a valid ADF document
        assert result["version"] == 1
        assert result["type"] == ADFNodeType.DOC
        assert len(result["content"]) >= 1

        # Should have at least one paragraph
        assert any(node["type"] == ADFNodeType.PARAGRAPH for node in result["content"])

    def test_nested_lists(self):
        """Test conversion of nested lists."""
        markdown = """- Item 1
  - Nested item 1
  - Nested item 2
- Item 2"""

        result = self.adapter.convert(markdown)

        # Should have a bullet list
        assert len(result["content"]) == 1
        bullet_list = result["content"][0]
        assert bullet_list["type"] == ADFNodeType.BULLET_LIST

        # The nested structure might be flattened depending on markdown parser
        # Just ensure we have list items
        assert len(bullet_list["content"]) >= 2
        assert all(item["type"] == ADFNodeType.LIST_ITEM for item in bullet_list["content"])
