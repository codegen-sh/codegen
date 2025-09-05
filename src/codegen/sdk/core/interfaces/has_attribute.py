from abc import abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from codegen.sdk.core.interfaces.editable import Editable


Attribute = TypeVar("Attribute", bound="Editable")


class HasAttribute(Generic[Attribute]):
    @abstractmethod
    def resolve_attribute(self, name: str) -> Attribute | None:
        """Resolve an attribute belonging to this object."""
        pass
