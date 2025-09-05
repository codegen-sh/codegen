from collections.abc import Generator
from typing import TYPE_CHECKING, Generic, Self, TypeVar, override

from codegen.sdk.codebase.resolution_stack import ResolutionStack
from codegen.sdk.compiled.autocommit import reader
from codegen.sdk.core.expressions import Name
from codegen.sdk.shared.decorators.docs import noapidoc

if TYPE_CHECKING:
    from codegen.sdk.core.symbol import Symbol


Parent = TypeVar("Parent", bound="Symbol")


class DefinedName(Name[Parent], Generic[Parent]):
    """A name that defines a symbol.

    Does not reference any other names
    """

    @reader
    @noapidoc
    @override
    def _resolved_types(self) -> Generator[ResolutionStack[Self], None, None]:
        yield ResolutionStack(self)
