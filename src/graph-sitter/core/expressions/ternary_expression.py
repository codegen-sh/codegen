import itertools
from collections.abc import Generator
from typing import Generic, Self, TypeVar, override

from codegen.sdk.codebase.resolution_stack import ResolutionStack
from codegen.sdk.compiled.autocommit import commiter, reader
from codegen.sdk.core.autocommit import writer
from codegen.sdk.core.dataclasses.usage import UsageKind
from codegen.sdk.core.expressions import Expression
from codegen.sdk.core.interfaces.chainable import Chainable
from codegen.sdk.core.interfaces.editable import Editable
from codegen.sdk.core.interfaces.has_name import HasName
from codegen.sdk.core.interfaces.importable import Importable
from codegen.sdk.core.interfaces.unwrappable import Unwrappable
from codegen.sdk.shared.decorators.docs import apidoc, noapidoc

Parent = TypeVar("Parent", bound="Editable")


@apidoc
class TernaryExpression(Expression[Parent], Chainable, Generic[Parent]):
    """Any ternary expression in the code where a condition will determine branched execution.

    Attributes:
        condition: The condition expression that determines which branch to execute.
        consequence: The expression to execute if the condition is true.
        alternative: The expression to execute if the condition is false.
    """

    condition: Expression[Self] | None
    consequence: Expression[Self] | None
    alternative: Expression[Self] | None

    @writer
    def reduce_condition(self, bool_condition: bool, node: Editable | None = None) -> None:
        """Simplifies a ternary expression based on a boolean condition.

        Args:
            bool_condition (bool): The boolean value to reduce the condition to. If True, keeps the consequence branch. If False, keeps the alternative branch.
            node (Editable | None, optional): The node to be edited. Defaults to None.

        Returns:
            None: Modifies the ternary expression in place.
        """
        # ==== [ Reduce condition to True ] ====
        to_keep = self.consequence if bool_condition else self.alternative
        for node in self._anonymous_children:
            node.remove()
        self.condition.remove()
        if bool_condition:
            self.alternative.remove()
        else:
            self.consequence.remove()
            self.remove_byte_range(self.alternative.ts_node.prev_sibling.end_byte, self.alternative.start_byte)
        if isinstance(to_keep, Unwrappable):
            to_keep.unwrap()
        if isinstance(self.parent, Unwrappable):
            self.parent.unwrap(to_keep)

    @reader
    @noapidoc
    @override
    def _resolved_types(self) -> Generator[ResolutionStack[Self], None, None]:
        yield from self.with_resolution_frame(self.consequence)
        yield from self.with_resolution_frame(self.alternative)

    @property
    @noapidoc
    def descendant_symbols(self) -> list[Importable]:
        elems = [self.condition, self.consequence, self.alternative]
        return list(itertools.chain.from_iterable(elem.descendant_symbols for elem in elems if elem))

    @noapidoc
    @commiter
    def _compute_dependencies(self, usage_type: UsageKind | None = None, dest: HasName | None = None) -> None:
        self.condition._compute_dependencies(usage_type, dest)
        self.consequence._compute_dependencies(usage_type, dest)
        self.alternative._compute_dependencies(usage_type, dest)
