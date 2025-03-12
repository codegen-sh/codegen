from typing import TYPE_CHECKING, Generic, TypeVar

from codegen.sdk.core.expressions import Expression
from codegen.sdk.core.interfaces.has_value import HasValue
from codegen.sdk.core.interfaces.unwrappable import Unwrappable
from codegen.sdk.core.interfaces.wrapper_expression import IWrapper
from codegen.shared.decorators.docs import apidoc

if TYPE_CHECKING:
    from codegen.sdk.core.interfaces.editable import Editable

Parent = TypeVar("Parent", bound="Editable")


@apidoc
class Unpack(Unwrappable[Parent], HasValue, IWrapper, Generic[Parent]):
    """Unpacking of an iterable.

    Example:
        ```python
        [a, *b]
        ```
    """

    def __init__(self, ts_node, file_node_id, ctx, parent: Parent):
        super().__init__(ts_node, file_node_id, ctx, parent=parent)
        self._value_node = self.children[0]

    def unwrap(self, node: Expression | None = None) -> None:
        """Unwraps a node's content into its parent node.

        Unwraps the content of a node by removing its wrapping syntax and merging its content with its parent node.
        Specifically handles dictionary unwrapping, maintaining proper indentation and formatting.

        Args:
            node (Expression | None): The node to unwrap. If None, uses the instance's value node.

        Returns:
            None
        """
        from codegen.sdk.core.symbol_groups.dict import Dict

        node = node or self._value_node
        if isinstance(node, Dict) and isinstance(self.parent, Dict):
            if self.start_point[0] != self.parent.start_point[0]:
                self.remove(delete_formatting=False)
                self.remove_byte_range(self.start_byte - self.start_point[1], self.start_byte)
                next_sibling = self.next_sibling
                if next_sibling.source == ",":
                    next_sibling = next_sibling.next_sibling
                    indent_start = next_sibling.start_byte - next_sibling.start_point[1]
                    self.remove_byte_range(self.end_byte, next_sibling.start_byte)
                    self.insert_at(next_sibling.start_byte, self.file.content_bytes[indent_start : next_sibling.start_byte].decode("utf-8"), priority=-10)
                else:
                    # Delete the remaining characters on this line
                    self.remove_byte_range(self.end_byte, next_sibling.start_byte - next_sibling.start_point[1])

            else:
                self.remove()
            for k, v in node.items():
                self.parent[k] = v.source.strip()
            if node.unpack:
                self.parent._underlying.append(self.node.unpack.source)
