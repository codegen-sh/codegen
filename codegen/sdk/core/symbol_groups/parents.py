from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from codegen.sdk.core.autocommit import reader
from codegen.sdk.core.dataclasses.usage import UsageKind
from codegen.sdk.core.interfaces.has_name import HasName
from codegen.sdk.core.symbol_groups.collection import Collection
from codegen.sdk.enums import EdgeType

if TYPE_CHECKING:
    from collections.abc import Iterator

    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.codebase.resolution_stack import ResolutionStack
    from codegen.sdk.core.expressions.chained_attribute import ChainedAttribute
    from codegen.sdk.core.expressions.name import Name
    from codegen.sdk.core.expressions.type import Type
    from codegen.sdk.core.interfaces.inherits import Inherits
    from codegen.sdk.core.node_id_factory import NodeId


TType = TypeVar("TType", bound="Type")
Parent = TypeVar("Parent", bound="Inherits")


class Parents(Collection["TType", Parent], Generic[TType, Parent]):
    type_arguments: list[Type]

    def __init__(self, ts_node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: Parent) -> None:
        super().__init__(ts_node, file_node_id, ctx, parent)
        self._init_children([self._parse_type(child) for child in ts_node.named_children if child.type != "type_arguments"])
        self.type_arguments = [self._parse_type(child) for child in ts_node.children if child.type == "type_arguments"]

    def __iter__(self) -> Iterator[TType]:
        return super().__iter__()

    def compute_superclass_dependencies(self) -> None:
        """Compute superclass dependencies."""
        dest = self.parent
        for superclass in self:
            resolution: list[ResolutionStack] = superclass.resolved_types
            if len(resolution) == 1 and self.ctx.has_node(getattr(resolution[0], "node_id", None)):
                self.ctx.add_edge(dest.node_id, resolution[0].node_id, type=EdgeType.SUBCLASS)
            else:
                self._log_parse("%r is ambiguous with possibilities: %r.", superclass, resolution)
        self.parent.__dict__.pop("superclasses", None)
        self.parent.__dict__.pop("constructor", None)

    def _compute_dependencies(self, usage_type: UsageKind = UsageKind.SUBCLASS, dest: HasName | None = None) -> None:
        if dest is None:
            dest = self.parent
        for superclass in self:
            superclass._compute_dependencies(UsageKind.BODY, dest)
        for type_argument in self.type_arguments:
            type_argument._compute_dependencies(UsageKind.GENERIC, dest)

    @reader
    def is_subclass_of(self, parent: str | HasName, max_depth: int | None = None) -> bool:
        """Returns True if the class is a subclass of the given parent class."""
        from codegen.sdk.core.class_definition import Class
        from codegen.sdk.core.interface import Interface

        if isinstance(parent, HasName):
            parent = parent.name
        to_search = parent.split(".")[-1]
        if to_search in (c.source.split(".")[-1] for c in self.parent_class_names):
            return True
        for parent_class in self.parent._get_superclasses(max_depth=(max_depth if max_depth is None else max_depth - 1)):
            if isinstance(parent_class, Class):
                if to_search in (c.source.split(".")[-1] for c in parent_class.parent_class_names):
                    return True
            if isinstance(parent_class, Interface) and parent_class.parent_interfaces is not None:
                if to_search in (c.name for c in parent_class.parent_interfaces):
                    return True
        return False

    @property
    @reader
    def parent_class_names(self) -> list[Name | ChainedAttribute]:
        """Returns a list of the args passed to the class (the parent classes)"""
        return [superclass.get_name() for superclass in self._symbols if isinstance(superclass, HasName)]
