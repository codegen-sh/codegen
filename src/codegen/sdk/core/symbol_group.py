from __future__ import annotations

from collections.abc import Collection, Iterator
from typing import TYPE_CHECKING, Generic, TypeVar, override

from codegen.sdk.core.autocommit import reader, repr_func, writer
from codegen.sdk.core.interfaces.editable import Editable
from codegen.sdk.extensions.autocommit import commiter
from codegen.shared.decorators.docs import apidoc, noapidoc

if TYPE_CHECKING:
    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.dataclasses.usage import UsageKind
    from codegen.sdk.core.interfaces.has_name import HasName
    from codegen.sdk.core.node_id_factory import NodeId
    from codegen.sdk.output.ast import AST


Child = TypeVar("Child", bound="Editable")
Parent = TypeVar("Parent", bound="Editable")


@apidoc
class SymbolGroup(Editable[Parent], Collection[Child], Generic[Child, Parent]):
    """These are groups of symbols that form some kind of logical grouping, like a class or module,
    that do not follow the traditional tree structure.
    """

    _symbols: list[Child]

    def __init__(self, file_node_id: NodeId, ctx: CodebaseContext, parent: Parent, node: TSNode | None = None, children: list[Child] | None = None) -> None:
        self._symbols = children
        if node is None:
            # For backwards compatibility, assure that the first node is the main node
            node = children[0].ts_node
        super().__init__(node, file_node_id, ctx, parent)

    def __repr__(self) -> str:
        return f"Collection({self.symbols})" if self.symbols is not None else super().__repr__()

    def _init_children(self): ...

    @repr_func  # HACK
    def __hash__(self):
        return super().__hash__()
        # return hash(hash(node) for node in self.symbols) if self.symbols is not None else super().__hash__()

    def __eq__(self, other: object) -> bool:
        if other is None:
            return False
        if isinstance(other, SymbolGroup):
            return self.symbols == other.symbols
        if isinstance(other, list):
            return self.symbols == other
        return super().__eq__(other)

    @property
    @reader
    def symbols(self) -> list[Child]:
        """Returns the list of symbols in the group.

        Gets the list of symbols associated with this SymbolGroup. These symbols can be code elements like functions, classes, or variables that form a logical grouping.

        Returns:
            list[Child]: A list of symbol objects that belong to this group.
        """
        return self._symbols

    @property
    @reader
    def source(self) -> str:
        """Returns the concatenated source code of all symbols in the group.

        Returns:
            str: The concatenated source code of all symbols in the group.
        """
        # Use _source to avoid infinite recursion
        return "\n".join([symbol._source for symbol in self.symbols])

    @source.setter
    @writer
    def source(self, value) -> None:
        """Sets the source code of the Editable instance.

        Updates the source code by calling the edit method with the provided value.

        Args:
            value (str): The new source code to set for this Editable instance.

        Returns:
            None
        """
        self.edit(value)

    @property
    @reader
    def next_sibling(self) -> Editable | None:
        """Returns the next sibling of the last symbol in the symbol group.

        Provides access to the next sibling node of the last symbol in this symbol group.

        Returns:
            Editable | None: The next sibling node of the last symbol in the group, or None if there is no next sibling.
        """
        return self.symbols[-1].next_sibling

    @property
    @reader
    def next_named_sibling(self) -> Editable | None:
        """Returns the next named sibling of the last symbol in the group.

        Args:
            None

        Returns:
            Editable | None: The next named sibling node, or None if there is no next named sibling.
        """
        return self.symbols[-1].next_named_sibling

    @writer
    def find_string_literals(self, strings_to_match: list[str], fuzzy_match: bool = False) -> list[Editable]:
        """Search for string literals matching given strings in the SymbolGroup.

        Iterates through all symbols in the group and aggregates the results of
        finding string literals in each symbol.

        Args:
            strings_to_match (list[str]): List of strings to search for in string literals.
            fuzzy_match (bool, optional): If True, performs fuzzy matching instead of exact matching.

        Returns:
            list[Editable]: List of Editable nodes representing the matching string literals found within the symbols.
        """
        return [node for symbol in self.symbols for node in symbol.find_string_literals(strings_to_match, fuzzy_match)]

    @writer
    def replace(self, old: str, new: str, count: int = -1, priority: int = 0) -> int:
        """Replaces all instances of a string with a new string in all symbols within the group.

        Args:
            old (str): The string to be replaced.
            new (str): The string to replace with.
            count (int, optional): Maximum number of replacements to make. Defaults to -1 (replace all).
            priority (int, optional): Priority of the replacement operation. Defaults to 0.

        Returns:
            int: Number of replacements made.
        """
        for symbol in self.symbols:
            symbol.replace(old, new, count, priority)

    @reader
    def find(self, strings_to_match: list[str] | str, *, exact: bool = False) -> list[Editable]:
        """Search for substrings in the given symbols that match `strings_to_match`.

        Args:
            strings_to_match (list[str] | str): The string or list of strings to search for.
            exact (bool): If True, only return nodes that exactly match the query.

        Returns:
            list[Editable]: A list of Editable objects representing each match found.
        """
        return [node for symbol in self.symbols for node in symbol.find(strings_to_match, exact)]

    @reader
    def search(self, regex_pattern: str, include_strings: bool = True, include_comments: bool = True) -> list[Editable]:
        """Searches for regex matches in the codebase.

        Searches through the source code to find text matching a regex pattern, with options to exclude string literals and comments from the search.

        Args:
            regex_pattern (str): The regular expression pattern to search for.
            include_strings (bool, optional): Whether to include string literals in the search. Defaults to True.
            include_comments (bool, optional): Whether to include comments in the search. Defaults to True.

        Returns:
            list[Editable]: A list of Editable objects representing matched text nodes in the codebase.
        """
        return [node for symbol in self.symbols for node in symbol.search(regex_pattern, include_strings, include_comments)]

    @writer
    def insert_before(self, new_src: str, fix_indentation: bool = False, newline: bool = True, priority: int = 0, dedupe: bool = True) -> None:
        """Inserts source code before this symbol group.

        Inserts the provided source code before the first symbol in the group, while maintaining proper code formatting.

        Args:
            new_src (str): The source code to insert.
            fix_indentation (bool, optional): Whether to adjust the indentation of the inserted code to match the current code. Defaults to False.
            newline (bool, optional): Whether to add a newline after the inserted code. Defaults to True.
            priority (int, optional): The priority of this edit operation. Higher priority edits are applied first. Defaults to 0.
            dedupe (bool, optional): Whether to prevent duplicate insertions of the same code. Defaults to True.

        Returns:
            None
        """
        super().insert_before(new_src, fix_indentation, newline, priority, dedupe)

    @writer
    def insert_after(self, new_src: str, fix_indentation: bool = False, newline: bool = True, priority: int = 0, dedupe: bool = True) -> None:
        """Inserts source code after this node in the codebase.

        Args:
            new_src (str): The source code to insert.
            fix_indentation (bool, optional): Adjust indentation to match current text.
            newline (bool, optional): Add a newline before the inserted code.
            priority (int, optional): Priority of the edit operation.
            dedupe (bool, optional): Deduplicate identical edits.

        Returns:
            None
        """
        if len(self.symbols) == 0 or self.ts_node != self.symbols[0].ts_node:
            super().insert_after(new_src, fix_indentation, newline, priority, dedupe)
        else:
            self.symbols[-1].insert_after(new_src, fix_indentation, newline, priority, dedupe)

    @writer
    def edit(self, new_src: str, fix_indentation: bool = False, priority: int = 0, dedupe: bool = True) -> None:
        """Replace the source of this node with new text.

        Replaces the source of this SymbolGroup with new text by replacing the first symbol's source and removing all other symbols.

        Args:
            new_src (str): The new source text to replace the current text with.
            fix_indentation (bool, optional): Adjusts the indentation of new_src to match the current text's indentation. Defaults to False.
            priority (int, optional): Priority of the edit operation. Higher priority edits take precedence. Defaults to 0.
            dedupe (bool, optional): Prevents duplicate edits at the same location. Defaults to True.

        Returns:
            None
        """
        self.symbols[0].edit(new_src, fix_indentation, priority, dedupe)
        for symbol in self.symbols[1:]:
            symbol.remove()

    @writer
    def remove(self, delete_formatting: bool = True, priority: int = 0, dedupe: bool = True) -> None:
        """Removes this node and its related extended nodes from the codebase.

        Args:
            delete_formatting (bool, optional): Whether to delete related extended nodes like decorators and comments. Defaults to True.
            priority (int, optional): Priority level of the removal operation. Defaults to 0.
            dedupe (bool, optional): Whether to deduplicate removal operations. Defaults to True.

        Returns:
            None
        """
        for symbol in self.symbols:
            symbol.remove(delete_formatting, priority, dedupe)

    @reader
    def __iter__(self) -> Iterator[Child]:
        return iter(self.symbols)

    @reader
    def __contains__(self, __x) -> bool:
        return __x in self.symbols

    @reader
    def __len__(self) -> int:
        return len(self.symbols)

    @reader
    def __getitem__(self, item):
        return self.symbols[item]

    def __bool__(self) -> bool:
        return True

    @noapidoc
    @commiter
    def _compute_dependencies(self, usage_type: UsageKind | None = None, dest: HasName | None = None) -> None:
        for symbol in self.symbols:
            symbol._compute_dependencies(usage_type, dest)

    @override
    def _get_ast_children(self) -> list[tuple[str | None, AST]]:
        return [(None, symbol.ast()) for symbol in self.symbols]
