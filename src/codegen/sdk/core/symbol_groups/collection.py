from collections import defaultdict
from collections.abc import Iterable, Iterator, MutableSequence
from typing import TYPE_CHECKING, Any, Generic, TypeVar, overload

from tree_sitter import Node as TSNode

from codegen.sdk.codebase.transactions import TransactionPriority
from codegen.sdk.core.autocommit import reader, writer
from codegen.sdk.core.interfaces.editable import Editable
from codegen.sdk.core.node_id_factory import NodeId
from codegen.sdk.core.symbol_group import SymbolGroup
from codegen.shared.decorators.docs import noapidoc

if TYPE_CHECKING:
    from codegen.sdk.codebase.codebase_context import CodebaseContext


Child = TypeVar("Child", bound="Editable")
Parent = TypeVar("Parent")


class Collection(SymbolGroup[Child, Parent], MutableSequence[Child], Generic[Child, Parent]):
    """Ordered collection of nodes
    Attributes:
        _bracket_size: Number of characters wrapping the collection
    """

    _elements: int
    _reversed: set[int]
    _inserts: dict[int, int]
    _pending_removes: int = 0

    _delimiter: str
    _indent: int = 0
    _bracket_size: int = 1
    _container_start_byte: int
    _container_end_byte: int

    def __init__(self, node: TSNode, file_node_id: NodeId, ctx: "CodebaseContext", parent: Parent, delimiter: str = ",", children: list[Child] | None = None, *, bracket_size: int = 1) -> None:
        super().__init__(file_node_id, ctx, parent, node)
        self._delimiter = delimiter
        self._reversed = set()
        self._inserts = defaultdict(lambda: 0)
        self._container_start_byte = self.ts_node.start_byte
        self._container_end_byte = self.ts_node.end_byte
        self._bracket_size = bracket_size
        if children is not None:
            self._init_children(children)

    def _init_children(self, symbols: list[Child]):
        """Call this after setting self._symbols."""
        if self.ts_node.start_point[0] != self.ts_node.end_point[0] and symbols:
            # This is a multiline collection.
            self._indent = symbols[0].ts_node.start_point[1]
            self._delimiter += "\n"
        else:
            self._delimiter += " "
        self._elements = len(symbols)
        self._symbols = symbols
        self._original_children = symbols.copy()

    @overload
    def __setitem__(self, key: int, value: str | Child) -> None: ...

    @overload
    def __setitem__(self, key: slice, value: Iterable[Child] | Iterable[str]) -> None: ...

    @writer
    def __setitem__(self, key: int | slice, value: str | Child | Iterable[Child] | Iterable[str]) -> None:
        if isinstance(key, slice):
            assert isinstance(value, Iterable)
            for idx, item in zip(range(key.start, key.stop, key.step), value):
                self[idx] = item
        else:
            assert not isinstance(value, Iterable)
            if isinstance(value, Editable):
                value = value.source
            self.symbols[key].edit(value)

    @writer
    def __delitem__(self, key: int | slice) -> None:
        if isinstance(key, slice):
            for i in reversed(range(key.start, key.stop, key.step)):
                del self[i]
        else:
            self.symbols[key].remove(delete_formatting=True)
            del self.symbols[key]

    def __iter__(self) -> Iterator[Child]:
        return super().__iter__()

    @reader
    def __len__(self) -> int:
        return self._elements + self._inserts_till()

    @writer
    def remove(self, value: Child | None = None, *args, **kwargs) -> None:
        """Removes an element from a Collection.

        Deletes the specified element from the Collection by calling its remove method. If no value is specified,
        delegates to the parent class's remove method.

        Args:
            value (Child | None): The element to remove from the Collection. If None, delegates to parent class.
            *args: Variable length argument list to pass to the remove method.
            **kwargs: Arbitrary keyword arguments to pass to the remove method.

        Returns:
            None: This method doesn't return anything.
        """
        # Your custom remove logic goes here
        # For example, let's remove all occurrences of the value instead of just the first one
        if value is None:
            super().remove(*args, **kwargs)
            Editable.remove(self, *args, **kwargs)
        else:
            value.remove(*args, **kwargs)

    def _inserts_till(self, max_idx: int | None = None) -> int:
        """Find the number of pending inserts until max_idx."""
        return sum(inserts for idx, inserts in self._inserts.items() if (max_idx is None or idx < max_idx))

    @writer
    def insert(self, index: int, value: str | Child) -> None:
        """Adds `value` to the container that this node represents
        Args:
            value: source to add
            index: If  provided, the `value` will be inserted at that index, otherwise will default to end of the list.
        """
        if index < 0:
            index = len(self) - index
        # If index is not specified, insert at the end of the list
        if self._elements == 0:
            insert_byte = self._container_start_byte + self._bracket_size
        elif index - self._inserts_till(index) >= self._elements:
            # If inserting at end of the list, insert before the closing container character
            insert_byte = self._container_end_byte - self._bracket_size
        else:
            # If inserting in the middle of the list, insert before the next sibling
            sibling_index = index - self._inserts_till(index)
            insert_byte = self._get_insert_byte_from_next_sibling(sibling_index)
        insert_idx = index
        # insert_idx = min(index, len(self.symbols) - self.pending_removes)
        self._incr_insert_size(insert_idx)
        insert_number = self._inserts[insert_idx]
        # Case 1: Insert occuring before the last element, should be reversed
        if insert_byte < self._container_end_byte - self._bracket_size:
            self._reversed.add(insert_idx)
        elif len(self.source) > 1 and self._bracket_size > 0:
            remaining = self.source[: -self._bracket_size].rstrip()
            # Case 2: Last element ends with the delimiter, reverse for this insert
            if remaining.endswith(self._delimiter.rstrip()):
                self._reversed.add(insert_idx)
            # Case 3: A spread element was deleted and we must respect that
            elif insert_number == 1:
                if (relative_byte := remaining.rfind(self._delimiter)) != -1:
                    delim_byte = relative_byte + self.start_byte + len(self._delimiter)
                    element_deleted = self.transaction_manager.get_transactions_at_range(self.file.path, delim_byte, self.start_byte + len(remaining), TransactionPriority.Remove, combined=True)
                    delimeter_deleted = self.transaction_manager.get_transactions_at_range(self.file.path, delim_byte - len(self._delimiter), delim_byte, TransactionPriority.Remove, combined=True)
                    if element_deleted and not delimeter_deleted:
                        # Adjust the insert to insert at the correct location
                        insert_byte = delim_byte
                        self._reversed.add(insert_idx)

        def get_source() -> str:
            return self._get_insert_source(value, insert_idx)

        def incr_elements() -> None:
            self._inserts[insert_idx] -= 1
            self._elements += 1
            self._mark_dirty()

        # We want right -> left ordering
        # Therefore, we go by highest index then insert the lowest insert number on the same index
        super().insert_at(insert_byte, get_source, priority=(-index, +insert_number), exec_func=incr_elements)

    def _get_insert_byte_from_next_sibling(self, sibling_index: int) -> int:
        return self.symbols[sibling_index].start_byte

    def _get_insert_source(self, src: Any, insert_idx: int) -> str:
        elements = self._elements - self._pending_removes
        if elements == 0:
            # Further inserts to this index are reversed
            self._reversed.add(insert_idx)
            # If list is empty, insert after the opening container character
            return str(src)
        # Check if this index is reversed
        # Additionally, if it isn't, check if the next one is
        elif insert_idx in self._reversed or (insert_idx + 1) in self._reversed:
            self._reversed.add(insert_idx)
            # Insert in the middle, reverse the delimiter
            return f"{' ' * self._indent}{src}{self._delimiter}"
        else:
            # If inserting at the end of the list
            return f"{self._delimiter}{src}"

    @noapidoc
    def _incr_insert_size(self, index: int) -> None:
        self._inserts[index] += 1

    @noapidoc
    def _removed_child_commit(self) -> None:
        self._mark_dirty()
        self._elements -= 1
        self._pending_removes -= 1

    @noapidoc
    def _removed_child(self) -> None:
        self._mark_dirty()
        self._pending_removes += 1

    @property
    @reader
    def source(self) -> str:
        """Get the source code content of the node.

        Retrieves the underlying source code content associated with this node as stored in the _source attribute.

        Returns:
            str: The source code content of the node.
        """
        return self._source

    @source.setter
    @writer
    def source(self, value) -> None:
        """Set the source of the Editable instance by calling .edit(..)"""
        if self.source != value:
            self.edit(value)

    @writer
    def edit(self, *args, **kwargs) -> None:
        """Edit the source for this Collection instance.

        This method is used to update the source of a Collection while preserving its start and end brackets. It is primarily used internally by
        Collection to maintain structural integrity during edits.

        Args:
            *args: Variable length argument list passed to the parent Editable class's edit method.
            **kwargs: Arbitrary keyword arguments passed to the parent Editable class's edit method.

        Returns:
            None
        """
        return Editable.edit(self, *args, **kwargs)  # HACK: keep start/end brackets

    @property
    @reader
    @noapidoc
    def uncommitted_len(self):
        """Get the len of this list including pending removes and adds."""
        return len(self) - self._pending_removes

    @reader
    def index(self, value: Child, start: int = 0, stop: int | None = None) -> int:
        """Return the index of the first occurrence of value.

        Returns -1 if value is not present.
        """
        if stop is None:
            stop = len(self)
        ts_node = value if isinstance(value, TSNode) else value.ts_node
        try:
            return [x.ts_node for x in self.symbols].index(ts_node, start, stop)
        except ValueError:
            return -1

    @noapidoc
    def _mark_dirty(self):
        self.transaction_manager.pending_undos.add(self.reset)

    @noapidoc
    def reset(self):
        self._pending_removes = 0
        self._elements = len(self._original_children)
        self._symbols = self._original_children.copy()
        self._inserts.clear()
        self._reversed.clear()

    def _smart_remove(self, child, *args, **kwargs) -> bool:
        return self.parent._smart_remove(self, child, *args, **kwargs)
