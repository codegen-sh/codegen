from typing import TYPE_CHECKING, Generic, Self, TypeVar

from tree_sitter import Node as TSNode

from codegen.sdk.core.dataclasses.usage import UsageKind
from codegen.sdk.core.expressions.expression import Expression
from codegen.sdk.core.expressions.type import Type
from codegen.sdk.core.expressions.value import Value
from codegen.sdk.core.interfaces.importable import Importable
from codegen.sdk.core.node_id_factory import NodeId
from codegen.sdk.typescript.symbol_groups.dict import TSDict, TSPair
from codegen.shared.decorators.docs import ts_apidoc
from codegen.shared.logging.get_logger import get_logger

if TYPE_CHECKING:
    from codegen.sdk.codebase.codebase_context import CodebaseContext


logger = get_logger(__name__)


Parent = TypeVar("Parent")


class TSObjectPair(TSPair, Generic[Parent]):
    """Object type

    Examples:
        a: {a: int; b?(a: int): c}
    """

    def _get_key_value(self) -> tuple[Expression[Self] | None, Expression[Self] | None]:
        from codegen.sdk.typescript.expressions.function_type import TSFunctionType

        key, value = None, None
        if self.ts_node_type == "property_signature":
            type_node = self.ts_node.child_by_field_name("type")
            value = self._parse_expression(type_node)
            key = self._parse_expression(self.ts_node.child_by_field_name("name"))
        elif self.ts_node_type == "call_signature":
            value = TSFunctionType(self.ts_node, self.file_node_id, self.ctx, self)
        elif self.ts_node_type == "index_signature":
            value = self._parse_expression(self.ts_node.child_by_field_name("type"))
            key = self._parse_expression(self.ts_node.named_children[0])
        elif self.ts_node_type == "method_signature":
            value = TSFunctionType(self.ts_node, self.file_node_id, self.ctx, self)
            key = self._parse_expression(self.ts_node.child_by_field_name("name"))
        elif self.ts_node_type == "method_definition":
            key = self._parse_expression(self.ts_node.child_by_field_name("mapped_clause_type"))
            value = self._parse_expression(self.ts_node.child_by_field_name("type"))
        else:
            key, value = super()._get_key_value()
        if isinstance(value, Value):
            # HACK: sometimes types are weird
            value = self._parse_expression(value.ts_node.named_children[0])
        elif not isinstance(value, Type):
            self._log_parse(f"{value} of type {value.__class__.__name__} from {self.ts_node} not a valid type")

        return key, value


Parent = TypeVar("Parent")


@ts_apidoc
class TSObjectType(TSDict, Type[Parent], Generic[Parent]):
    """A class representing a TypeScript object type with type annotations and dependencies.

    A specialized class extending `TSDict` and implementing `Type` for handling TypeScript object type annotations.
    This class handles object type definitions including nested type structures and manages their dependencies.
    It provides functionality for computing dependencies within the type structure and handling type relationships
    in TypeScript code.
    """

    def __init__(self, ts_node: TSNode, file_node_id: NodeId, ctx: "CodebaseContext", parent: Parent) -> None:
        super().__init__(ts_node, file_node_id, ctx, parent, delimiter=";", pair_type=TSObjectPair)

    def _compute_dependencies(self, usage_type: UsageKind, dest: Importable):
        for child in self.values():
            if isinstance(child, Type):
                child._compute_dependencies(usage_type, dest)
