from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from codegen.sdk.core.interfaces.has_value import HasValue
from codegen.sdk.core.interfaces.wrapper_expression import IWrapper
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
class ExpressionStatement(Statement, HasValue, IWrapper, Generic[Parent, TCodeBlock]):
    """Abstract representation of any expression statements that resolves to an expression. In some
    languages without a statement delimiter, expression statement and the enclosed expression looks
    the same in text.

    For example, in Python:
    ```python
    x = 1
    ```
    The above code is an expression statement, but its expression value is an assignment.

    In Typescript:
    ```typescript
    x = 1;
    ```
    The above code is also an expression statement, but its expression value is an assignment excluding the semicolon.
    """

    statement_type = StatementType.EXPRESSION_STATEMENT

    def __init__(self, ts_node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: Parent, pos: int, expression_node: TSNode) -> None:
        super().__init__(ts_node, file_node_id, ctx, parent, pos=pos)
        self._value_node = self._parse_expression(expression_node)

    @property
    @reader
    def function_calls(self) -> list[FunctionCall]:
        """Get all function calls contained within this expression statement.

        Returns a list of function calls that are direct or nested within the expression of this statement. This retrieves function calls from the resolved value of the expression.

        Returns:
            list[FunctionCall]: A list of FunctionCall objects representing all function calls contained within this statement.
        """
        return self.resolve().function_calls

    @noapidoc
    @commiter
    def _compute_dependencies(self, usage_type: UsageKind, dest: HasName | None = None):
        if self._value_node:
            self.resolve()._compute_dependencies(usage_type, dest)

    def _smart_remove(self, child, *args, **kwargs) -> bool:
        return self.parent._smart_remove(child, *args, **kwargs)
