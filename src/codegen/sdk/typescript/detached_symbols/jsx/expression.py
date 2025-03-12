from functools import cached_property
from typing import TYPE_CHECKING, Self, override

from codegen.sdk.core.autocommit import reader, writer
from codegen.sdk.core.dataclasses.usage import UsageKind
from codegen.sdk.core.expressions import Expression
from codegen.sdk.core.interfaces.editable import Editable
from codegen.sdk.core.interfaces.has_name import HasName
from codegen.sdk.core.interfaces.unwrappable import Unwrappable
from codegen.sdk.extensions.autocommit import commiter
from codegen.shared.decorators.docs import noapidoc, ts_apidoc

if TYPE_CHECKING:
    from codegen.sdk.core.function import Function
    from codegen.sdk.typescript.detached_symbols.jsx.element import JSXElement
    from codegen.sdk.typescript.detached_symbols.jsx.prop import JSXProp


@ts_apidoc
class JSXExpression(Unwrappable["Function | JSXElement | JSXProp"]):
    """Abstract representation of TSX/JSX expression"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.statement

    @cached_property
    @reader
    def statement(self) -> Editable[Self] | None:
        """Returns the editable component of this JSX expression.

        Retrieves the editable contained within this JSX expression by accessing the second child node. Returns None if the JSX expression doesn't
        contain an editable object.

        Returns:
            Editable[Self]: A Editable object representing the statement of this JSX expression. None if the object doesn't have an Editable object.
        """
        return self._parse_expression(self.ts_node.named_children[0]) if len(self.ts_node.named_children) > 0 else None

    @commiter
    @noapidoc
    @override
    def _compute_dependencies(self, usage_type: UsageKind, dest: HasName | None = None) -> None:
        if self.statement:
            self.statement._compute_dependencies(usage_type, dest=dest)

    @writer
    def reduce_condition(self, bool_condition: bool, node: Editable) -> None:
        """Simplifies a JSX expression by reducing it based on a boolean condition.


        Args:
            bool_condition (bool): The boolean value to reduce the condition to.

        """
        if self.ts_node.parent.type == "jsx_attribute" and not bool_condition:
            node.edit(self.ctx.node_classes.bool_conversion[bool_condition])
        else:
            self.remove()

    @writer
    @override
    def unwrap(self, node: Expression | None = None) -> None:
        """Removes the brackets from a JSX expression.


        Returns:
            None
        """
        from codegen.sdk.typescript.detached_symbols.jsx.element import JSXElement
        from codegen.sdk.typescript.detached_symbols.jsx.prop import JSXProp

        if node is None:
            node = self
        if isinstance(self.parent, JSXProp):
            return
        if isinstance(node, JSXExpression | JSXElement | JSXProp):
            for child in self._anonymous_children:
                child.remove()
