from typing import TYPE_CHECKING, Generic, Self, TypeVar

from tree_sitter import Node as TSNode

from codegen.sdk.core.expressions.generic_type import GenericType
from codegen.sdk.core.symbol_groups.collection import Collection
from codegen.sdk.python.expressions.named_type import PyNamedType
from codegen.shared.decorators.docs import py_apidoc
from codegen.shared.logging.get_logger import get_logger

if TYPE_CHECKING:
    from codegen.sdk.python.expressions.type import PyType

logger = get_logger(__name__)


Parent = TypeVar("Parent")


@py_apidoc
class PyGenericType(PyNamedType[Parent], GenericType["PyType", Parent], Generic[Parent]):
    """Generic python type.

    Examples:
        list[int]
    """

    def _get_name_node(self) -> TSNode | None:
        if self.ts_node_type == "subscript":
            return self.ts_node.child_by_field_name("value")
        if self.ts_node_type == "generic_type":
            return self.child_by_field_types(["identifier", "attribute"]).ts_node
        return self.ts_node

    def _get_parameters(self) -> Collection["PyType", Self] | None:
        if self.ts_node_type == "subscript":
            types = [self._parse_type(child) for child in self.ts_node.children_by_field_name("subscript")]
            return Collection(node=self.ts_node, file_node_id=self.file_node_id, ctx=self.ctx, parent=self, children=types)
        elif self.ts_node_type == "generic_type":
            type_parameter = self.ts_node.named_children[1]
            assert type_parameter.type == "type_parameter"
            types = [self._parse_type(child) for child in type_parameter.named_children]
            return Collection(node=type_parameter, file_node_id=self.file_node_id, ctx=self.ctx, parent=self, children=types)
        logger.warning(f"Type {self.ts_node_type} not implemented")
        return None
