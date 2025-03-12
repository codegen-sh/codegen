import os
import re
import shutil
import statistics
from collections.abc import Iterable
from contextlib import contextmanager
from xml.dom.minidom import parseString

import dicttoxml
import xmltodict
from tree_sitter import Node as TSNode

from codegen.sdk.extensions.utils import find_all_descendants, find_first_descendant, get_all_identifiers
from codegen.sdk.typescript.enums import TSFunctionTypeNames
from codegen.shared.enums.programming_language import ProgrammingLanguage

"""
Utility functions for traversing the tree sitter structure.
Do not include language specific traversals, or string manipulations here.
"""


class XMLUtils:
    @staticmethod
    def dict_to_xml(data: dict | list, format: bool = False, **kwargs) -> str:
        result = dicttoxml.dicttoxml(data, return_bytes=False, **kwargs)
        if not isinstance(result, str):
            msg = "Failed to convert dict to XML"
            raise ValueError(msg)
        if format:
            result = parseString(result).toprettyxml()
        return result

    @staticmethod
    def add_cdata_to_function_body(xml_string):
        pattern = r"(<function_body>)(.*?)(</function_body>)"
        replacement = r"\1<![CDATA[\2]]>\3"
        updated_xml_string = re.sub(pattern, replacement, xml_string, flags=re.DOTALL)
        return updated_xml_string

    @staticmethod
    def add_cdata_to_tags(xml_string: str, tags: Iterable[str]) -> str:
        patterns = [rf"(<{tag}>)(.*?)(</{tag}>)" for tag in tags]
        updated_xml_string = xml_string

        for pattern in patterns:
            replacement = r"\1<![CDATA[\2]]>\3"
            updated_xml_string = re.sub(pattern, replacement, updated_xml_string, flags=re.DOTALL)

        return updated_xml_string

    @staticmethod
    def xml_to_dict(xml_string: str, **kwargs) -> dict:
        return xmltodict.parse(XMLUtils.add_cdata_to_tags(xml_string, ["function_body", "reasoning"]), **kwargs)

    @staticmethod
    def strip_after_tag(xml_string, tag):
        pattern = re.compile(f"<{tag}.*?>.*", re.DOTALL)
        match = pattern.search(xml_string)
        if match:
            return xml_string[: match.start()]
        else:
            return xml_string

    @staticmethod
    def strip_tag(xml_string: str, tag: str):
        pattern = re.compile(f"<{tag}>.*?</{tag}>", re.DOTALL)
        return pattern.sub("", xml_string).strip()

    @staticmethod
    def strip_all_tags(xml_string: str):
        pattern = re.compile(r"<[^>]*>")
        return pattern.sub("", xml_string).strip()

    @staticmethod
    def extract_elements(xml_string: str, tag: str, keep_tag: bool = False) -> list[str]:
        pattern = re.compile(f"<{tag}.*?</{tag}>", re.DOTALL)
        matches = pattern.findall(xml_string)
        if keep_tag:
            return matches
        else:
            return [match.strip(f"<{tag}>").strip(f"</{tag}>") for match in matches]


def find_first_function_descendant(node: TSNode) -> TSNode:
    type_names = [function_type.value for function_type in TSFunctionTypeNames]
    return find_first_descendant(node=node, type_names=type_names, max_depth=2)


def find_import_node(node: TSNode) -> TSNode | None:
    """Get the import node from a node that may contain an import.
    Returns None if the node does not contain an import.

    Returns:
        TSNode | None: The import_statement or call_expression node if it's an import, None otherwise
    """
    # Static imports
    if node.type == "import_statement":
        return node

    # Dynamic imports and requires can be either:
    # 1. Inside expression_statement -> call_expression
    # 2. Direct call_expression

    # we only parse imports inside expressions and variable declarations

    if member_expression := find_first_descendant(node, ["member_expression"]):
        # there may be multiple call expressions (for cases such as import(a).then(module => module).then(module => module)
        descendants = find_all_descendants(member_expression, ["call_expression"], stop_at_first="statement_block")
        if descendants:
            import_node = descendants[-1]
        else:
            # this means this is NOT a dynamic import()
            return None
    else:
        import_node = find_first_descendant(node, ["call_expression"])

    # thus we only consider the deepest one
    if import_node:
        function = import_node.child_by_field_name("function")
        if function and (function.type == "import" or (function.type == "identifier" and function.text.decode("utf-8") == "require")):
            return import_node

    return None


def find_index(target: TSNode, siblings: list[TSNode]) -> int:
    """Returns the index of the target node in the list of siblings, or -1 if not found. Recursive implementation."""
    if target in siblings:
        return siblings.index(target)

    for i, sibling in enumerate(siblings):
        index = find_index(target, sibling.named_children if target.is_named else sibling.children)
        if index != -1:
            return i
    return -1


def find_first_ancestor(node: TSNode, type_names: list[str], max_depth: int | None = None) -> TSNode | None:
    depth = 0
    while node is not None and (max_depth is None or depth <= max_depth):
        if node.type in type_names:
            return node
        node = node.parent
        depth += 1
    return None


def find_first_child_by_field_name(node: TSNode, field_name: str) -> TSNode | None:
    child = node.child_by_field_name(field_name)
    if child is not None:
        return child
    for child in node.children:
        first_descendant = find_first_child_by_field_name(child, field_name)
        if first_descendant is not None:
            return first_descendant
    return None


def has_descendant(node: TSNode, type_name: str) -> bool:
    def traverse(current_node: TSNode, depth: int = 0) -> bool:
        if current_node.type == type_name:
            return True
        return any(traverse(child, depth + 1) for child in current_node.children)

    return traverse(node)


