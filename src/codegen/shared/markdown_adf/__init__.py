"""
Markdown to ADF (Atlassian Document Format) Adapter

This module provides utilities to convert Markdown text to Atlassian Document Format (ADF),
which is used by Atlassian products like Jira and Confluence.
"""

from .adapter import MarkdownToADFAdapter
from .adf_types import ADFDocument, ADFNode, ADFMark

__all__ = ["MarkdownToADFAdapter", "ADFDocument", "ADFNode", "ADFMark"]
