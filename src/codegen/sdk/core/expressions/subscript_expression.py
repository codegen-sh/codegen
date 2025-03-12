from collections.abc import Generator
from typing import TYPE_CHECKING, Generic, Optional, Self, TypeVar, override

from codegen.sdk.codebase.resolution_stack import ResolutionStack
from codegen.sdk.core.autocommit import reader, writer
from codegen.sdk.core.dataclasses.usage import UsageKind
from codegen.sdk.core.expressions import Name
from codegen.sdk.core.expressions.expression import Expression
from codegen.sdk.core.interfaces.resolvable import Resolvable
from codegen.sdk.extensions.autocommit import commiter
from codegen.shared.decorators.docs import apidoc, noapidoc

if TYPE_CHECKING:
    from codegen.sdk.core.interfaces.chainable import Chainable
    from codegen.sdk.core.interfaces.has_name import HasName


Object = TypeVar("Object", bound="Chainable")
Index = TypeVar("Index", bound="Expression")
Parent = TypeVar("Parent", bound="Expression")


@apidoc
class SubscriptExpression(Expression[Parent], Resolvable[Parent], Generic[Object, Index, Parent]):
    """Indexing onto an object (Aka using brackets on an object)

    Examples:
     A[]

    Attributes:
        object: The object being indexed.
        indices: A list of indices used for indexing the object.

    """

    object: Object
    indices: list[Index]

    def __init__(self, ts_node, file_node_id, ctx, parent: Parent):
        super().__init__(ts_node, file_node_id, ctx, parent=parent)
        self.object = self._parse_expression(self.ts_node.children[0], default=Name)
        self.indices = self.children[1:]

    @reader
    @noapidoc
    @override
    def _resolved_types(self) -> Generator[ResolutionStack[Self], None, None]:
        # TODO: implement this properly
        yield from self.object.resolved_type_frames

    @noapidoc
    @commiter
    def _compute_dependencies(self, usage_type: UsageKind, dest: Optional["HasName | None"] = None) -> None:
        self.object._compute_dependencies(usage_type, dest)
        for index in self.indices:
            index._compute_dependencies(usage_type, dest)

    @writer
    @noapidoc
    def rename_if_matching(self, old: str, new: str) -> None:
        if self.object:
            self.object.rename_if_matching(old, new)
