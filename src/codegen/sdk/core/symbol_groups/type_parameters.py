from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from codegen.sdk.core.symbol_groups.collection import Collection

if TYPE_CHECKING:
    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.expressions.type import Type
    from codegen.sdk.core.interfaces.supports_generic import SupportsGenerics
    from codegen.sdk.core.node_id_factory import NodeId


TType = TypeVar("TType", bound="Type")
Parent = TypeVar("Parent", bound="SupportsGenerics")


class TypeParameters(Collection["TType", Parent], Generic[TType, Parent]):
    def __init__(self, ts_node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: Parent) -> None:
        super().__init__(ts_node, file_node_id, ctx, parent)
        self._init_children([self._parse_type(child) for child in ts_node.named_children])
