from __future__ import annotations

from abc import abstractmethod
from functools import cached_property
from typing import TYPE_CHECKING, Generic, Self, TypeVar

from codegen.sdk._proxy import proxy_property
from codegen.sdk.core.autocommit import reader, writer
from codegen.sdk.core.dataclasses.usage import UsageKind
from codegen.sdk.core.function import Function
from codegen.sdk.core.interfaces.conditional_block import ConditionalBlock
from codegen.sdk.core.statements.statement import Statement, StatementType
from codegen.sdk.extensions.autocommit import commiter
from codegen.shared.decorators.docs import apidoc, noapidoc

if TYPE_CHECKING:
    from collections.abc import Sequence

    from codegen.sdk.core.detached_symbols.code_block import CodeBlock
    from codegen.sdk.core.detached_symbols.function_call import FunctionCall
    from codegen.sdk.core.expressions import Expression
    from codegen.sdk.core.interfaces.editable import Editable
    from codegen.sdk.core.interfaces.has_name import HasName
    from codegen.sdk.core.interfaces.importable import Importable


TIfBlockStatement = TypeVar("TIfBlockStatement", bound="IfBlockStatement")
TCodeBlock = TypeVar("TCodeBlock", bound="CodeBlock")


@apidoc
class IfBlockStatement(ConditionalBlock, Statement[TCodeBlock], Generic[TCodeBlock, TIfBlockStatement]):
    """Abstract representation of the if/elif/else if/else statement block.

    For example, if there is a code block like:
    if condition1:
        block1
    elif condition2:
        block2
    else:
        block3
    This class represents the entire block, including the conditions and nested code blocks.

    Attributes:
        condition: The condition expression for the if block. None if the block is an else block.
        consequence_block: The code block that is executed if the condition is True.
    """

    statement_type = StatementType.IF_BLOCK_STATEMENT
    condition: Expression[Self] | None
    consequence_block: TCodeBlock
    _alternative_blocks: list[TIfBlockStatement] | None  # None if it is an elif or else block
    _main_if_block: TIfBlockStatement

    @abstractmethod
    def _parse_consequence_block(self) -> TCodeBlock: ...

    @abstractmethod
    def _parse_alternative_blocks(self) -> list[TIfBlockStatement]:
        """Returns the alternative blocks if they exist.

        Otherwise, returns empty list. This includes both elif and else blocks.
        """

    @commiter
    @noapidoc
    def _compute_dependencies(self, usage_type: UsageKind = UsageKind.BODY, dest: HasName | None = None) -> None:
        # Compute dependencies for all statements in the nested code blocks
        if self.condition:
            self.condition._compute_dependencies(usage_type, dest)

        self.consequence_block._compute_dependencies(usage_type, dest)

        for alt_block in self.alternative_blocks:
            if alt_block.condition:
                alt_block.condition._compute_dependencies(usage_type, dest)
            alt_block.consequence_block._compute_dependencies(usage_type, dest)

    @property
    @reader
    def function_calls(self) -> list[FunctionCall]:
        """Returns all function calls within the if block statement and its alternative blocks.

        Collects all function calls from the if block's condition, consequence block, and any alternative blocks (elif/else)
        including their conditions and consequence blocks.

        Returns:
            list[FunctionCall]: A list of function call objects found within this if block statement and its alternative blocks.
        """
        fcalls = [] if self.condition is None else self.condition.function_calls
        fcalls.extend(self.consequence_block.function_calls)
        for alt_block in self.alternative_blocks:
            if alt_block.condition:
                fcalls.extend(alt_block.condition.function_calls)
            fcalls.extend(alt_block.consequence_block.function_calls)
        return fcalls

    @property
    @noapidoc
    def descendant_symbols(self) -> list[Importable]:
        symbols = super().descendant_symbols
        if self.condition:
            symbols.extend(self.condition.descendant_symbols)
        if self.consequence_block:
            symbols.extend(self.consequence_block.descendant_symbols)
        for alt_block in self.alternative_blocks:
            if alt_block.condition:
                symbols.extend(alt_block.condition.descendant_symbols)
            if alt_block.consequence_block:
                symbols.extend(alt_block.consequence_block.descendant_symbols)
        return symbols

    @cached_property
    @reader
    def nested_code_blocks(self) -> list[TCodeBlock]:
        """Returns all nested code blocks within an if/elif/else statement block.

        Returns a list of all CodeBlocks that are part of the current if/elif/else statement block, including the main if block's consequence block
        and all alternative (elif/else) blocks' consequence blocks.

        Returns:
            list[TCodeBlock]: A list of CodeBlock objects representing all nested code blocks within the statement.
        """
        return [self.consequence_block] + [x.consequence_block for x in self.alternative_blocks]

    @property
    @abstractmethod
    def is_if_statement(self) -> bool:
        """Returns whether the current block is an if block.

        A property that checks if the current block within an if/elif/else statement chain is an if block.
        This includes the main if block but not elif or else blocks.

        Args:
            None

        Returns:
            bool: True if the current block is an if block, False if it is an elif or else block.
        """

    @property
    @abstractmethod
    def is_else_statement(self) -> bool:
        """Indicates if the current block is an else block in an if/else statement chain.

        This property checks whether the current block represents an 'else' branch in a control flow statement. It helps in identifying and handling else
        blocks differently from if/elif blocks, particularly when manipulating control flow structures.

        Returns:
            bool: True if the current block is an else block, False otherwise.
        """

    @property
    @abstractmethod
    def is_elif_statement(self) -> bool:
        """Indicates whether the current block is an elif block.

        A property that returns True if the current instance of IfBlockStatement is specifically an elif block, False for if or else blocks.

        Returns:
            bool: True if the current block is an elif block, False for if or else blocks.
        """

    @property
    @reader
    def alternative_blocks(self) -> list[TIfBlockStatement]:
        """Returns a list of alternative if/elif/else blocks for the current block.

        Gets the alternative blocks (elif/else blocks) based on the type of the current block:
        - For if blocks: returns all alternative blocks
        - For else blocks: returns empty list
        - For elif blocks: returns all subsequent alternative blocks in the main if block

        Returns:
            list[TIfBlockStatement]: A list of alternative if/elif/else blocks that are executed if the condition is False.
        """
        if self.is_if_statement:
            return self._alternative_blocks
        if self.is_else_statement:
            return []
        return [x for x in self._main_if_block.alternative_blocks if x.start_byte > self.start_byte]

    @proxy_property
    @reader
    def elif_statements(self) -> list[TIfBlockStatement]:
        """Returns all elif blocks within the if block.

        Gets all alternative blocks that are specifically elif blocks (i.e., excluding else blocks) from an if statement. Can be called on any if/elif/else block to get subsequent elif blocks.

        Note:
        This method can be called as both a property and a method. If used as a property, it is equivalent to invoking it without arguments.

        Returns:
            list[TIfBlockStatement]: A list of elif block statements. Empty list if no elif blocks exist.
        """
        return [alt for alt in self.alternative_blocks if alt.is_elif_statement]

    @property
    @reader
    def else_statement(self) -> TIfBlockStatement | None:
        """Returns the else block within the if-statement.

        Gets the else block from the if-statement's alternative blocks if one exists. Only returns the else block, not elif blocks.

        Returns:
            TIfBlockStatement | None: The else block statement if it exists, None otherwise.
        """
        return next((alt for alt in self.alternative_blocks if alt.is_else_statement), None)

    @abstractmethod
    def _else_if_to_if(self) -> None:
        """Converts an elif block to an if block."""

    @writer
    def reduce_condition(self, bool_condition: bool, node: Editable | None = None) -> None:
        """Simplifies a conditional block by reducing its condition to a boolean value.

        This method modifies the if/elif/else block structure based on the provided boolean value.
        When reducing to True, it unwraps the consequence block and adjusts subsequent elif/else blocks.
        When reducing to False, it handles different cases for elif statements and main if blocks.

        Args:
            bool_condition (bool): The boolean value to reduce the condition to.
                If True, unwraps the consequence block and adjusts alternative blocks.
                If False, removes or modifies the current block based on its type.

        Returns:
            None

        Raises:
            ValueError: If attempting to reduce a condition on an IfBlockStatement that doesn't have a condition
                (like an else block).
        """
        if self.condition is None:
            msg = "Cannot reduce condition of an IfBlockStatement without a condition."
            raise ValueError(msg)

        first_elif = next((x for x in self.elif_statements()), None)

        # ==== [ Reduce condition to True ] ====
        if bool_condition:
            # If condition is reduced to True, unwrap the consequence block.
            # If the first alternative block is an elif block, change the elif to if.
            # If the first alternative block is else, remove the else block.
            self.consequence_block.unwrap()
            if first_elif:
                first_elif._else_if_to_if()
            elif (else_block := self.else_statement) is not None:
                remove_start = self.consequence_block._get_line_ends()[-1].end_byte
                else_block.remove_byte_range(remove_start, else_block.end_byte)

            # If the last statement in the consequence block is a return statement, remove all the lines after it.
            if isinstance(self.parent, Function):
                last_statement = self.consequence_block.get_statements(max_level=self.consequence_block.level)[-1]
                if last_statement.statement_type == StatementType.RETURN_STATEMENT:
                    self.consequence_block.remove_byte_range(last_statement.end_byte, self.parent.end_byte)

        # ==== [ Reduce condition to False ] ====
        elif self.is_elif_statement:
            # If the current block is an elif block, remove the elif block and nothing else.
            remove_end_byte = first_elif.start_byte if first_elif else self.ts_node.end_byte
            self.remove_byte_range(self.ts_node.start_byte, remove_end_byte)
        else:
            # ==== [ Main block ] ====
            # If condition is reduced to False, remove the if block.
            # If the first alternative block is an elif block, change the elif to else.
            # If the first alternative block is else, unwrap the else block.
            if first_elif:
                self.remove_byte_range(self.ts_node.start_byte, first_elif.start_byte)
                first_elif._else_if_to_if()
            elif (else_block := self.else_statement) is not None:
                else_block.consequence_block.unwrap()
                remove_end = else_block.consequence_block._get_line_starts()[0].start_byte
                self.remove_byte_range(self.ts_node.start_byte, remove_end)
            else:
                self.remove()

    @property
    @noapidoc
    def other_possible_blocks(self) -> Sequence[ConditionalBlock]:
        if self.is_if_statement:
            return self.alternative_blocks
        elif self.is_elif_statement:
            main = self._main_if_block
            statements = [main]
            if main.else_statement:
                statements.append(main.else_statement)
            for statement in main.elif_statements:
                if statement != self:
                    statements.append(statement)
            return statements
        else:
            main = self._main_if_block
            return [main, *main.elif_statements]

    @property
    @noapidoc
    def end_byte_for_condition_block(self) -> int:
        if self.is_if_statement:
            return self.consequence_block.end_byte
        return self.end_byte

    @property
    @noapidoc
    def start_byte_for_condition_block(self) -> int:
        if self.is_if_statement:
            return self.consequence_block.start_byte
        return self.start_byte
