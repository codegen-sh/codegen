from __future__ import annotations

from typing import Generic, TypeVar

from codegen.sdk.compiled.autocommit import reader
from codegen.sdk.core.interfaces.chainable import Chainable
from codegen.sdk.core.interfaces.editable import Editable
from codegen.sdk.enums import NodeType
from codegen.sdk.shared.decorators.docs import apidoc

Parent = TypeVar("Parent", bound="Editable")


@apidoc
class Expression(Editable[Parent], Generic[Parent]):
    """Represents an arbitrary Expression, such as List, Dict, Binary Expression, String.

    Attributes:
        node_type: The type of the node, set to NodeType.EXPRESSION.
    """

    node_type: NodeType = NodeType.EXPRESSION

    @property
    @reader
    def resolved_value(self) -> Expression | list[Expression]:
        """Returns the resolved type of an Expression.

        Returns the inferred type of the expression. For example, a function call's resolved value will be its definition.

        Returns:
            Expression | list[Expression]: The resolved expression type(s). Returns a single Expression if there is only one resolved type,
            or a list of Expressions if there are multiple resolved types. Returns self if the expression is not resolvable or has no resolved types.
        """
        if isinstance(self, Chainable) and (resolved_types := self.resolved_types):
            if len(resolved_types) == 1:
                return resolved_types[0]
            return resolved_types
        return self
