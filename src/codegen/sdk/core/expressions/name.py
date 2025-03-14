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


    def _resolve_conditionals(self,conditional_parent:ConditionalBlock,name:str,original_resolved):
        search_limit = conditional_parent.start_byte_for_condition_block
        if search_limit>=original_resolved.start_byte:
            search_limit=original_resolved.start_byte-1
        if not conditional_parent.is_true_conditional(original_resolved):
            #If it's a fake conditional we must skip any potential enveloping conditionals
            def get_top_of_fake_chain(conditional,resolved,search_limit=0):
                if skip_fake:= conditional.parent_of_type(ConditionalBlock):
                    if skip_fake.is_true_conditional(resolved):
                        return skip_fake.start_byte_for_condition_block
                    search_limit=skip_fake.start_byte_for_condition_block
                    return get_top_of_fake_chain(skip_fake,conditional,search_limit)
                return search_limit
            if search_limit:=get_top_of_fake_chain(conditional_parent,original_resolved):
                search_limit=search_limit
            else:
                return

        original_conditional = conditional_parent
        while next_resolved:= next(conditional_parent.resolve_name(name,start_byte=search_limit,strict=False),None):
            yield next_resolved
            next_conditional = next_resolved.parent_of_type(ConditionalBlock)
            if not next_conditional or  next_conditional == original_conditional:
                return
            search_limit = next_conditional.start_byte_for_condition_block
            if next_conditional and not next_conditional.is_true_conditional(original_resolved):
                pass
            if search_limit>=next_resolved.start_byte:
                search_limit=next_resolved.start_byte-1
    @noapidoc
    @reader
    def resolve_name(self, name: str, start_byte: int | None = None, strict: bool = True) -> Generator["Symbol | Import | WildcardImport"]:
        resolved_name = next(super().resolve_name(name, start_byte or self.start_byte, strict=strict), None)
        if resolved_name:
            yield resolved_name
        else:
            return

        if hasattr(resolved_name, "parent") and (conditional_parent := resolved_name.parent_of_type(ConditionalBlock)):
            if self.parent_of_type(ConditionalBlock) == conditional_parent:
                # Use in the same block, should only depend on the inside of the block
                return

            yield from self._resolve_conditionals(conditional_parent=conditional_parent,name=name,original_resolved=resolved_name)
