"""
Fallback Python implementation of compiled sort module.
This provides basic functionality for testing when Cython modules aren't compiled.
"""

def sort_editables(editables):
    """Sort editables - basic implementation"""
    if not editables:
        return []
    
    # Simple sort by name if available, otherwise return as-is
    try:
        return sorted(editables, key=lambda x: getattr(x, 'name', str(x)))
    except (AttributeError, TypeError):
        return list(editables)

