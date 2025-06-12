# Markdown to ADF Adapter

This module provides utilities to convert Markdown text to Atlassian Document Format (ADF), which is used by Atlassian products like Jira and Confluence.

## Overview

The Atlassian Document Format (ADF) is a JSON-based format that represents rich text content in Atlassian products. This adapter converts standard Markdown syntax to the corresponding ADF structure.

## Usage

### Basic Usage

````python
from codegen.shared.markdown_adf import MarkdownToADFAdapter

# Create an adapter instance
adapter = MarkdownToADFAdapter()

# Convert markdown to ADF
markdown_text = """
# Hello World

This is a paragraph with **bold** and *italic* text.

## Code Example

Here's some Python code:

```python
def greet(name):
    print(f"Hello, {name}!")
````

## Lists

- Item 1
- Item 2 with `inline code`
- Item 3

> This is a blockquote with important information.
> """

adf_document = adapter.convert(markdown_text)
print(json.dumps(adf_document, indent=2))

````

### Output Structure

The adapter returns an `ADFDocument` which is a dictionary with the following structure:

```python
{
    "version": 1,
    "type": "doc",
    "content": [
        # Array of ADF nodes
    ]
}
````

## Supported Markdown Elements

### Text Formatting

| Markdown            | ADF Mark Type | Description        |
| ------------------- | ------------- | ------------------ |
| `**bold**`          | `strong`      | Bold text          |
| `*italic*`          | `em`          | Italic text        |
| `` `code` ``        | `code`        | Inline code        |
| `[link](url)`       | `link`        | Hyperlinks         |
| `~~strikethrough~~` | `strike`      | Strikethrough text |

### Block Elements

| Markdown    | ADF Node Type | Description                        |
| ----------- | ------------- | ---------------------------------- |
| `# Heading` | `heading`     | Headings (H1-H6)                   |
| Paragraphs  | `paragraph`   | Regular paragraphs                 |
| `code`      | `codeBlock`   | Code blocks with optional language |
| `- item`    | `bulletList`  | Bullet lists                       |
| `1. item`   | `orderedList` | Numbered lists                     |
| `> quote`   | `blockquote`  | Block quotes                       |
| `---`       | `rule`        | Horizontal rules                   |

### Advanced Features

- **Code blocks with syntax highlighting**: Language detection from fenced code blocks
- **Nested lists**: Support for multi-level lists
- **Mixed formatting**: Combination of multiple inline formats
- **Link handling**: Automatic conversion of markdown links to ADF link marks

## Examples

### Simple Text with Formatting

```python
markdown = "This is **bold** and *italic* text with `inline code`."
adf = adapter.convert(markdown)
```

Results in:

```json
{
  "version": 1,
  "type": "doc",
  "content": [
    {
      "type": "paragraph",
      "content": [
        {
          "type": "text",
          "text": "This is "
        },
        {
          "type": "text",
          "text": "bold",
          "marks": [
            {
              "type": "strong"
            }
          ]
        },
        {
          "type": "text",
          "text": " and "
        },
        {
          "type": "text",
          "text": "italic",
          "marks": [
            {
              "type": "em"
            }
          ]
        },
        {
          "type": "text",
          "text": " text with "
        },
        {
          "type": "text",
          "text": "inline code",
          "marks": [
            {
              "type": "code"
            }
          ]
        },
        {
          "type": "text",
          "text": "."
        }
      ]
    }
  ]
}
```

### Code Block with Language

````python
markdown = """```python
def hello():
    print("Hello, world!")
```"""
adf = adapter.convert(markdown)
````

Results in:

```json
{
  "version": 1,
  "type": "doc",
  "content": [
    {
      "type": "codeBlock",
      "attrs": {
        "language": "python"
      },
      "content": [
        {
          "type": "text",
          "text": "def hello():\n    print(\"Hello, world!\")"
        }
      ]
    }
  ]
}
```

### Lists

```python
markdown = """
- First item
- Second item with **bold** text
- Third item
"""
adf = adapter.convert(markdown)
```

Results in a bullet list with properly formatted list items.

## Error Handling

The adapter is designed to be robust and handle malformed markdown gracefully:

- **Invalid HTML**: Falls back to creating a simple paragraph with the original text
- **Empty input**: Creates an empty paragraph
- **Unsupported elements**: Extracts text content and wraps in paragraphs
- **Malformed markdown**: Processes what it can and creates valid ADF structure

## Type Safety

The module includes comprehensive TypeScript-style type definitions:

- `ADFDocument`: The root document structure
- `ADFNode`: Base node type with all possible properties
- `ADFMark`: Inline formatting marks
- Specific node types: `ADFTextNode`, `ADFParagraphNode`, `ADFHeadingNode`, etc.

## Dependencies

- `markdown`: Python markdown parser
- `typing`: Type hints support

## Testing

The module includes comprehensive tests covering:

- Basic text conversion
- All supported markdown elements
- Complex nested structures
- Error handling scenarios
- Edge cases and malformed input

Run tests with:

```bash
pytest tests/shared/test_markdown_adf_adapter.py
```

## Limitations

- **Tables**: Not yet implemented (markdown tables are complex to convert to ADF)
- **Images**: Not implemented (requires media handling)
- **Custom HTML**: Raw HTML in markdown is not processed
- **Advanced ADF features**: Some ADF-specific features like panels, mentions, etc. are not supported

## Future Enhancements

- Table support
- Image and media handling
- Custom ADF node types (panels, mentions, etc.)
- Configuration options for conversion behavior
- Performance optimizations for large documents
