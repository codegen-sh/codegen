from __future__ import annotations

from typing import TYPE_CHECKING

from codegen.sdk.core.statements.for_loop_statement import ForLoopStatement
from codegen.sdk.extensions.autocommit import commiter, reader
from codegen.sdk.typescript.statements.block_statement import TSBlockStatement
from codegen.shared.decorators.docs import noapidoc, ts_apidoc

if TYPE_CHECKING:
    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.dataclasses.usage import UsageKind
    from codegen.sdk.core.detached_symbols.function_call import FunctionCall
    from codegen.sdk.core.expressions import Expression
    from codegen.sdk.core.interfaces.has_name import HasName
    from codegen.sdk.core.interfaces.importable import Importable
    from codegen.sdk.core.node_id_factory import NodeId
    from codegen.sdk.typescript.detached_symbols.code_block import TSCodeBlock


@ts_apidoc
class TSForLoopStatement(ForLoopStatement["TSCodeBlock"], TSBlockStatement["TSCodeBlock"]):
    """Abstract representation of the for loop in TypeScript.

    Attributes:
        item: An item in the iterable object. Only applicable for `for...of` loops.
        iterable: The iterable that is being iterated over. Only applicable for `for...of` loops.

        initializer: The counter variable. Applicable for traditional for loops.
        condition: The condition for the loop. Applicable for traditional for loops.
        increment: The increment expression. Applicable for traditional for loops.
    """

    # TODO: parse as statement
    item: Expression[TSForLoopStatement] | None = None
    # TODO: parse as statement
    iterable: Expression[TSForLoopStatement] | None = None

    initializer: Expression[TSForLoopStatement] | None = None
    condition: Expression[TSForLoopStatement] | None = None
    increment: Expression[TSForLoopStatement] | None = None

    def __init__(self, ts_node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: TSCodeBlock, pos: int | None = None) -> None:
        super().__init__(ts_node, file_node_id, ctx, parent, pos)
        if ts_node.type == "for_statement":
            self.initializer = self.child_by_field_name("initializer")
            self.condition = self.child_by_field_name("condition")
            self.increment = self.child_by_field_name("increment")
        elif ts_node.type == "for_in_statement":
            self.item = self.child_by_field_name("left")
            self.iterable = self.child_by_field_name("right")
        else:
            msg = f"Invalid for loop type: {ts_node.type}"
            raise ValueError(msg)

    @property
    @reader
    def is_for_in_loop(self) -> bool:
        """Determines whether the current for loop is a `for...in` loop.

        A property that identifies if the current for loop is a 'for...in' loop by checking its tree-sitter node type.

        Returns:
            bool: True if the for loop is a 'for...in' loop, False otherwise.
        """
        return self.ts_node.type == "for_in_statement"

    @property
    @reader
    def function_calls(self) -> list[FunctionCall]:
        """Retrieves all function calls within a for loop statement.

        For a for...in loop, collects function calls from the iterable expression.
        For a traditional for loop, collects function calls from the initializer,
        condition, and increment expressions. Also includes function calls from
        the superclass implementation.

        Returns:
            list[FunctionCall]: A list of all FunctionCall objects found within the for loop statement.
        """
        fcalls = []
        if self.is_for_in_loop:
            fcalls.extend(self.iterable.function_calls)
        else:
            fcalls.extend(self.initializer.function_calls)
            fcalls.extend(self.condition.function_calls)
            if self.increment:
                fcalls.extend(self.increment.function_calls)
        fcalls.extend(super().function_calls)
        return fcalls

    @noapidoc
    @commiter
    def _compute_dependencies(self, usage_type: UsageKind | None = None, dest: HasName | None = None) -> None:
        if self.is_for_in_loop:
            self.item._compute_dependencies(usage_type, dest)
            self.iterable._compute_dependencies(usage_type, dest)
        else:
            self.initializer._compute_dependencies(usage_type, dest)
            self.condition._compute_dependencies(usage_type, dest)
            if self.increment:
                self.increment._compute_dependencies(usage_type, dest)
        super()._compute_dependencies(usage_type, dest)

    @property
    @noapidoc
    def descendant_symbols(self) -> list[Importable]:
        symbols = []
        if self.is_for_in_loop:
            symbols.extend(self.item.descendant_symbols)
            symbols.extend(self.iterable.descendant_symbols)
        else:
            symbols.extend(self.initializer.descendant_symbols)
            symbols.extend(self.condition.descendant_symbols)
            if self.increment:
                symbols.extend(self.increment.descendant_symbols)
        symbols.extend(super().descendant_symbols)
        return symbols
