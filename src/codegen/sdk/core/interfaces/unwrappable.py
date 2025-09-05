from abc import abstractmethod
from typing import Generic

from typing_extensions import TypeVar

from codegen.sdk.core.expressions import Expression
from codegen.sdk.core.interfaces.editable import Editable
from codegen.sdk.shared.decorators.docs import apidoc

Parent = TypeVar("Parent", bound=Editable)


@apidoc
class Unwrappable(Expression[Parent], Generic[Parent]):
    """An abstract representation of an expression that can be unwrapped.
    Expressions that can be unwrapped include binary expressions and ternary expressions.
    """

    @abstractmethod
    def unwrap(self, node: Expression | None = None) -> None:
        """Unwrap this expression, removing parenthesis and other syntax elements while maintaining the function of the code.

        Args:
            node: the node that's remaining. If None, assume all children of this expression are kept
        """
