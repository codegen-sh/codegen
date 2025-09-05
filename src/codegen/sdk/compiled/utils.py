"""
Fallback Python implementation of compiled utils module.
This provides basic functionality for testing when Cython modules aren't compiled.
"""
from functools import cached_property as functools_cached_property
from functools import lru_cache as functools_lru_cache
from typing import Generator, Iterable

try:
    from tree_sitter import Node as TSNode
except ImportError:
    # Fallback for when tree_sitter isn't available
    TSNode = None


def get_all_identifiers(node):
    """Get all the identifiers in a tree-sitter node. Recursive implementation"""
    if not node:
        return []
    
    identifiers = []
    if hasattr(node, 'type') and node.type == 'identifier':
        identifiers.append(node)
    
    if hasattr(node, 'children'):
        for child in node.children:
            identifiers.extend(get_all_identifiers(child))
    
    return identifiers


def iter_all_descendants(node, type_names, max_depth=None, nested=True):
    """Iterate over all descendants of a node matching type names"""
    if not node:
        return
    
    if isinstance(type_names, str):
        type_names = [type_names]
    
    def _iter_descendants(current_node, current_depth=0):
        if max_depth is not None and current_depth > max_depth:
            return
        
        if hasattr(current_node, 'children'):
            for child in current_node.children:
                if hasattr(child, 'type') and child.type in type_names:
                    yield child
                
                if nested:
                    yield from _iter_descendants(child, current_depth + 1)
    
    yield from _iter_descendants(node)


def find_all_descendants(node, type_names, max_depth=None, nested=True, stop_at_first=None):
    """Find all descendants matching type names"""
    return list(iter_all_descendants(node, type_names, max_depth, nested))


def find_line_start_and_end_nodes(node):
    """Returns a list of tuples of the start and end nodes of each line in the node"""
    # Simplified implementation
    if not node or not hasattr(node, 'children'):
        return []
    
    lines = []
    for child in node.children:
        lines.append((child, child))
    
    return lines


def find_first_descendant(node, type_names, max_depth=None):
    """Find first descendant matching type names"""
    for descendant in iter_all_descendants(node, type_names, max_depth):
        return descendant
    return None


def is_descendant_of(node, possible_parent):
    """Check if node is a descendant of possible_parent"""
    if not node or not possible_parent:
        return False
    
    current = node
    while hasattr(current, 'parent') and current.parent:
        if current.parent == possible_parent:
            return True
        current = current.parent
    
    return False


def uncache_all():
    """Clear all caches"""
    pass


# Export the cached_property and lru_cache
cached_property = functools_cached_property
lru_cache = functools_lru_cache

