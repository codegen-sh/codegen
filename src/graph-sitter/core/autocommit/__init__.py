"""Autocommit implementation.

Theory of Operation:
-------------------
Context: We operate on 3 kinds of nodes: Files, Symbols, and DetachedSymbols.
(Technically DetachedSymbols includes Editables and some are orphans)

Every time we perform an operation, if the node is a File or Symbol, we will commit and reaquire if it has been updated.
Then if the operation was a write, we mark it (and the file containing it) as pending.
If the symbol is detached, we mark its parent as pending. This is recursive until we reach a symbol on the graph or an orphan
If it was a move (or rename), we also mark where the new symbol will be. This removes all need for commiting in most circumstances.
Edge Cases:
----------
- We cannot reaquire detached symbols, so we don't autoupdate those.
- We cannot handle situations where you change the type of a symbol then operate on it
- We cannot handle removing then operating on a symbol
- We skip commits when you do raw edits and inserts, but will fall back to autocommit if needed
"""

from codegen.sdk.core.autocommit.constants import enabled
from codegen.sdk.core.autocommit.decorators import mover, remover, repr_func, writer
from codegen.sdk.core.autocommit.manager import AutoCommit
from codegen.sdk.compiled.autocommit import commiter, reader

__all__ = [
    "AutoCommit",
    "commiter",
    "enabled",
    "mover",
    "reader",
    "remover",
    "repr_func",
    "writer",
]
