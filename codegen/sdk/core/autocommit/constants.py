from enum import IntEnum, unique
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from codegen.sdk.core.interfaces.editable import Editable

REMOVED = "REMOVED"

AutoCommitSymbol = "Editable"


@unique
class AutoCommitState(IntEnum):
    """Current operation."""

    Write = 0  # Can only be done inside another write or as the first state
    Read = 1  # Can be done anytime
    Committing = 2  # During a commit/reset, Prevents any updates
    Special = 4  # During Hash or Repr, prevents further changes to state


class IllegalWriteError(Exception):
    """Indicates there is a write, move, or commit called inside a read, commit, or repr
    function.
    """

    pass


class NodeNotFoundError(Exception):
    """Indicates a node was not found during the update process, such as when editing the type."""

    pass


class OutdatedNodeError(Exception):
    """Indicates a node is out of date."""

    def __init__(self, node: "Editable") -> None:
        parent = node
        from codegen.sdk.core.symbol import Symbol

        while parent is not None and not isinstance(parent, Symbol):
            parent = parent.parent
        super().__init__(
            f"Using an outdated node {node}.\n"
            + "This can happen if you cache a detached symbol, then update a related symbol or file.\n"
            + (
                f"Try acquiring the node from it's parent symbol: {parent}.\n"
                + "For example if the node was the first parameter of a function, "
                + f"call {node.name} = {parent.name}.parameters[0]"
            )
            if parent
            else ""
        )


# SAFETY TOGGLE
enabled = False
# def enabled():
#     # SAFETY TOGGLE
#     return True
