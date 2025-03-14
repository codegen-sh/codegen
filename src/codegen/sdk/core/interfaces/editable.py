from __future__ import annotations

import itertools
import re
from abc import abstractmethod
from functools import cached_property
from typing import TYPE_CHECKING, Generic, Self, TypeVar, Unpack, final, overload

from rich.markup import escape
from rich.pretty import Pretty

from codegen.sdk.codebase.span import Span
from codegen.sdk.codebase.transactions import EditTransaction, InsertTransaction, RemoveTransaction, TransactionPriority
from codegen.sdk.core.autocommit import commiter, reader, remover, repr_func, writer
from codegen.sdk.core.placeholder.placeholder import Placeholder
from codegen.sdk.extensions.utils import get_all_identifiers
from codegen.sdk.output.ast import AST
from codegen.sdk.output.constants import ANGULAR_STYLE, MAX_STRING_LENGTH
from codegen.sdk.output.jsonable import JSONable
from codegen.sdk.output.utils import style_editable
from codegen.sdk.utils import descendant_for_byte_range, find_all_descendants, find_first_ancestor, find_index, truncate_line
from codegen.shared.decorators.docs import apidoc, noapidoc

if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Iterable, Sequence

    import rich.repr
    from rich.console import Console, ConsoleOptions, RenderResult
    from tree_sitter import Node as TSNode
    from tree_sitter import Point, Range

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.codebase.flagging.code_flag import CodeFlag
    from codegen.sdk.codebase.flagging.enums import FlagKwargs
    from codegen.sdk.codebase.transaction_manager import TransactionManager
    from codegen.sdk.core.class_definition import Class
    from codegen.sdk.core.dataclasses.usage import UsageKind
    from codegen.sdk.core.detached_symbols.function_call import FunctionCall
    from codegen.sdk.core.export import Export
    from codegen.sdk.core.expressions import Expression
    from codegen.sdk.core.expressions.type import Type
    from codegen.sdk.core.file import File, SourceFile
    from codegen.sdk.core.function import Function
    from codegen.sdk.core.import_resolution import Import, WildcardImport
    from codegen.sdk.core.interfaces.has_name import HasName
    from codegen.sdk.core.interfaces.importable import Importable
    from codegen.sdk.core.node_id_factory import NodeId
    from codegen.sdk.core.statements.statement import Statement
    from codegen.sdk.core.symbol import Symbol
    from codegen.sdk.core.symbol_group import SymbolGroup
    from codegen.sdk.enums import NodeType
    from codegen.visualizations.enums import VizNode
CONTAINER_CHARS = (b"(", b")", b"{", b"}", b"[", b"]", b"<", b">", b"import")
MAX_REPR_LEN: int = 200


def _contains_container_chars(text: bytes) -> bool:
    return any([char in text for char in CONTAINER_CHARS])


def _is_empty_container(text: str) -> bool:
    stripped_str = re.sub(r"\s+", "", text)
    return len(stripped_str) == 2 and all([char in CONTAINER_CHARS for char in text])


_EXCLUDE_FROM_REPR: list[str] = [
    "ctx",
    "autocommit_cache",
    "parent",
    "file_node_id",
    "to_file_id",
    "ts_node",
    "node_id",
    "resolved_type_frames",
    "resolved_types",
    "valid_symbol_names",
    "valid_import_names",
    "predecessor",
    "successor",
    "base",
    "call_chain",
    "code_block",
    "parent_statement",
    "symbol_usages",
    "usages",
    "function_definition_frames",
    "start_point",
    "end_point",
    "span",
    "range",
    "methods",
    "ts_config",
    "symbols",
    "exports",
]

Parent = TypeVar("Parent", bound="Editable")
P = TypeVar("P", bound=Placeholder)
T = TypeVar("T", bound="Editable")


