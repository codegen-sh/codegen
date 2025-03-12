from collections.abc import Generator
from dataclasses import dataclass, field
from functools import cached_property
from typing import TYPE_CHECKING, Generic

from typing_extensions import TypeVar

from codegen.sdk.core.dataclasses.usage import Usage, UsageKind, UsageType
from codegen.sdk.core.interfaces.editable import Editable
from codegen.sdk.enums import Edge, EdgeType

if TYPE_CHECKING:
    from codegen.sdk.core.import_resolution import Import

NodeType = TypeVar("NodeType", bound=Editable)


@dataclass(frozen=True)
class ResolutionStack(Generic[NodeType]):
    """Represents the resolution stack from a symbol to a usage

    Symbol
    ...
    <Imports, Assignments, Etc>

    Attributes:
        aliased: If this was aliased at any point
        parent_frame: The frame above this frame
    """

    node: NodeType = field(repr=False)
    parent_frame: "ResolutionStack | None" = None
    direct: bool = True
    aliased: bool = False
    chained: bool = False
    generics: dict = field(default_factory=dict)

    def with_frame(self, node, direct: bool = True, aliased: bool = False, chained: bool = False, generics: dict | None = None) -> "ResolutionStack":
        """Adds node to the Resolution stack and returns it as a new frame."""
        assert node is not None
        if not generics:
            generics = self.generics
        return ResolutionStack(node, self, direct, aliased, chained, generics=generics)

    def usage_type(self, direct: bool, aliased: bool, chained: bool) -> UsageType:
        if chained:
            return UsageType.CHAINED
        elif direct:
            return UsageType.DIRECT
        elif aliased:
            return UsageType.ALIASED
        else:
            return UsageType.INDIRECT

    def get_edges(
        self,
        match: "Editable",
        usage_type: UsageKind,
        dest: "HasName",
        codebase_context: "CodebaseContext",
        *,
        direct: bool = True,
        aliased: bool = False,
        chained: bool = False,
        imported_by: Import | None = None,
    ) -> Generator[(int, int, Edge), None, None]:
        """Get usage edges for a given node."""
        # Only add nodes that are already on the graph
        edge_usage_type = self.usage_type(direct, aliased, chained)
        if hasattr(self.node, "node_id") and codebase_context.has_node(getattr(self.node, "node_id")):
            usage = Usage(kind=usage_type, match=match, usage_type=edge_usage_type, usage_symbol=dest.parent_symbol, imported_by=imported_by)
            yield dest.node_id, self.node.node_id, Edge(type=EdgeType.SYMBOL_USAGE, usage=usage)
        if self.parent_frame is not None:
            from codegen.sdk.core.import_resolution import Import

            if isinstance(self, Import):
                imported_by = self
            aliased = self.aliased or aliased
            direct = self.direct and direct
            chained = self.chained or (chained and self.direct)
            yield from self.parent_frame.get_edges(match, usage_type, dest, codebase_context, direct=direct, aliased=aliased, chained=chained, imported_by=imported_by)

    def add_usage(self, match: "Editable", usage_type: UsageKind, dest: "HasName", codebase_context: "CodebaseContext", *, direct: bool = True, aliased: bool = False, chained: bool = False) -> None:
        """Add the resolved type to the graph. Also adds any intermediate nodes as usages as well if they are on the graph."""
        # Only add nodes that are already on the graph
        codebase_context.add_edges(list(self.get_edges(match, usage_type, dest, codebase_context, direct=direct, aliased=aliased, chained=chained)))

    @cached_property
    def top(self) -> ResolutionStack:
        if self.parent_frame is not None:
            return self.parent_frame.top
        return self

    @cached_property
    def is_direct_usage(self) -> bool:
        return self.direct and (self.parent_frame is None or self.parent_frame.is_direct_usage)

    def with_new_base(self, base: Editable, *args, **kwargs) -> ResolutionStack:
        new_parent = ResolutionStack(base, *args, **kwargs)
        return self.with_new_base_frame(new_parent)

    def with_new_base_frame(self, base: ResolutionStack) -> ResolutionStack:
        if self.parent_frame is not None:
            new_parent = self.parent_frame.with_new_base_frame(base)
        else:
            new_parent = base
        return new_parent.with_frame(self.node, direct=self.direct, aliased=self.aliased)
