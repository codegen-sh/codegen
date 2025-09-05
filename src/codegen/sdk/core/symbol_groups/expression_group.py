from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from codegen.sdk.compiled.autocommit import reader
from codegen.sdk.core.symbol_group import SymbolGroup
from codegen.sdk.shared.decorators.docs import apidoc

if TYPE_CHECKING:
    from codegen.sdk.core.detached_symbols.function_call import FunctionCall
    from codegen.sdk.core.expressions import Expression

Parent = TypeVar("Parent")


TExpression = TypeVar("TExpression", bound="Expression")
Parent = TypeVar("Parent")


@apidoc
class ExpressionGroup(SymbolGroup[TExpression, Parent], Generic[TExpression, Parent]):
    """Group of contiguous set of expressions."""

    @property
    @reader
    def expressions(self) -> list[TExpression]:
        """Returns all expressions in the group.

        A property that returns all expressions stored in the ExpressionGroup as a list.

        Returns:
            list[TExpression]: A list of expressions contained in the group, where TExpression is a type variable bound to Expression.
        """
        return self._symbols

    @property
    @reader
    def source(self) -> str:
        """Returns the source code of the symbol group.

        Args:
            None

        Returns:
            str: The source code string for the symbol group, including all symbols within the group.
        """
        # TODO: Use _source to avoid infinite recursion
        return self.file.content[self.symbols[0].start_byte : self.symbols[-1].end_byte]

    @property
    @reader
    def function_calls(self) -> list[FunctionCall]:
        """Returns all function calls within the expression group.

        Retrieves all function calls from the expressions in this group, sets their
        parent as this group, and returns them.

        Returns:
            list[FunctionCall]: A list of all function calls found in the expressions
            of this group.
        """
        fcalls = []
        for expr in self.expressions:
            for call in expr.function_calls:
                fcalls.append(call)
        return fcalls
