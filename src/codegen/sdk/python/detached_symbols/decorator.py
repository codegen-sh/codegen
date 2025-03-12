from __future__ import annotations

from typing import TYPE_CHECKING

from codegen.sdk.core.autocommit import reader
from codegen.sdk.core.detached_symbols.decorator import Decorator
from codegen.sdk.core.detached_symbols.function_call import FunctionCall
from codegen.shared.decorators.docs import py_apidoc

if TYPE_CHECKING:
    from tree_sitter import Node as TSNode

    from codegen.sdk.python.class_definition import PyClass
    from codegen.sdk.python.detached_symbols.parameter import PyParameter
    from codegen.sdk.python.function import PyFunction


@py_apidoc
class PyDecorator(Decorator["PyClass", "PyFunction", "PyParameter"]):
    """Extends Decorators for Python codebases."""

    @reader
    def _get_name_node(self) -> TSNode:
        """Returns the name of the decorator."""
        for child in self.ts_node.children:
            # =====[ Identifier ]=====
            # Just `@dataclass` etc.
            if child.type == "identifier":
                return child

            # =====[ Attribute ]=====
            # e.g. `@a.b`
            elif child.type == "attribute":
                return child

            # =====[ Call ]=====
            # e.g. `@a.b()`
            elif child.type == "call":
                func = child.child_by_field_name("function")
                return func

        msg = f"Could not find decorator name within {self.source}"
        raise ValueError(msg)

    @property
    @reader
    def call(self) -> FunctionCall | None:
        """Gets the function call node from the decorator if the decorator is a call.

        This property retrieves the FunctionCall instance if the decorator is a function call
        (e.g., @decorator()), otherwise returns None for simple decorators (e.g., @decorator).

        Args:
            None

        Returns:
            FunctionCall | None: A FunctionCall instance if the decorator is a function call,
            None if it's a simple decorator.
        """
        if call_node := next((x for x in self.ts_node.named_children if x.type == "call"), None):
            return FunctionCall(call_node, self.file_node_id, self.ctx, self.parent)
        return None