@apidoc
class Editable(JSONable, Generic[Parent]):
    """An editable instance is an abstract text representation of any text in a file.

    Attributes:
        ts_node: The TreeSitter node associated with this Editable instance.
        file_node_id: The unique identifier for the file node.
        ctx: The codebase context that this Editable instance is part of.
        parent: The parent node of this Editable instance.
        node_type: The type of node this Editable instance represents.
    """

    ts_node: TSNode
    file_node_id: NodeId
    ctx: CodebaseContext
    parent: Parent
    node_type: NodeType
    _file: File | None = None
    _hash: int | None = None

    def __init__(self, ts_node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: Parent) -> None:
        self.ts_node = ts_node
        self.file_node_id = file_node_id
        self.ctx = ctx
        self.parent = parent
        if ctx.config.debug:
            seen = set()
            while parent is not None:
                assert (parent.ts_node, parent.__class__) not in seen
                seen.add((parent.ts_node, parent.__class__))
                parent = parent.parent
        if self.file and self.ctx.config.full_range_index:
            self._add_to_index

    def __hash__(self):
        if self._hash is None:
            self._hash = hash((self.filepath, self.range, self.ts_node.kind_id))
        return self._hash

    def __str__(self) -> str:
        return self.source

    @repr_func
    def __repr__(self) -> str:
        """Represent the string for logging purposes."""
        if hasattr(self, "__dict__"):
            keys = list(self.__dict__.keys())
        elif hasattr(self, "__slots__"):
            keys = list(self.__slots__)
        else:
            keys = list()
        keys = ["name", "filepath", "start_point", "end_point", *keys]
        if not hasattr(self, "name"):
            keys[0] = "source"
        elif "source" in keys:
            keys.remove("source")
        kws = [f"{k}={truncate_line(repr(getattr(self, k, None)), MAX_REPR_LEN)}" for k in dict.fromkeys(keys) if k not in _EXCLUDE_FROM_REPR and not k.startswith("_") and hasattr(self, k)]
        return "{}({})".format(type(self).__name__, ", ".join(kws))

    def __rich_repr__(self) -> rich.repr.Result:
        yield escape(self.filepath)

    __rich_repr__.angular = ANGULAR_STYLE  # type: ignore

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield Pretty(self, max_string=MAX_STRING_LENGTH)
        if self.file:
            yield from style_editable(self.ts_node, self.file.path, self.file.ts_node)

    @reader
    def __eq__(self, other: object):
        if other is None:
            return False
        if isinstance(other, Editable):
            return self.filepath == other.filepath and self.ts_node.kind_id == other.ts_node.kind_id and self.range == other.range
        if isinstance(other, str):
            return self.source == other
        return False

    @reader
    def __contains__(self, item: str | Editable) -> bool:
        if isinstance(item, Editable):
            return item.source in self.source
        return item in self.source

    @property
    @noapidoc
    def transaction_manager(self) -> TransactionManager:
        return self.ctx.transaction_manager

    @property
    @noapidoc
    @reader
    def start_byte(self) -> int:
        """The start byte of the Editable instance that appears in file."""
        return self.ts_node.start_byte

    @property
    @noapidoc
    @reader
    @final
    def end_byte(self) -> int:
        """The end byte of the Editable instance that appears in file."""
        return self.ts_node.end_byte

    @property
    @noapidoc
    @reader
    @final
    def start_point(self) -> Point:
        """The start point (row, column) of the Editable instance that appears in file."""
        return self.ts_node.start_point

    @property
    @noapidoc
    @reader
    @final
    def end_point(self) -> Point:
        """The end point (row, column) of the Editable instance that appears in file."""
        return self.ts_node.end_point

    @property
    @noapidoc
    @reader
    def line_range(self) -> range:
        """The 0-indexed line/row range that the Editable instance spans in the file."""
        return range(self.start_point[0], self.end_point[0] + 1)  # +1 b/c end_point[0] is inclusive

    @property
    @noapidoc
    @reader
    def _source(self) -> str:
        """Text representation of the Editable instance."""
        return self.ts_node.text.decode("utf-8")

    @property
    @reader
    def source(self) -> str:
        """Text representation of the Editable instance.

        Returns the source text of the Editable instance. This is the main property used to access the text content of any code element in GraphSitter.

        Returns:
            str: The text content of this Editable instance.
        """
        return self._source

    @source.setter
    @writer
    def source(self, value) -> None:
        """Sets the source (text representation) of the Editable instance using .edit(..).

        Only edits if the new value is different from the current source.

        Args:
            value (str): The new text representation to set.

        Returns:
            None: The method returns nothing.
        """
        if self.source != value:
            self.edit(value)

    @property
    @noapidoc
    @reader(cache=False)
    def extended_nodes(self) -> list[Editable]:
        """List of Editable instances that includes itself and its extended symbols like `export`,
        `public` or `decorator`
        """
        return [self]

    @property
    def extended(self) -> SymbolGroup:
        """Returns a SymbolGroup of all extended nodes associated with this element.

        Creates a SymbolGroup that provides a common interface for editing all extended nodes,
        such as decorators, modifiers, and comments associated with the element.

        Args:
            None

        Returns:
            SymbolGroup: A group containing this node and its extended nodes that allows
            batch modification through a common interface.
        """
        from codegen.sdk.core.symbol_group import SymbolGroup

        return SymbolGroup(self.file_node_id, self.ctx, self.parent, children=self.extended_nodes)

    @property
    @reader
    def extended_source(self) -> str:
        """Returns the source text representation of all extended nodes.

        Gets the source text of all extended nodes combined. This property allows reading the source text
        of all extended nodes (e.g. decorators, export statements) associated with this node.

        Returns:
            str: The combined source text of all extended nodes.
        """
        return self.extended.source

    @extended_source.setter
    def extended_source(self, value: str) -> None:
        """Set the source of all extended nodes.

        Updates the source of all nodes in the extended nodes list by calling .edit(..). This is useful for updating multiple related nodes (e.g. decorators, export statements) at once.

        Args:
            value (str): The new source text to set for all extended nodes.

        Returns:
            None
        """
        self.extended.edit(value)

    @property
    @reader
    @noapidoc
    def children(self) -> list[Editable[Self]]:
        """List of Editable instances that are children of this node."""
        return [self._parse_expression(child) for child in self.ts_node.named_children]

    @property
    @reader
    @noapidoc
    def _anonymous_children(self) -> list[Editable[Self]]:
        """All anonymous children of an editable."""
        return [self._parse_expression(child) for child in self.ts_node.children if not child.is_named]

    @property
    @reader
    @noapidoc
    def next_sibling(self) -> Editable | None:
        """Returns the Editable instance that next appears in the file."""
        if self.ts_node is None:
            return None

        next_sibling_node = self.ts_node.next_sibling
        if next_sibling_node is None:
            return None

        return self._parse_expression(next_sibling_node)

    @property
    @reader
    @noapidoc
    def next_named_sibling(self) -> Editable[Parent] | None:
        if self.ts_node is None:
            return None

        next_named_sibling_node = self.ts_node.next_named_sibling
        if next_named_sibling_node is None:
            return None

        return self.parent._parse_expression(next_named_sibling_node)

    @property
    @reader
    @noapidoc
    def previous_named_sibling(self) -> Editable[Parent] | None:
        if self.ts_node is None:
            return None

        previous_named_sibling_node = self.ts_node.prev_named_sibling
        if previous_named_sibling_node is None:
            return None

        return self.parent._parse_expression(previous_named_sibling_node)

    @property
    def file(self) -> SourceFile:
        """The file object that this Editable instance belongs to.

        Retrieves or caches the file object associated with this Editable instance.

        Returns:
            File: The File object containing this Editable instance.
        """
        if self._file is None:
            self._file = self.ctx.get_node(self.file_node_id)
        return self._file  # type: ignore

    @property
    def filepath(self) -> str:
        """The file path of the file that this Editable instance belongs to.

        Returns a string representing the absolute file path of the File that contains this Editable instance.

        Returns:
            str: The absolute file path.
        """
        return self.file.file_path

    @reader
    def find_string_literals(self, strings_to_match: list[str], fuzzy_match: bool = False) -> list[Editable[Self]]:
        """Returns a list of string literals within this node's source that match any of the given
        strings.

        Args:
            strings_to_match (list[str]): A list of strings to search for in string literals.
            fuzzy_match (bool): If True, matches substrings within string literals. If False, only matches exact strings. Defaults to False.

        Returns:
            list[Editable[Self]]: A list of Editable objects representing the matching string literals.
        """
        matches: list[Editable[Self]] = []
        for node in self.extended_nodes:
            matches.extend(node._find_string_literals(strings_to_match, fuzzy_match))
        return matches

    @noapidoc
    @reader
    def _find_string_literals(self, strings_to_match: list[str], fuzzy_match: bool = False) -> Sequence[Editable[Self]]:
        all_string_nodes = find_all_descendants(self.ts_node, type_names={"string"})
        editables = []
        for string_node in all_string_nodes:
            assert string_node.text is not None
            full_string = string_node.text.strip(b'"').strip(b"'")
            if fuzzy_match:
                if not any([str_to_match.encode("utf-8") in full_string for str_to_match in strings_to_match]):
                    continue
            else:
                if not any([str_to_match.encode("utf-8") == full_string for str_to_match in strings_to_match]):
                    continue
            editables.append(self._parse_expression(string_node))
        return editables

    @writer
    def replace(self, old: str, new: str, count: int = -1, is_regex: bool = False, priority: int = 0) -> int:
        """Search and replace occurrences of text within this node's source and its extended nodes.

        This method performs string replacement similar to Python's string.replace(), with support for regex patterns.
        It operates on both the main node and any extended nodes (e.g. decorators, exports).

        Args:
            old (str): The text or pattern to search for.
            new (str): The text to replace matches with.
            count (int, optional): Maximum number of replacements to make. Defaults to -1 (replace all).
            is_regex (bool, optional): Whether to treat 'old' as a regex pattern. Defaults to False.
            priority (int, optional): Priority of the replacement operation. Defaults to 0.

        Returns:
            int: The total number of replacements made.

        Raises:
            ValueError: If there are multiple occurrences of the substring in a node's source.
        """
        total_count = 0
        for node in self.extended_nodes:
            total_count += node._replace(old, new, count - total_count, is_regex, priority)
            if 0 < count <= total_count:
                break
        return total_count

    @noapidoc
    @writer
    def _replace(self, old: str, new: str, count: int = -1, is_regex: bool = False, priority: int = 0) -> int:
        """Search and replace an instance of `substring` within this node's source.

        Only replaces up to the `count` specified, and returns the total instances replaced.
        """
        total_count = 0
        if not is_regex:
            old = re.escape(old)

        for match in re.finditer(old.encode("utf-8"), self.ts_node.text):  # type: ignore
            start_byte = self.ts_node.start_byte + match.start()
            end_byte = self.ts_node.start_byte + match.end()
            t = EditTransaction(
                start_byte,
                end_byte,
                self.file,
                new,
                priority=priority,
            )
            self.transaction_manager.add_transaction(t, dedupe=True)

            total_count += 1
            if 0 < count <= total_count:
                break
        return total_count

    @reader
    def find(self, strings_to_match: list[str] | str, *, exact: bool = False) -> list[Editable]:
        """Find and return matching nodes or substrings within an Editable instance.

        This method searches through the extended_nodes of the Editable instance and returns all nodes or substrings that match the given search criteria.

        Args:
            strings_to_match (Union[list[str], str]): One or more strings to search for.
            exact (bool): If True, only return nodes whose source exactly matches one of the strings_to_match.
                         If False, return nodes that contain any of the strings_to_match as substrings.
                         Defaults to False.

        Returns:
            list[Editable]: A list of Editable instances that match the search criteria.
        """
        matches = []
        for node in self.extended_nodes:
            matches.extend(node._find(strings_to_match, exact))
        return matches

    @noapidoc
    @reader
    def _find(self, strings_to_match: list[str] | str, exact: bool = False) -> list[Editable]:
        if isinstance(strings_to_match, str):
            strings_to_match = [strings_to_match]
        # Use search to find string
        search_results = itertools.chain.from_iterable(map(self._search, map(re.escape, strings_to_match)))
        if exact:
            search_results = filter(lambda result: result.source in strings_to_match, search_results)

        # Combine and deduplicate results
        return list(search_results)

    @reader
    def search(self, regex_pattern: str, include_strings: bool = True, include_comments: bool = True) -> list[Editable]:
        """Returns a list of all regex match of `regex_pattern`, similar to python's re.search().

        Searches for matches of a regular expression pattern within the text of this node and its extended nodes.

        Args:
            regex_pattern (str): The regular expression pattern to search for.
            include_strings (bool): When False, excludes the contents of string literals from the search. Defaults to True.
            include_comments (bool): When False, excludes the contents of comments from the search. Defaults to True.

        Returns:
            list[Editable]: A list of Editable objects corresponding to the matches found.
        """
        matches = []
        for node in self.extended_nodes:
            matches.extend(node._search(regex_pattern, include_strings=include_strings, include_comments=include_comments))
        return matches

    @noapidoc
    @reader
    def _search(self, regex_pattern: str, include_strings: bool = True, include_comments: bool = True) -> list[Editable]:
        matching_byte_ranges: list[tuple[int, int]] = []
        string = self.ts_node.text

        pattern = re.compile(regex_pattern.encode("utf-8"))
        start_byte_offset = self.ts_node.byte_range[0]
        for match in pattern.finditer(string):  # type: ignore
            matching_byte_ranges.append((match.start() + start_byte_offset, match.end() + start_byte_offset))

        matches: list[Editable] = []
        for byte_range in matching_byte_ranges:
            ts_match = descendant_for_byte_range(self.ts_node, byte_range[0], byte_range[1], allow_comment_boundaries=include_comments)
            if ts_match is not None:
                # Check for inclusion of comments and/or strings
                if (include_strings or ts_match.type not in ("string", "string_content", "string_fragment")) and (include_comments or ts_match.type != "comment"):
                    matches.append(self._parse_expression(ts_match))
        return list(matches)

    @writer(commit=False)
    @noapidoc
    def insert_at(self, byte: int, new_src: str | Callable[[], str], *, priority: int | tuple = 0, dedupe: bool = True, exec_func: Callable[[], None] | None = None) -> None:
        # Insert the new_src
        t = InsertTransaction(
            byte,
            self.file,
            new_src,
            priority=priority,
            exec_func=exec_func,
        )
        self.transaction_manager.add_transaction(t, dedupe=dedupe)

    def _get_indent(self) -> int:
        return self.ts_node.start_point[1]

    @writer(commit=False)
    def insert_before(self, new_src: str, fix_indentation: bool = False, newline: bool = True, priority: int = 0, dedupe: bool = True) -> None:
        """Inserts text before this node's source with optional indentation and newline handling.

        This method inserts the provided text before the current node's source code. It can automatically handle indentation and newline placement.

        Args:
            new_src (str): The text to insert before this node.
            fix_indentation (bool): Whether to fix the indentation of new_src to match the current node. Defaults to False.
            newline (bool): Whether to add a newline after new_src. Defaults to True.
            priority (int): Transaction priority for managing multiple edits. Defaults to 0.
            dedupe (bool): Whether to deduplicate identical transactions. Defaults to True.

        Returns:
            None
        """
        if self.ts_node is None:
            return

        indentation = " " * min(node._get_indent() for node in self.extended_nodes)
        if fix_indentation:
            src_lines = new_src.split("\n")
            src_lines = src_lines[:1] + [line if line == "" else indentation + line for line in src_lines[1:]]
            new_src = "\n".join(src_lines)

        # Add a newline before the new_src
        if newline:
            new_src += "\n"

        if fix_indentation:
            new_src += indentation
        self.insert_at(self.start_byte, new_src, priority=priority, dedupe=dedupe)

    @writer(commit=False)
    def insert_after(self, new_src: str, fix_indentation: bool = False, newline: bool = True, priority: int = 0, dedupe: bool = True) -> None:
        """Inserts code after this node.

        Args:
            new_src (str): The source code to insert after this node.
            fix_indentation (bool, optional): Whether to adjust the indentation of new_src to match the current node. Defaults to False.
            newline (bool, optional): Whether to add a newline before the new_src. Defaults to True.
            priority (int, optional): Priority of the insertion transaction. Defaults to 0.
            dedupe (bool, optional): Whether to deduplicate identical transactions. Defaults to True.

        Returns:
            None
        """
        if self.ts_node is None:
            return

        if fix_indentation:
            indentation = " " * min(node._get_indent() for node in self.extended_nodes)
            src_lines = new_src.split("\n")
            src_lines = [line if line == "" else indentation + line for line in src_lines]
            new_src = "\n".join(src_lines)

        # Add a newline before the new_src
        if newline:
            new_src = "\n" + new_src

        self.insert_at(self.ts_node.end_byte, new_src, priority=priority, dedupe=dedupe)

    @writer
    def edit(self, new_src: str, fix_indentation: bool = False, priority: int = 0, dedupe: bool = True) -> None:
        """Replace the source of this `Editable` with `new_src`.

        Replaces the text representation of this Editable instance with new text content. The method handles indentation adjustments and transaction management.

        Args:
            new_src (str): The new source text to replace the current text with.
            fix_indentation (bool): If True, adjusts the indentation of `new_src` to match the current text's indentation level. Defaults to False.
            priority (int): The priority of the edit transaction. Higher priority edits are applied first. Defaults to 0.
            dedupe (bool): If True, deduplicates identical transactions. Defaults to True.

        Returns:
            None
        """
        if fix_indentation:
            line = self.file.content.split("\n")[self.ts_node.start_point[0]]
            indentation = line[: len(line) - len(line.strip())]
            src_lines = new_src.split("\n")
            src_lines = src_lines[:1] + [line if line == "" else indentation + line for line in src_lines[1:]]
            new_src = "\n".join(src_lines)

        t = EditTransaction(
            self.start_byte,
            self.end_byte,
            self.file,
            new_src,
            priority=priority,
        )
        self.transaction_manager.add_transaction(t, dedupe=dedupe)

    @writer
    def _edit_byte_range(self, new_src: str, start_byte: int, end_byte: int, priority: int = 0, dedupe: bool = True) -> None:
        t = EditTransaction(
            start_byte,
            end_byte,
            self.file,
            new_src,
            priority=priority,
        )
        self.transaction_manager.add_transaction(t, dedupe=dedupe)

    @remover
    @noapidoc
    def remove_byte_range(self, start_byte: int, end_byte: int) -> None:
        if self.ctx.config.debug:
            assert start_byte < end_byte
        t = RemoveTransaction(start_byte, end_byte, self.file)
        self.transaction_manager.add_transaction(t)

    @remover
    def remove(self, delete_formatting: bool = True, priority: int = 0, dedupe: bool = True) -> None:
        """Deletes this Node and its related extended nodes (e.g. decorators, comments).

        Removes the current node and its extended nodes (e.g. decorators, comments) from the codebase.
        After removing the node, it handles cleanup of any surrounding formatting based on the context.

        Args:
            delete_formatting (bool): Whether to delete surrounding whitespace and formatting. Defaults to True.
            priority (int): Priority of the removal transaction. Higher priority transactions are executed first. Defaults to 0.
            dedupe (bool): Whether to deduplicate removal transactions at the same location. Defaults to True.

        Returns:
            None
        """
        for node in self.extended_nodes:
            node._remove(delete_formatting=delete_formatting, priority=priority, dedupe=dedupe)

    @remover
    @noapidoc
    def _remove(self, delete_formatting: bool = True, priority: int = 0, dedupe: bool = True) -> None:
        if self.parent._smart_remove(self, delete_formatting=delete_formatting, priority=priority, dedupe=dedupe):
            return
        # If the node deleted is the only node, delete the entire node
        parent = self.ts_node.parent
        removed_start_byte = self.start_byte
        removed_end_byte = self.end_byte
        if parent is not None and parent.type in ("parenthesized_expression", "jsx_expression") and self.ts_node.is_named:
            removed_start_byte = min(parent.start_byte, removed_start_byte)
            removed_end_byte = max(parent.end_byte, removed_end_byte)
            parent = parent.parent
        while parent is not None and parent.byte_range == self.ts_node.byte_range:
            parent = parent.parent
        if parent is not None and parent.type in ("named_imports", "export_statement") and len(parent.named_children) == 1 and self.ts_node.is_named:
            removed_start_byte = min(parent.start_byte, removed_start_byte)
            removed_end_byte = max(parent.end_byte, removed_end_byte)
            parent = parent.parent

        def should_keep(node: TSNode):
            if node.type == "comment":
                # Remove comments on the same rows as the deleted node
                if node.end_point[0] <= self.end_point[0] and node.start_byte > removed_start_byte:
                    return False
            return True

        siblings = None if parent is None else list(filter(should_keep, parent.named_children if self.ts_node.is_named else parent.children))
        # same line

        # In the case this is an import_from_statement, the first sibling is the module_name, and the rest are the imports
        if parent is not None and parent.type == "import_from_statement" and siblings and len(siblings) > 0:
            siblings = siblings[1:]

        if isinstance(self.parent, Editable):
            exec_func = self.parent._removed_child_commit
        else:
            exec_func = None

        # Delete the node
        t = RemoveTransaction(removed_start_byte, removed_end_byte, self.file, priority=priority, exec_func=exec_func)
        if self.transaction_manager.add_transaction(t, dedupe=dedupe):
            if exec_func is not None:
                self.parent._removed_child()

        # If there are sibling nodes, delete the surrounding whitespace & formatting (commas)
        if delete_formatting and siblings and len(siblings) > 1:
            index = find_index(self.ts_node, siblings)

            # Check if all previous siblings are being deleted
            all_previous_deleted = all(
                self.transaction_manager.get_transactions_at_range(self.file.path, start_byte=siblings[i].start_byte, end_byte=siblings[i].end_byte, transaction_order=TransactionPriority.Remove)
                for i in range(index)
            )

            if all_previous_deleted:
                if index != 0:
                    self.remove_byte_range(siblings[index - 1].end_byte, removed_start_byte)
                # If it's the first import or all previous imports are being deleted,
                # remove the comma after
                start_byte = removed_end_byte
                if index + 1 < len(siblings):
                    end_byte = siblings[index + 1].start_byte
                else:
                    return  # Do not delete if it's the last node
            elif _contains_container_chars(self.file.content_bytes[siblings[index - 1].end_byte : removed_start_byte]):
                if index + 1 < len(siblings):
                    start_byte = removed_end_byte
                    end_byte = siblings[index + 1].start_byte
                else:
                    return  # Do not delete the last node
            else:
                start_byte = siblings[index - 1].end_byte
                end_byte = removed_start_byte

            # Check that it is not deleting a list container
            if _contains_container_chars(self.file.content_bytes[start_byte:end_byte]):
                return

            t = RemoveTransaction(
                start_byte,
                end_byte,
                self.file,
                priority=priority,
            )
            self.transaction_manager.add_transaction(t, dedupe=dedupe)

    # ==================================================================================================================
    # Utilities
    # ==================================================================================================================
    # TODO: not sure if these functions should be here tbh
    @overload
    def child_by_field_name(self, field_name: str, *, placeholder: type[P], default: type[Expression] | None = None) -> Expression[Self] | P: ...

    @overload
    def child_by_field_name(self, field_name: str, *, placeholder: None = ..., default: type[Expression] | None = None) -> Expression[Self] | None: ...

    @reader
    @noapidoc
    def child_by_field_name(self, field_name: str, *, placeholder: type[P] | None = None, **kwargs) -> Expression[Self] | P | None:
        """Get child by field name."""
        node = self.ts_node.child_by_field_name(field_name)
        if node is None:
            if placeholder is not None:
                return placeholder(self)
            return None
        return self._parse_expression(node, **kwargs)

    @reader
    @noapidoc
    def children_by_field_types(self, field_types: str | Iterable[str]) -> Generator[Expression[Self], None, None]:
        """Get child by field types."""
        if isinstance(field_types, str):
            field_types = [field_types]
        for child in self.ts_node.children:
            if child.type in field_types:
                if node := self._parse_expression(child):
                    yield node

    @reader
    @noapidoc
    def child_by_field_types(self, field_types: str | Iterable[str]) -> Expression[Self] | None:
        """Get child by fiexld types."""
        return next(self.children_by_field_types(field_types), None)

    @property
    @reader
    @noapidoc
    def ts_node_type(self) -> str:
        """This is the underlying type of the TreeSitter node corresponding to this entity, and the
        value will correspond to the tree-sitter language grammar.
        """
        return self.ts_node.type

    @commiter
    @noapidoc
    def commit(self) -> None:
        """Commits any pending transactions for the current node to the codebase.

        Commits only the transactions that affect the file this node belongs to. This is useful when you want to
        commit changes made to a specific node without committing all pending transactions in the codebase.

        Args:
            None

        Returns:
            None
        """
        self.ctx.commit_transactions(files={self.file.path})

    @noapidoc
    def _removed_child(self) -> None:
        pass

    @noapidoc
    def _removed_child_commit(self) -> None:
        pass

    @property
    @reader
    def variable_usages(self) -> list[Editable]:
        """Returns Editables for all TreeSitter node instances of variable usages within this node's
        scope.

        This method finds all variable identifier nodes in the TreeSitter AST, excluding:
        - Function names in function calls
        - Import names in import statements
        - Property access identifiers (except the base object)
        - Keyword argument names (in Python and TypeScript)

        This is useful for variable renaming and usage analysis within a scope.

        Returns:
            list[Editable]: A list of Editable nodes representing variable usages. Each
                Editable corresponds to a TreeSitter node instance where the variable
                is referenced.
        """
        usages: Sequence[Editable[Self]] = []
        identifiers = get_all_identifiers(self.ts_node)
        for identifier in identifiers:
            # Excludes function names
            parent = identifier.parent
            if parent is None:
                continue
            if parent.type in ["call", "call_expression"]:
                continue
            # Excludes local import statements
            if parent.parent is not None and parent.parent.type in ["import_statement", "import_from_statement"]:
                continue
            # Excludes property identifiers
            if parent.type == "attribute" and parent.children.index(identifier) != 0:
                continue
            # Excludes arg keyword (Python specific)
            if parent.type == "keyword_argument" and identifier == parent.child_by_field_name("name"):
                continue
            # Excludes arg keyword (Typescript specific)
            arguments = find_first_ancestor(parent, ["arguments"])
            if arguments is not None and any(identifier == arg.child_by_field_name("left") for arg in arguments.named_children):
                continue

            usages.append(self._parse_expression(identifier))

        return usages

    @reader
    def get_variable_usages(self, var_name: str, fuzzy_match: bool = False) -> Sequence[Editable[Self]]:
        """Returns Editables for all TreeSitter nodes corresponding to instances of variable usage
        that matches the given variable name.

        Retrieves a list of variable usages that match a specified name, with an option for fuzzy matching. By default, excludes property identifiers and argument keywords.

        Args:
            var_name (str): The variable name to search for.
            fuzzy_match (bool): If True, matches variables where var_name is a substring. If False, requires exact match. Defaults to False.

        Returns:
            list[Editable]: List of Editable objects representing variable usage nodes matching the given name.
        """
        if fuzzy_match:
            return [usage for usage in self.variable_usages if var_name in usage.source]
        else:
            return [usage for usage in self.variable_usages if var_name == usage.source]

    @overload
    def _parse_expression(self, node: TSNode, **kwargs) -> Expression[Self]: ...

    @overload
    def _parse_expression(self, node: TSNode | None, **kwargs) -> Expression[Self] | None: ...

    def _parse_expression(self, node: TSNode | None, **kwargs) -> Expression[Self] | None:
        return self.ctx.parser.parse_expression(node, self.file_node_id, self.ctx, self, **kwargs)

    def _parse_type(self, node: TSNode) -> Type[Self] | None:
        return self.ctx.parser.parse_type(node, self.file_node_id, self.ctx, self)

    def flag(self, **kwargs: Unpack[FlagKwargs]) -> CodeFlag[Self]:
        """Adds a visual flag comment to the end of this Editable's source text.

        Flags this Editable by appending a comment with emoji flags at the end of its source text.
        This is useful for visually highlighting specific nodes in the source code during development
        and debugging.

        Returns:
            None
        """
        # TODO: remove this once the frontend can process code flags
        return self.ctx.flags.flag_instance(self, **kwargs)

    @noapidoc
    @abstractmethod
    @commiter
    def _compute_dependencies(self, usage_type: UsageKind, dest: HasName | None = None) -> None:
        """Compute the dependencies of the export object."""
        pass

    @commiter
    @noapidoc
    def _add_symbol_usages(self: HasName, identifiers: list[TSNode], usage_type: UsageKind, dest: HasName | None = None) -> None:
        from codegen.sdk.core.expressions import Name
        from codegen.sdk.core.interfaces.resolvable import Resolvable

        if dest is None:
            dest = self
        for x in identifiers:
            if dep := self._parse_expression(x, default=Name):
                assert isinstance(dep, Resolvable)
                dep._compute_dependencies(usage_type, dest)

    @commiter
    @noapidoc
    def _add_all_identifier_usages(self, usage_type: UsageKind, dest: HasName | None = None) -> None:
        id_types = self.ctx.node_classes.resolvables
        # Skip identifiers that are part of a property
        identifiers = find_all_descendants(self.ts_node, id_types, nested=False)
        return self._add_symbol_usages(identifiers, usage_type, dest)

    @commiter
    @noapidoc
    def add_all_identifier_usages_for_child_node(self, usage_type: UsageKind, child: TSNode, dest=None) -> None:
        # Interim hack. Don't use
        id_types = self.ctx.node_classes.resolvables
        # Skip identifiers that are part of a property
        identifiers = find_all_descendants(child, id_types, nested=False)
        return self._add_symbol_usages(identifiers, usage_type, dest)

    @noapidoc
    def _log_parse(self, msg: str, *args, **kwargs):
        self.ctx.parser.log(msg, *args, **kwargs)

    @property
    @noapidoc
    def viz(self) -> VizNode:
        from codegen.sdk.core.interfaces.has_name import HasName
        from codegen.visualizations.enums import VizNode

        if isinstance(self, HasName):
            return VizNode(file_path=self.filepath, start_point=self.start_point, end_point=self.end_point, name=self.name, symbol_name=self.__class__.__name__)
        else:
            return VizNode(file_path=self.filepath, start_point=self.start_point, end_point=self.end_point, symbol_name=self.__class__.__name__)

    @noapidoc
    @reader
    def resolve_name(self, name: str, start_byte: int | None = None, strict: bool = True) -> Generator[Symbol | Import | WildcardImport]:
        if self.parent is not None:
            yield from self.parent.resolve_name(name, start_byte or self.start_byte, strict=strict)
        else:
            yield from self.file.resolve_name(name, start_byte or self.start_byte, strict=strict)

    @cached_property
    @noapidoc
    def github_url(self) -> str | None:
        if self.file.github_url:
            return self.file.github_url + f"#L{self.start_point[0] + 1}-L{self.end_point[0] + 1}"

    @property
    @noapidoc
    def parent_symbol(self) -> Symbol | File | Import | Export:
        """Returns the parent symbol of the symbol."""
        return self.parent.parent_symbol

    @property
    @noapidoc
    @final
    def range(self) -> Range:
        return self.ts_node.range

    @cached_property
    @noapidoc
    @final
    def span(self) -> Span:
        return Span(range=self.range, filepath=self.filepath)

    @property
    @noapidoc
    def descendant_symbols(self) -> list[Importable]:
        """Returns the nested symbols of the importable object, including itself."""
        return []
        # return list(itertools.chain.from_iterable(child.descendant_symbols for child in self.children))

    @writer
    def reduce_condition(self, bool_condition: bool, node: Editable | None = None) -> None:
        """Reduces an editable to the following condition"""
        if node is not None:
            node.edit(self.ctx.node_classes.bool_conversion[bool_condition])
        else:
            self.parent.reduce_condition(bool_condition, self)

    @property
    @reader
    def function_calls(self) -> list[FunctionCall]:
        """Returns a list of all function calls contained within this expression.

        Traverses the extended nodes of this expression to find all function calls within it. This is useful for tasks like analyzing call patterns or renaming function invocations.

        Returns:
            list[FunctionCall]: A list of FunctionCall objects representing all function calls contained within this expression.
        """
        calls = []
        for node in self.children:
            calls.extend(node.function_calls)
        return calls

    @property
    @noapidoc
    def self_dest(self) -> Importable:
        """Returns the symbol usage resolution destination node for the symbol."""
        from codegen.sdk.core.interfaces.importable import Importable

        dest = self
        while dest and not isinstance(dest, Importable):
            dest = dest.parent
        return dest

    @cached_property
    @noapidoc
    def _add_to_index(self) -> None:
        self.file._range_index.add_to_range(self)

    @noapidoc
    def _smart_remove(self, child, *args, **kwargs) -> bool:
        """Check if a node should remove itself based on the removal of its children nodes"""
        return False

    @reader
    def is_wrapped_in(self, cls: type[Expression]) -> bool:
        """Check if this node is contained another node of the given class"""
        return self.parent_of_type(cls) is not None

    @reader
    def parent_of_type(self, type: type[T]) -> T | None:
        """Find the first ancestor of the node of the given type. Does not return itself"""
        if isinstance(self.parent, type):
            return self.parent
        if self.parent is not self and self.parent is not None:
            return self.parent.parent_of_type(type)
        return None

    def parent_of_types(self, types: set[type[T]]) -> T | None:
        """Find the first ancestor of the node of the given type. Does not return itself"""
        if self.parent and any(isinstance(self.parent, t) for t in types):
            return self.parent
        if self.parent is not self and self.parent is not None:
            return self.parent.parent_of_types(types)
        return None

    def is_child_of(self, instance: Editable) -> bool:
        """Checks if this node is a descendant of the given editable instance in the AST."""
        if not self.parent:
            return False
        if self.parent is instance:
            return True
        else:
            return self.parent.is_child_of(instance=instance)

    @reader
    def ancestors(self, type: type[T]) -> list[T]:
        """Find all ancestors of the node of the given type. Does not return itself"""
        if self.parent is not self and self.parent is not None:
            ret = self.parent.ancestors(type)
        else:
            ret = []
        if isinstance(self.parent, type):
            ret.append(self.parent)
        return ret

    @reader
    @noapidoc
    def first_ancestors(self, type: type[T]) -> T | None:
        """Find the first ancestor of the node of the given type."""
        return next(iter(self.ancestors(type)), None)

    @property
    @reader
    def parent_statement(self) -> Statement | None:
        """Find the statement this node is contained in"""
        from codegen.sdk.core.statements.statement import Statement

        return self.parent_of_type(Statement)

    @property
    @reader
    def parent_function(self) -> Function | None:
        """Find the function this node is contained in"""
        from codegen.sdk.core.function import Function

        return self.parent_of_type(Function)

    @property
    @reader
    def parent_class(self) -> Class | None:
        """Find the class this node is contained in"""
        from codegen.sdk.core.class_definition import Class

        return self.parent_of_type(Class)

    def _get_ast_children(self) -> list[tuple[str | None, AST]]:
        children = []
        names = {}
        for name, val in self._list_members(include_methods=True).items():
            if isinstance(val, Editable):
                names[val] = name
        for child in self.file._range_index.get_children(self):
            if self.ctx.config.debug:
                assert child != self, child
            elif child == self:
                continue
            children.append((names.get(child, None), child.ast()))
        return children

    @noapidoc
    @final
    def ast(self) -> AST:
        children = self._get_ast_children()
        return AST(codegen_sdk_type=self.__class__.__name__, span=self.span, tree_sitter_type=self.ts_node_type, children=children)
