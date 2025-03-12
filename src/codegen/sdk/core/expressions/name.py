from collections.abc import Generator
from typing import TYPE_CHECKING, Generic, Optional, Self, TypeVar, override

from codegen.sdk.codebase.resolution_stack import ResolutionStack
from codegen.sdk.core.autocommit import reader, writer
from codegen.sdk.core.dataclasses.usage import UsageKind
from codegen.sdk.core.expressions.expression import Expression
from codegen.sdk.core.interfaces.resolvable import Resolvable
from codegen.sdk.extensions.autocommit import commiter
from codegen.shared.decorators.docs import apidoc, noapidoc

if TYPE_CHECKING:
    from codegen.sdk.core.interfaces.has_name import HasName


Parent = TypeVar("Parent", bound="Expression")


@apidoc
class Name(Expression[Parent], Resolvable, Generic[Parent]):
    """Editable attribute on any given code objects that has a name.

    For example, function, classes, global variable, interfaces, attributes, parameters are all
    composed of a name.
    """

    @reader
    @noapidoc
    @override
    def _resolved_types(self) -> Generator[ResolutionStack[Self], None, None]:
        """Resolve the types used by this symbol."""
        if used := self.resolve_name(self.source, self.start_byte):
            yield from self.with_resolution_frame(used)

    @noapidoc
    @commiter
    def _compute_dependencies(self, usage_type: UsageKind, dest: Optional["HasName | None "] = None) -> None:
        """Compute the dependencies of the export object."""
        edges = []
        for used_frame in self.resolved_type_frames:
            edges.extend(used_frame.get_edges(self, usage_type, dest, self.ctx))
        if self.ctx.config.debug:
            edges = list(dict.fromkeys(edges))
        self.ctx.add_edges(edges)

    @noapidoc
    @writer
    def rename_if_matching(self, old: str, new: str):
        if self.source == old:
            self.edit(new)
