from __future__ import annotations

from typing import TYPE_CHECKING, Self, override

from codegen.sdk.core.statements.try_catch_statement import TryCatchStatement
from codegen.sdk.extensions.autocommit import commiter, reader
from codegen.sdk.typescript.statements.block_statement import TSBlockStatement
from codegen.sdk.typescript.statements.catch_statement import TSCatchStatement
from codegen.shared.decorators.docs import noapidoc, ts_apidoc

if TYPE_CHECKING:
    from collections.abc import Sequence

    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.dataclasses.usage import UsageKind
    from codegen.sdk.core.detached_symbols.function_call import FunctionCall
    from codegen.sdk.core.interfaces.conditional_block import ConditionalBlock
    from codegen.sdk.core.interfaces.has_name import HasName
    from codegen.sdk.core.interfaces.importable import Importable
    from codegen.sdk.core.node_id_factory import NodeId
    from codegen.sdk.typescript.detached_symbols.code_block import TSCodeBlock


@ts_apidoc
class TSTryCatchStatement(TryCatchStatement["TSCodeBlock"], TSBlockStatement):
    """Abstract representation of the try/catch/finally block in TypeScript.

    Attributes:
        catch: The catch block.
    """

    catch: TSCatchStatement[Self] | None = None

    def __init__(self, ts_node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: TSCodeBlock, pos: int | None = None) -> None:
        super().__init__(ts_node, file_node_id, ctx, parent, pos)
        if handler_node := self.ts_node.child_by_field_name("handler"):
            self.catch = TSCatchStatement(handler_node, file_node_id, ctx, self)
        if finalizer_node := self.ts_node.child_by_field_name("finalizer"):
            self.finalizer = TSBlockStatement(finalizer_node, file_node_id, ctx, self.code_block)

    @property
    @reader
    def function_calls(self) -> list[FunctionCall]:
        """Gets all function calls within a try-catch-finally statement.

        This property retrieves all function calls from the try block, catch block (if present), and finally block (if present).

        Returns:
            list[FunctionCall]: A list of function calls found within the try-catch-finally statement, including those from
            the try block, catch block (if it exists), and finally block (if it exists).
        """
        fcalls = super().function_calls
        if self.catch:
            fcalls.extend(self.catch.function_calls)
        if self.finalizer:
            fcalls.extend(self.finalizer.function_calls)
        return fcalls

    @noapidoc
    @commiter
    def _compute_dependencies(self, usage_type: UsageKind | None = None, dest: HasName | None = None) -> None:
        super()._compute_dependencies(usage_type, dest)
        if self.catch:
            self.catch._compute_dependencies(usage_type, dest)
        if self.finalizer:
            self.finalizer._compute_dependencies(usage_type, dest)

    @property
    @noapidoc
    def descendant_symbols(self) -> list[Importable]:
        symbols = super().descendant_symbols
        if self.catch:
            symbols.extend(self.catch.descendant_symbols)
        if self.finalizer:
            symbols.extend(self.finalizer.descendant_symbols)
        return symbols

    @property
    @reader
    @override
    def nested_code_blocks(self) -> list[TSCodeBlock]:
        """Returns all nested CodeBlocks within the statement.

        Retrieves a list of all the code blocks nested within this try/catch/finally statement, including the catch and finally blocks if they exist.

        Returns:
            list[TSCodeBlock]: A list of nested code blocks, including the catch and finally blocks.
        """
        nested_blocks = super().nested_code_blocks
        if self.catch:
            nested_blocks.append(self.catch.code_block)
        if self.finalizer:
            nested_blocks.append(self.finalizer.code_block)
        return nested_blocks

    @property
    @noapidoc
    def other_possible_blocks(self) -> Sequence[ConditionalBlock]:
        if self.catch:
            return [self.catch]
        else:
            return []
