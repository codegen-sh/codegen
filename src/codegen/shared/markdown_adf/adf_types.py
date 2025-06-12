"""
Type definitions for Atlassian Document Format (ADF) structures.
"""

from typing import Any, Dict, List, Literal, Optional, TypedDict, Union
from enum import Enum


class ADFNodeType(str, Enum):
    """ADF node types."""
    DOC = "doc"
    PARAGRAPH = "paragraph"
    HEADING = "heading"
    TEXT = "text"
    HARD_BREAK = "hardBreak"
    BULLET_LIST = "bulletList"
    ORDERED_LIST = "orderedList"
    LIST_ITEM = "listItem"
    CODE_BLOCK = "codeBlock"
    BLOCKQUOTE = "blockquote"
    RULE = "rule"
    TABLE = "table"
    TABLE_ROW = "tableRow"
    TABLE_HEADER = "tableHeader"
    TABLE_CELL = "tableCell"


class ADFMarkType(str, Enum):
    """ADF mark types for inline formatting."""
    STRONG = "strong"
    EM = "em"
    CODE = "code"
    LINK = "link"
    STRIKE = "strike"
    UNDERLINE = "underline"
    TEXT_COLOR = "textColor"
    SUBSUP = "subsup"


class ADFMark(TypedDict, total=False):
    """ADF mark structure for inline formatting."""
    type: ADFMarkType
    attrs: Optional[Dict[str, Any]]


class ADFNode(TypedDict, total=False):
    """Base ADF node structure."""
    type: ADFNodeType
    content: Optional[List["ADFNode"]]
    attrs: Optional[Dict[str, Any]]
    marks: Optional[List[ADFMark]]
    text: Optional[str]


class ADFTextNode(ADFNode):
    """ADF text node with required text field."""
    type: Literal[ADFNodeType.TEXT]
    text: str
    marks: Optional[List[ADFMark]]


class ADFParagraphNode(ADFNode):
    """ADF paragraph node."""
    type: Literal[ADFNodeType.PARAGRAPH]
    content: List[ADFNode]


class ADFHeadingNode(ADFNode):
    """ADF heading node."""
    type: Literal[ADFNodeType.HEADING]
    content: List[ADFNode]
    attrs: Dict[str, int]  # Contains level: 1-6


class ADFCodeBlockNode(ADFNode):
    """ADF code block node."""
    type: Literal[ADFNodeType.CODE_BLOCK]
    content: List[ADFTextNode]
    attrs: Optional[Dict[str, str]]  # Contains language if specified


class ADFListNode(ADFNode):
    """ADF list node (bullet or ordered)."""
    type: Union[Literal[ADFNodeType.BULLET_LIST], Literal[ADFNodeType.ORDERED_LIST]]
    content: List["ADFListItemNode"]


class ADFListItemNode(ADFNode):
    """ADF list item node."""
    type: Literal[ADFNodeType.LIST_ITEM]
    content: List[ADFNode]


class ADFDocument(TypedDict):
    """Complete ADF document structure."""
    version: Literal[1]
    type: Literal[ADFNodeType.DOC]
    content: List[ADFNode]


# Type aliases for convenience
AnyADFNode = Union[
    ADFNode,
    ADFTextNode,
    ADFParagraphNode,
    ADFHeadingNode,
    ADFCodeBlockNode,
    ADFListNode,
    ADFListItemNode,
]

