from collections.abc import Generator
from typing import TYPE_CHECKING, Generic, Self, TypeVar, override

from tree_sitter import Node as TSNode

from codegen.sdk.codebase.resolution_stack import ResolutionStack
from codegen.sdk.core.expressions.type import Type
from codegen.sdk.core.node_id_factory import NodeId
from codegen.sdk.core.symbol_groups.collection import Collection
from codegen.sdk.extensions.autocommit import reader
from codegen.shared.decorators.docs import apidoc, noapidoc

if TYPE_CHECKING:
    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.interfaces.editable import Editable
    from codegen.sdk.core.interfaces.importable import Importable


TType = TypeVar("TType", bound="Type")
Parent = TypeVar("Parent", bound="Editable")


@apidoc
class UnionType(Collection[Type, Parent], Type[Parent], Generic[TType, Parent]):
    """An abstract representation of a union type.
    For example `str | None` or `string | number`.
    """

    def __init__(self, ts_node: TSNode, file_node_id: NodeId, ctx: "CodebaseContext", parent: Parent):
        super().__init__(ts_node, file_node_id, ctx, parent, delimiter=" |")
        elements = list(self._get_types(ts_node))
        self._init_children(elements)
        self._bracket_size = 0

    def _get_types(self, node: TSNode) -> Generator[TType, None, None]:
        for child in node.named_children:
            type_cls = self.ctx.node_classes.type_map.get(child.type, None)
            if isinstance(type_cls, type) and issubclass(type_cls, self.__class__):
                yield from self._get_types(child)
            else:
                yield self._parse_type(child)

    @reader
    @noapidoc
    @override
    def _resolved_types(self) -> Generator[ResolutionStack[Self], None, None]:
        for type in self.symbols:
            yield from self.with_resolution_frame(type)

    @property
    @noapidoc
    def descendant_symbols(self) -> list["Importable"]:
        """Returns the nested symbols of the importable object, including itself."""
        ret = []
        for param in self.symbols:
            ret.extend(param.descendant_symbols)
        return ret
