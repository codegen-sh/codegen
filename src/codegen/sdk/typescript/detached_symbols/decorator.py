from __future__ import annotations

from typing import TYPE_CHECKING

from codegen.sdk.core.autocommit import reader
from codegen.sdk.core.detached_symbols.decorator import Decorator
from codegen.sdk.core.detached_symbols.function_call import FunctionCall
from codegen.shared.decorators.docs import ts_apidoc

if TYPE_CHECKING:
    from tree_sitter import Node as TSNode

    from codegen.sdk.typescript.class_definition import TSClass
    from codegen.sdk.typescript.detached_symbols.parameter import TSParameter
    from codegen.sdk.typescript.function import TSFunction


@ts_apidoc
class TSDecorator(Decorator["TSClass", "TSFunction", "TSParameter"]):
    """Abstract representation of a Decorator"""

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
            elif child.type == "member_expression":
                return child

            # =====[ Call ]=====
            # e.g. `@a.b()`
            elif child.type == "call_expression":
                func = child.child_by_field_name("function")
                return func

        msg = f"Could not find decorator name within {self.source}"
        raise ValueError(msg)

    @property
    @reader
    def call(self) -> FunctionCall | None:
        """Retrieves the function call expression associated with the decorator.

        This property checks if the decorator has a function call expression (e.g., @decorator()) and returns it as a FunctionCall object.
        If the decorator is a simple identifier (e.g., @decorator), returns None.

        Returns:
            FunctionCall | None: A FunctionCall object representing the decorator's call expression if present, None otherwise.
        """
        if call_node := next((x for x in self.ts_node.named_children if x.type == "call_expression"), None):
            return FunctionCall(call_node, self.file_node_id, self.ctx, self.parent)
        return None
