from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from codegen.sdk.core.interfaces.has_value import HasValue
from codegen.sdk.core.statements.statement import Statement, StatementType
from codegen.sdk.extensions.autocommit import commiter, reader
from codegen.shared.decorators.docs import apidoc, noapidoc

if TYPE_CHECKING:
    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.dataclasses.usage import UsageKind
    from codegen.sdk.core.detached_symbols.code_block import CodeBlock
    from codegen.sdk.core.detached_symbols.function_call import FunctionCall
    from codegen.sdk.core.interfaces.has_block import HasBlock
    from codegen.sdk.core.interfaces.has_name import HasName
    from codegen.sdk.core.node_id_factory import NodeId


Parent = TypeVar("Parent", bound="HasBlock")
TCodeBlock = TypeVar("TCodeBlock", bound="CodeBlock")


@apidoc
class ReturnStatement(Statement, HasValue, Generic[Parent, TCodeBlock]):
    """Abstract representation of return statements, e.g. in Python:

    Example:
        def f(x):
            if x:
            return x**2  # ReturnStatement
        else:
            return 1  # ReturnStatement
    """

    statement_type = StatementType.RETURN_STATEMENT

    def __init__(self, ts_node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: Parent, pos: int | None = None) -> None:
        super().__init__(ts_node, file_node_id, ctx, parent, pos)
        value_node = self._get_value_node()
        self._value_node = self._parse_expression(value_node) if value_node else None

    def _get_value_node(self) -> TSNode | None:
        if len(self.ts_node.children) == 1:
            return None
        return self.ts_node.children[1]

    @property
    @reader
    def function_calls(self) -> list[FunctionCall]:
        """Returns a list of function calls contained within this return statement.

        If the return statement has no value, an empty list is returned. Otherwise, returns the function calls contained in the value expression of the return statement.

        Returns:
            list[FunctionCall]: A list of function calls contained in the return statement's value expression.
        """
        if not self.value:
            return []
        return self.value.function_calls

    @noapidoc
    @commiter
    def _compute_dependencies(self, usage_type: UsageKind | None = None, dest: HasName | None = None) -> None:
        if self.value:
            self.value._compute_dependencies(usage_type, dest)
