from collections.abc import Generator, Iterable
from functools import cached_property as functools_cached_property
from functools import lru_cache as functools_lru_cache

from tree_sitter import Node as TSNode

def get_all_identifiers(node: TSNode) -> list[TSNode]:
    """Get all the identifiers in a tree-sitter node. Recursive implementation"""

def iter_all_descendants(node: TSNode, type_names: Iterable[str] | str, max_depth: int | None = None, nested: bool = True) -> Generator[TSNode, None, None]: ...
def find_all_descendants(
    node: TSNode,
    type_names: Iterable[str] | str,
    max_depth: int | None = None,
    nested: bool = True,
    stop_at_first: str | None = None,
) -> list[TSNode]: ...
def find_line_start_and_end_nodes(node: TSNode) -> list[tuple[TSNode, TSNode]]:
    """Returns a list of tuples of the start and end nodes of each line in the node"""

def find_first_descendant(node: TSNode, type_names: list[str], max_depth: int | None = None) -> TSNode | None: ...

cached_property = functools_cached_property
lru_cache = functools_lru_cache

def uncache_all(): ...
def is_descendant_of(node: TSNode, possible_parent: TSNode) -> bool: ...
