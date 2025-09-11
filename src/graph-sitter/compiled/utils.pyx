from collections import Counter
from collections.abc import Generator, Iterable
from functools import cached_property as functools_cached_property
from functools import lru_cache as functools_lru_cache

from tabulate import tabulate
from tree_sitter import Node as TSNode


def get_all_identifiers(node: TSNode) -> list[TSNode]:
    """Get all the identifiers in a tree-sitter node. Recursive implementation"""
    identifiers = []

    def traverse(current_node: TSNode):
        if current_node is None:
            return
        if current_node.type in ("identifier", "shorthand_property_identifier_pattern"):
            identifiers.append(current_node)
            return

        elif current_node.type == "attribute":
            value_node = current_node.child_by_field_name("value")
            if value_node:
                traverse(value_node)
                return

        for child in current_node.children:
            traverse(child)

    traverse(node)
    return sorted(dict.fromkeys(identifiers), key=lambda x: x.start_byte)


def find_all_descendants(node: TSNode, type_names: Iterable[str] | str, max_depth: int | None = None, nested: bool = True, stop_at_first: str | None = None) -> list[TSNode]:
    if isinstance(type_names, str):
        type_names = [type_names]
    descendants = []

    def traverse(current_node: TSNode, depth=0):
        if max_depth is not None and depth > max_depth:
            return

        if current_node.type in type_names:
            descendants.append(current_node)
            if not nested and current_node != node:
                return

        if stop_at_first and current_node.type == stop_at_first:
            return

        for child in current_node.children:
            traverse(child, depth + 1)

    traverse(node)
    return descendants


def iter_all_descendants(node: TSNode, type_names: Iterable[str] | str, max_depth: int | None = None, nested: bool = True) -> Generator[TSNode, None, None]:
    if isinstance(type_names, str):
        type_names = [type_names]
    type_names = frozenset(type_names)

    def traverse(current_node: TSNode, depth=0):
        if max_depth is not None and depth > max_depth:
            return

        if current_node.type in type_names:
            yield current_node
            if not nested and current_node != node:
                return

        for child in current_node.children:
            yield from traverse(child, depth + 1)

    yield from traverse(node)


def find_line_start_and_end_nodes(node: TSNode) -> list[tuple[TSNode, TSNode]]:
    line_to_start_node = {}
    line_to_end_node = {}

    def collect_start_and_end_nodes(current_node: TSNode) -> None:
        start_row = current_node.start_point[0]
        if start_row not in line_to_start_node or line_to_start_node[start_row].start_point[1] >= current_node.start_point[1]:
            line_to_start_node[start_row] = current_node

        if current_node.start_point[0] != current_node.end_point[0]:
            # We only care about multi-line nodes
            for child in current_node.children:
                collect_start_and_end_nodes(child)
        end_row = current_node.end_point[0]
        if end_row not in line_to_end_node or line_to_end_node[end_row].end_point[1] <= current_node.end_point[1]:
            line_to_end_node[end_row] = current_node

    collect_start_and_end_nodes(node)
    return list(zip(line_to_start_node.values(), line_to_end_node.values()))


def find_first_descendant(node: TSNode, type_names: list[str], max_depth: int | None = None) -> TSNode | None:
    def find(current_node: TSNode, depth: int = 0) -> TSNode | None:
        if current_node.type in type_names:
            return current_node
        if max_depth is not None and depth >= max_depth:
            return
        for child in current_node.children:
            if ret := find(child, depth + 1):
                return ret

    return find(node)


to_uncache = []
lru_caches = []
counter = Counter()


class cached_property(functools_cached_property):
    def __get__(self, instance, owner=None):
        ret = super().__get__(instance)
        if instance is not None:
            to_uncache.append((instance, self.attrname))
            counter[self.attrname] += 1
        return ret


def lru_cache(func=None, *, maxsize=128, typed=False):
    """A wrapper around functools.lru_cache that tracks the cached function so that its cache
    can be cleared later via uncache_all().
    """
    if func is None:
        # return decorator
        return lambda f: lru_cache(f, maxsize=maxsize, typed=typed)

    # return decorated
    cached_func = functools_lru_cache(maxsize=maxsize, typed=typed)(func)
    lru_caches.append(cached_func)
    return cached_func


def uncache_all():
    for instance, name in to_uncache:
        try:
            del instance.__dict__[name]
        except KeyError:
            pass

    for cached_func in lru_caches:
        cached_func.cache_clear()


def report():
    print(tabulate(counter.most_common(10)))


def is_descendant_of(node: TSNode, possible_parent: TSNode) -> bool:
    """Helper to check if node is inside possible_parent in the AST"""
    current = node
    while current:
        if current == possible_parent:
            return True
        current = current.parent
    return False
