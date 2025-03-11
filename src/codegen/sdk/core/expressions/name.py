from collections.abc import Generator
from typing import TYPE_CHECKING, Generic, Optional, Self, TypeVar, override

from codegen.sdk.codebase.resolution_stack import ResolutionStack
from codegen.sdk.core.autocommit import reader, writer
from codegen.sdk.core.dataclasses.usage import UsageKind
from codegen.sdk.core.expressions.expression import Expression
from codegen.sdk.core.interfaces.conditional_block import ConditionalBlock
from codegen.sdk.core.interfaces.resolvable import Resolvable
from codegen.sdk.extensions.autocommit import commiter
from codegen.shared.decorators.docs import apidoc, noapidoc

if TYPE_CHECKING:
    from codegen.sdk.core.import_resolution import Import, WildcardImport
    from codegen.sdk.core.interfaces.has_name import HasName
    from codegen.sdk.core.symbol import Symbol

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
        for used in self.resolve_name(self.source, self.start_byte):
            yield from self.with_resolution_frame(used)

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

    @noapidoc
    @reader
    def resolve_name(self, name: str, start_byte: int | None = None, strict: bool = True) -> Generator["Symbol | Import | WildcardImport"]:
        resolved_name = next(super().resolve_name(name, start_byte or self.start_byte, strict=strict), None)
        if resolved_name:
            yield resolved_name
        else:
            return

        if hasattr(resolved_name, "parent") and (conditional_parent := resolved_name.parent_of_type(ConditionalBlock)):
            top_of_conditional = conditional_parent.start_byte
            if self.parent_of_type(ConditionalBlock) == conditional_parent:
                # Use in the same block, should only depend on the inside of the block
                return
            for other_conditional in conditional_parent.other_possible_blocks:
                if cond_name := next(other_conditional.resolve_name(name, start_byte=other_conditional.end_byte_for_condition_block), None):
                    if cond_name.start_byte >= other_conditional.start_byte:
                        yield cond_name
                top_of_conditional = min(top_of_conditional, other_conditional.start_byte)

            yield from self.resolve_name(name, top_of_conditional, strict=False)