def get_first_identifier(node: TSNode) -> TSNode | None:
    """Get the text of the first identifier child of a tree-sitter node. Recursive implementation"""
    if node.type in ("identifier", "shorthand_property_identifier_pattern"):
        return node
    for child in node.children:
        output = get_first_identifier(child)
        if output is not None:
            return output
    return None


def descendant_for_byte_range(node: TSNode, start_byte: int, end_byte: int, allow_comment_boundaries: bool = True) -> TSNode | None:
    """Proper implementation of descendant_for_byte_range, which returns the lowest node that contains the byte range."""
    ts_match = node.descendant_for_byte_range(start_byte, end_byte)

    # We don't care if the match overlaps with comments
    if allow_comment_boundaries:
        return ts_match

    # Want to prevent it from matching with part of the match within a comment
    else:
        if not ts_match.children:
            return ts_match
        comments = find_all_descendants(ts_match, "comment")
        # see if any of these comments partially overlaps with the match
        if any(comment.start_byte < start_byte < comment.end_byte or comment.start_byte < end_byte < comment.end_byte for comment in comments):
            return None
        return ts_match


@contextmanager
def shadow_files(files: str | list[str]):
    """Creates shadow copies of the given files. Restores the original files after the context manager is exited.

    Returns list of filenames of shadowed files.
    """
    if isinstance(files, str):
        files = [files]
    shadowed_files = {}
    # Generate shadow file names
    for file_name in files:
        shadow_file_name = file_name + ".gs_internal.bak"
        shadowed_files[file_name] = shadow_file_name
    # Shadow files
    try:
        # Backup the original files
        for file_name, shadow_file_name in shadowed_files.items():
            shutil.copy(file_name, shadow_file_name)
        yield shadowed_files.values()
    finally:
        # Restore the original files
        for file_name, shadow_file_name in shadowed_files.items():
            # If shadow file was created, restore the original file and delete the shadow file
            if os.path.exists(shadow_file_name):
                # Delete the original file if it exists
                if os.path.exists(file_name):
                    os.remove(file_name)
                # Copy the shadow file to the original file path
                shutil.copy(shadow_file_name, file_name)
                # Delete the shadow file
                os.remove(shadow_file_name)


def calculate_base_path(full_path, relative_path):
    """Calculate the base path represented by './' in a relative path.

    :param full_path: The full path to a file or directory
    :param relative_path: A relative path starting with './'
    :return: The base path represented by './' in the relative path
    """
    # Normalize paths to handle different path separators
    full_path = os.path.normpath(full_path)
    relative_path = os.path.normpath(relative_path)

    # Split paths into components
    full_components = full_path.split(os.sep)
    relative_components = relative_path.split(os.sep)

    # Remove './' from the start of relative path if present
    if relative_components[0] == ".":
        relative_components = relative_components[1:]

    # Calculate the number of components to keep from the full path
    keep_components = len(full_components) - len(relative_components)

    # Join the components to form the base path
    base_path = os.sep.join(full_components[:keep_components])

    return base_path


__all__ = [
    "find_all_descendants",
    "find_first_ancestor",
    "find_first_child_by_field_name",
    "find_first_descendant",
    "get_all_identifiers",
    "has_descendant",
]


def get_language_file_extensions(language: ProgrammingLanguage):
    """Returns the file extensions for the given language."""
    from codegen.sdk.python import PyFile
    from codegen.sdk.typescript.file import TSFile

    if language == ProgrammingLanguage.PYTHON:
        return set(PyFile.get_extensions())
    elif language == ProgrammingLanguage.TYPESCRIPT:
        return set(TSFile.get_extensions())


def truncate_line(input: str, max_chars: int) -> str:
    input = str(input)
    if len(input) > max_chars:
        return input[:max_chars] + f"...(truncated from {len(input)} characters)."
    return input


def is_minified_js(content):
    """Analyzes a string to determine if it contains minified JavaScript code.

    Args:
        content: String containing JavaScript code to analyze

    Returns:
        bool: True if the content appears to be minified JavaScript, False otherwise
    """
    try:
        # Skip empty content
        if not content.strip():
            return False

        # Characteristics of minified JS files
        lines = content.split("\n")

        # 1. Check for average line length (minified files have very long lines)
        line_lengths = [len(line) for line in lines if line.strip()]
        if not line_lengths:  # Handle empty content case
            return False

        avg_line_length = statistics.mean(line_lengths)

        # 2. Check for semicolon-to-newline ratio (minified often has ; instead of newlines)
        semicolons = content.count(";")
        newlines = len(lines) - 1
        semicolon_ratio = semicolons / max(newlines, 1)  # Avoid division by zero

        # 3. Check whitespace ratio (minified has low whitespace)
        whitespace_chars = len(re.findall(r"[\s]", content))
        total_chars = len(content)
        whitespace_ratio = whitespace_chars / total_chars if total_chars else 0

        # 4. Check for common minification patterns
        has_common_patterns = bool(re.search(r"[\w\)]\{[\w:]+\}", content))  # Condensed object notation

        # 5. Check for short variable names (common in minified code)
        variable_names = re.findall(r"var\s+(\w+)", content)
        avg_var_length = statistics.mean([len(name) for name in variable_names]) if variable_names else 0

        # Decision logic - tuned threshold values
        is_minified = (
            (avg_line_length > 250)  # Very long average line length
            and (semicolon_ratio > 0.8 or has_common_patterns)  # High semicolon ratio or minification patterns
            and (whitespace_ratio < 0.08)  # Very low whitespace ratio
            and (avg_var_length < 3 or not variable_names)  # Extremely short variable names or no vars
        )

        return is_minified

    except Exception as e:
        print(f"Error analyzing content: {e}")
        return False
