from __future__ import annotations

from typing import TYPE_CHECKING, Generic, Self, TypeVar, override

from codegen.sdk.core.autocommit import commiter, reader
from codegen.sdk.core.interfaces.chainable import Chainable
from codegen.sdk.core.placeholder.placeholder_type import TypePlaceholder
from codegen.sdk.shared.decorators.docs import apidoc, noapidoc

if TYPE_CHECKING:
    from collections.abc import Generator

    from codegen.sdk.codebase.resolution_stack import ResolutionStack
    from codegen.sdk.core.expressions.type import Type
    from codegen.sdk.core.interfaces.editable import Editable


TType = TypeVar("TType", bound="Type")
Parent = TypeVar("Parent", bound="Editable")


@apidoc
class Typeable(Chainable[Parent], Generic[TType, Parent]):
    """An interface for any node object that can be typed, eg. function parameters, variables, etc.

    Attributes:
        type: The type annotation associated with this node
    """

    type: TType | TypePlaceholder[Self]

    @commiter
    def _init_type(self, type_name: str = "type") -> None:
        self.type = self.child_by_field_name(type_name, placeholder=TypePlaceholder)

    @property
    @reader
    def is_typed(self) -> bool:
        """Indicates if a node has an explicit type annotation.

        Returns:
            bool: True if the node has an explicit type annotation, False otherwise.
        """
        return self.type

    @reader
    @noapidoc
    @override
    def _resolved_types(self) -> Generator[ResolutionStack[Self], None, None]:
        if isinstance(self.type, Chainable):
            yield from self.with_resolution_frame(self.type)
