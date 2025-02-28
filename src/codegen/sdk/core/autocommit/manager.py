from codegen.shared.logging.get_logger import get_logger
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union

from codegen.sdk.core.autocommit.constants import (
    REMOVED,
    AutoCommitState,
    AutoCommitSymbol,
    IllegalWriteError,
    NodeNotFoundError,
    OutdatedNodeError,
)
from codegen.sdk.core.autocommit.utils import is_file, is_on_graph, is_symbol
from codegen.sdk.core.node_id_factory import NodeId
from codegen.sdk.extensions.autocommit import update_dict

if TYPE_CHECKING:
    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.file import File
    from codegen.sdk.core.import_resolution import Import
    from codegen.sdk.core.symbol import Symbol


logger = get_logger(__name__)


@dataclass
class AutoCommitNode:
    """The pending update for a node.

    Attributes:
        symbol: The symbol being updated. Kept to ensure correctness
        generation: Version of the symbol
        new_id: New id to fetch (if applicable)
        new_file: File symbol was moved to (if applicable)
    """

    symbol: AutoCommitSymbol
    generation: int
    new_id: NodeId | None = None
    new_file: Optional["File"] = None


@dataclass
class PendingFiles:
    """Current files autocommit is operating on.

    For example, if we read a symbol and find another symbol out of date in the same file, we would
    not want to update it.
    """

    files: set[Path] | None
    all: bool = False

    def __bool__(self) -> bool:
        return bool(self.files) or self.all


