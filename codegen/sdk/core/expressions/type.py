import itertools
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

from typing_extensions import deprecated

from codegen.sdk.compiled.autocommit import reader
from codegen.sdk.core.dataclasses.usage import UsageKind
from codegen.sdk.core.expressions.expression import Expression
from codegen.sdk.core.interfaces.chainable import Chainable
from codegen.sdk.shared.decorators.docs import apidoc, noapidoc

if TYPE_CHECKING:
    from codegen.sdk.core.interfaces.editable import Editable
    from codegen.sdk.core.interfaces.importable import Importable
    from codegen.sdk.core.symbol import Symbol


Parent = TypeVar("Parent", bound="Editable")


@apidoc
class Type(Expression[Parent], Chainable, ABC, Generic[Parent]):
    """Abstract representation of a type
    Used to store the types of variables, parameters, or return values in functions, classes, etc.
    """

    @noapidoc
    @abstractmethod
    def _compute_dependencies(self, usage_type: UsageKind, dest: "Importable"): ...

    @property
    @deprecated("Use resolved_types instead for internal uses")
    @noapidoc
    @reader
    def resolved_symbol(self) -> "Symbol | str | None":
        from codegen.sdk.core.symbol import Symbol

        for resolved in self.resolved_types:
            if isinstance(resolved, Symbol):
                return resolved
        return None

    @property
    @noapidoc
    def descendant_symbols(self) -> list["Importable"]:
        """Returns the nested symbols of the importable object, including itself."""
        return list(itertools.chain.from_iterable(child.descendant_symbols for child in self.children))
