from collections import defaultdict
from collections.abc import Iterator
from typing import TYPE_CHECKING, Generic, TypeVar

from tree_sitter import Node as TSNode

from codegen.sdk.core.interfaces.editable import Editable
from codegen.sdk.core.node_id_factory import NodeId
from codegen.sdk.core.symbol_groups.collection import Collection
from codegen.shared.decorators.docs import apidoc, noapidoc

if TYPE_CHECKING:
    from codegen.sdk.codebase.codebase_context import CodebaseContext


Child = TypeVar("Child", bound=Editable)
Parent = TypeVar("Parent", bound="Editable")


@apidoc
class MultiLineCollection(Collection[Child, Parent], Generic[Child, Parent]):
    """A list containing multi-line objects.

    Example: A list of function definitions, class definitions
    You can use standard operations to operate on this list (IE len, del, append, insert, etc)
    """

    _inserts_max_size: dict[int, int]
    _leading_delimiter: str = "\n"
    _trailing_delimiter: str = "\n"

    def __init__(
        self,
        children: list[Child],
        file_node_id: NodeId,
        ctx: "CodebaseContext",
        parent: Parent,
        node: TSNode,
        indent_size: int,
        leading_delimiter: str = "\n",
        trailing_delimiter: str = "\n",
        start_byte: int | None = None,
        end_byte: int | None = None,
    ) -> None:
        super().__init__(node, file_node_id, ctx, parent, trailing_delimiter, children=children, bracket_size=0)
        self._inserts_max_size = defaultdict(lambda: 0)
        self._leading_delimiter = leading_delimiter
        self._trailing_delimiter = trailing_delimiter
        self._indent = indent_size
        self._container_start_byte = start_byte or self.ts_node.start_byte
        self._container_end_byte = end_byte or self.ts_node.end_byte + 1

    def __iter__(self) -> Iterator[Child]:
        return super().__iter__()

    def __len__(self) -> int:
        return super().__len__()

    def _get_insert_byte_from_next_sibling(self, sibling_index: int) -> int:
        # If inserting into the first sibling and the container_start_byte was specified,
        # insert at the start of the container
        if sibling_index == 0:
            return self._container_start_byte
        # Otherwise, insert at the line start of the sibling
        sibling = self.symbols[sibling_index]
        return sibling.start_byte - sibling.start_point[1]

    def _get_insert_source(self, src: str | Child, insert_idx: int) -> str:
        indent = " " * self._indent

        if isinstance(src, Child.__bound__):
            indent_size = src.start_point[1]
            src_lines = str(src.source).split("\n")
            src_lines = [f"{indent}{line}" for line in src_lines[:1]] + [line if line.strip() == "" else f"{indent}{line[indent_size:]}" for line in src_lines[1:]]
        elif isinstance(src, str):
            src = src.strip()
            src_lines = src.split("\n")
            src_lines = [line if line == "" else f"{indent}{line}" for line in src_lines]
        else:
            msg = f"Invalid source type: {type(src)}"
            raise ValueError(msg)
        src = "\n".join(src_lines)

        # Only add the leading delimiter if it's inserted before or after existing elements
        if insert_idx == 0 or insert_idx >= len(self.symbols):
            src = f"{self._leading_delimiter}{src}{self._trailing_delimiter}"
        else:
            src = f"{src}{self._trailing_delimiter}"

        # If this is the last element to insert before an existing element, add a delimiter
        if insert_idx == len(self.symbols) - 1 and self._inserts[insert_idx] == self._inserts_max_size[insert_idx]:
            src = f"{src}{self._leading_delimiter}"
        return src

    @noapidoc
    def _incr_insert_size(self, index: int) -> None:
        super()._incr_insert_size(index)
        self._inserts_max_size[index] = max(self._inserts[index], self._inserts_max_size[index])