class AutoCommit:
    """Global autocommit state.

    Attributes:
        state: Current operation being performed
        _files: Mapping of files to their new filepaths, or None if they were just modified
        _nodes: Mapping of nodes to their new Node IDs
        _locked_files: All files that are currently being operated on
        _lock_all: All files are currently being operated on
    """

    state: AutoCommitState | None = None
    _files: dict[Path, NodeId | None]
    _nodes: dict[NodeId, AutoCommitNode]
    ctx: "CodebaseContext"
    _locked_files: set[str]
    _lock_all: bool = False

    def __init__(self, ctx: "CodebaseContext") -> None:
        self.ctx = ctx
        self._files = {}
        self._nodes = {}
        self._locked_files = set()

    def __repr__(self) -> str:
        return str(self.__dict__)

    def _commit(self, lock: PendingFiles, additional: str | None = None) -> None:
        if lock:
            logger.debug(
                "Running autocommit on %s", "all files" if lock.all else lock.files
            )
            files = lock.files if not lock.all else None
            if additional and files:
                files.add(additional)
            self.ctx.commit_transactions(files=files)

    def _update_file(self, symbol: "File", lock: PendingFiles) -> None:
        """Check for an update to a file, and if there is one, copy its dict."""
        if symbol.file_node_id in self._files:
            new_id = self._files.pop(symbol.file_node_id, None)
            if new_id == REMOVED:
                logger.warning("Editing a removed node")
                return
            self._commit(lock, new_id)
            old_node = self.ctx.get_node(symbol.file_node_id)
            new_node = self.ctx.get_node(
                new_id if new_id is not None else symbol.file_node_id
            )
            old_node.__dict__ = new_node.__dict__
            if not lock:
                self._files[symbol.file_node_id] = new_id

    def _reaquire_node(
        self,
        symbol: Union["Symbol", "Import"],
        new_node_id: NodeId,
        missing_ok: bool = False,
    ):
        """Re-aquire a symbol."""
        # Prevent double re-aquire
        new_node = self.ctx.get_node(new_node_id)
        if new_node is None:
            if missing_ok:
                return
            raise NodeNotFoundError(
                f"Could not find node with {new_node_id=} {symbol.node_id=}. This may happen if you change the type of a symbol using edit (such as editing a variable into a function)"
            )
        update_dict(set(), symbol, new_node)

    def _update_symbol(
        self, symbol: Union["Symbol", "Import"], lock: PendingFiles
    ) -> None:
        """Check for an update to a symbol, and if there is one, copy its dict."""
        node_id = symbol.node_id
        if symbol_update := self._nodes.pop(node_id, None):
            assert self.state is not None
            logger.debug("Running autocommit on %r due to %r", symbol, self.state.name)
            self._commit(lock, symbol_update.new_file)
            if symbol_update.new_id == REMOVED:
                logger.warning("Editing a removed node")
                # Incredibly cursed, but keep the update around to make re-acquire succeed
                self._nodes[node_id] = symbol_update
                return
            if symbol.file._generation == symbol_update.generation:
                self._reaquire_node(symbol, node_id)
                self._nodes[node_id] = symbol_update
            else:
                new_id = (
                    node_id if (symbol_update.new_id is None) else symbol_update.new_id
                )
                self._reaquire_node(symbol, new_id)
                if symbol_update.new_id == REMOVED:
                    # Incredibly cursed, but keep the update around to make re-acquire succeed
                    self._nodes[node_id] = symbol_update
        elif symbol.is_outdated:
            # We can't re-acquire a node twice
            self._reaquire_node(symbol, node_id, missing_ok=True)

    def check_update(
        self, node: AutoCommitSymbol, lock: PendingFiles, must_be_updated: bool = True
    ) -> None:
        """Check for an update to a node if possible."""
        assert self.state is not None
        if is_on_graph(node):
            self._update_symbol(node, lock=lock)
        elif is_file(node):
            self._update_file(node, lock=lock)
        else:
            if node.is_outdated:
                if node.parent is not None:
                    self.check_update(
                        node.parent, lock=lock, must_be_updated=must_be_updated
                    )
                    if not node.is_outdated:
                        return
                if must_be_updated:
                    raise OutdatedNodeError(node)

    def set_pending_file(
        self,
        file: AutoCommitSymbol,
        *,
        update_id: NodeId | None = None,
        new_id: NodeId | None = None,
    ) -> None:
        """Mark a file as pending."""
        if update_id is None:
            update_id = file.filepath
        if new_id is not None or update_id not in self._files:
            self._files[update_id] = new_id

    def set_pending(
        self,
        node: AutoCommitSymbol,
        new_id: NodeId | None = None,
        new_file: NodeId | None = None,
    ) -> None:
        """Mark a node as pending.

        This also mark the file it's in, the file it's moved to, and it's parent if the node is
        detached
        """
        if is_file(node):
            self.set_pending_file(node, new_id=new_file)
            return
        self.set_pending_file(node, update_id=node.file_node_id)
        if new_file is not None:
            self.set_pending_file(node, update_id=new_file)
        if is_symbol(node):
            new_file_node = self.ctx.get_node(new_file) if new_file else None
            if symbol_update := self._nodes.get(node.node_id, None):
                assert symbol_update.symbol == node
                if new_id is not None:
                    logger.debug("Setting new id: %s", new_id)
                    symbol_update.new_id = new_id
                    symbol_update.new_file = new_file_node
                    symbol_update.generation = node.file._generation
            else:
                self._nodes[node.node_id] = AutoCommitNode(
                    node, node.file._generation, new_id, new_file_node
                )
        elif node.parent:
            self.set_pending(node.parent, None, None)
        else:
            logger.warning("Could not find parent node of %r", node)

    @contextmanager
    def write_state(
        self, node: AutoCommitSymbol, *, commit: bool = True, move: bool = False
    ) -> Iterator[None]:
        """Enter a write state."""
        if self.state not in (AutoCommitState.Write, None):
            # Can't write in a read or commit
            logger.error(IllegalWriteError())
        try:
            with self.lock_files({node.filepath}, all=move, commit=commit) as lock:
                old_state = self.enter_state(AutoCommitState.Write)
                self.check_update(node, lock=lock)
                yield None
                logger.debug("%r: Marking pending autoupdate", node)
                # self.set_pending(node, None)
        finally:
            self.state = old_state

    def enter_state(self, state: AutoCommitState) -> AutoCommitState | None:
        """Begin a new state."""
        old_state = self.state
        logger.debug(
            "Starting %s, previous: %s",
            state.name,
            old_state.name if old_state else None,
        )
        self.state = state
        return old_state

    @contextmanager
    def lock_files(
        self, files: set[Path], all: bool = False, commit: bool = True
    ) -> Iterator[PendingFiles]:
        to_unlock = self.try_lock_files(files, all, commit)
        try:
            yield to_unlock
        finally:
            self.unlock_files(to_unlock)

    def try_lock_files(
        self, files: set[Path], all: bool = False, commit: bool = True
    ) -> PendingFiles:
        if self._lock_all or not commit:
            return PendingFiles(set())
        if all:
            self._lock_all = True
            return PendingFiles(None, True)
        to_unlock = files - self._locked_files
        self._locked_files |= to_unlock
        return PendingFiles(to_unlock)

    def unlock_files(self, files: PendingFiles) -> None:
        if files.all:
            self._lock_all = False
        else:
            self._locked_files -= files.files

    def reset(self) -> None:
        """Reset Autocommit state.

        Probably not necessary
        """
        self._files.clear()
        self._nodes.clear()
        self._locked_files.clear()
        self.state = None
