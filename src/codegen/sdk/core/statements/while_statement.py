from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Generic, Self, TypeVar

from codegen.sdk.core.interfaces.has_block import HasBlock
from codegen.sdk.core.statements.statement import Statement, StatementType
from codegen.sdk.extensions.autocommit import commiter, reader
from codegen.shared.decorators.docs import apidoc, noapidoc

if TYPE_CHECKING:
    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.dataclasses.usage import UsageKind
    from codegen.sdk.core.detached_symbols.code_block import CodeBlock
    from codegen.sdk.core.detached_symbols.function_call import FunctionCall
    from codegen.sdk.core.expressions import Expression
    from codegen.sdk.core.interfaces.has_name import HasName
    from codegen.sdk.core.interfaces.importable import Importable
    from codegen.sdk.core.node_id_factory import NodeId


TCodeBlock = TypeVar("TCodeBlock", bound="CodeBlock")


@apidoc
class WhileStatement(Statement[TCodeBlock], HasBlock, ABC, Generic[TCodeBlock]):
    """Abstract representation of the while statement block.

    Attributes:
        condition: The condition expression of the while statement.
        code_block: The code block that represents the body of the while statement.
    """

    statement_type = StatementType.WHILE_STATEMENT
    condition: Expression[Self]
    code_block: TCodeBlock

    def __init__(self, ts_node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: TCodeBlock, pos: int | None = None) -> None:
        super().__init__(ts_node, file_node_id, ctx, parent, pos)
        self.code_block = self._parse_code_block()
        self.code_block.parse()

    @property
    @reader
    def nested_code_blocks(self) -> list[TCodeBlock]:
        """Returns all nested CodeBlocks within the statement.

        Returns all code blocks that are nested within the while statement. For while statements,
        this will always be a list containing only the single code block associated with the
        while statement's body.

        Returns:
            list[TCodeBlock]: A list containing the code blocks associated with this while
                statement.
        """
        return [self.code_block]

    @property
    @reader
    def function_calls(self) -> list[FunctionCall]:
        """Returns all function calls within the while statement block.

        Collects all function calls from both the condition expression and the code block.

        Returns:
            list[FunctionCall]: A list of function calls found in the while statement's condition and code block.
        """
        fcalls = self.condition.function_calls
        fcalls.extend(self.code_block.function_calls)
        return fcalls

    @noapidoc
    @commiter
    def _compute_dependencies(self, usage_type: UsageKind | None = None, dest: HasName | None = None) -> None:
        self.condition._compute_dependencies(usage_type, dest)
        self.code_block._compute_dependencies(usage_type, dest)

    @property
    @noapidoc
    def descendant_symbols(self) -> list[Importable]:
        symbols = super().descendant_symbols
        symbols.extend(self.condition.descendant_symbols)
        symbols.extend(self.code_block.descendant_symbols)
        return symbols
