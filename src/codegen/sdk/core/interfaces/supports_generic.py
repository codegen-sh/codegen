from typing import TYPE_CHECKING, Generic, Self

from typing_extensions import TypeVar

from codegen.sdk.compiled.utils import cached_property
from codegen.sdk.core.expressions.named_type import NamedType
from codegen.sdk.core.symbol import Symbol
from codegen.sdk.core.symbol_groups.type_parameters import TypeParameters
from codegen.sdk.shared.decorators.docs import noapidoc

if TYPE_CHECKING:
    from codegen.sdk.core.expressions import Type

TType = TypeVar("TType", bound="Type")


class SupportsGenerics(Symbol, Generic[TType]):
    """A symbol that supports generics.

    Attributes:
        type_parameters: The type parameters of the symbol, if any.
    """

    type_parameters: TypeParameters[TType, Self] | None = None

    @cached_property
    @noapidoc
    def generics(self) -> dict[str, TType]:
        if self.type_parameters:
            return {param.name: param for param in self.type_parameters if isinstance(param, NamedType)}
        return {}
