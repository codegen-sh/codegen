from __future__ import annotations

from _operator import attrgetter
from collections.abc import Iterable, Sequence

from tree_sitter import Node as TSNode
from typing_extensions import TypeVar

from graph_sitter.core.interfaces.editable import Editable

E = TypeVar("E", bound=Editable)


def sort_editables(nodes: Iterable[E | None] | Iterable[E], *, reverse: bool = False, dedupe: bool = True, alphabetical: bool = False, by_file: bool = False, by_id: bool = False) -> Sequence[E]:
    """Sort a list of Editables.

    Args:
        reverse: Reverse the order of the nodes in the list.
        dedupe: Filter out duplicate nodes.
        alphabetical: Sort nodes alphabetically instead of by start byte
        by_file: Sort nodes by file name then either alphabetically or by start byte
    """
    if dedupe:
        nodes = dict.fromkeys(nodes)
    sort_keys = ["name" if alphabetical else "ts_node.start_byte"]
    if by_file:
        sort_keys.insert(0, "filepath")
    if by_id:
        sort_keys.append("node_id")
    return sorted(filter(lambda node: node is not None, nodes), key=attrgetter(*sort_keys), reverse=reverse)


def sort_nodes(nodes: Iterable[TSNode | None] | Iterable[TSNode], *, reverse: bool = False, dedupe: bool = True) -> list[TSNode]:
    """Sort a list of ts_nodes.

    Args:
        reverse: Reverse the order of the nodes in the list.
        dedupe: Filter out duplicate nodes.
    """
    if dedupe:
        nodes = dict.fromkeys(nodes)
    return sorted(filter(lambda node: node is not None, nodes), key=attrgetter("start_byte"), reverse=reverse)
