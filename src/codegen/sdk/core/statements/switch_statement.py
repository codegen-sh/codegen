from __future__ import annotations

from typing import TYPE_CHECKING, Generic, Self, TypeVar, override

from codegen.sdk.compiled.autocommit import commiter, reader
from codegen.sdk.core.statements.statement import Statement, StatementType
from codegen.sdk.shared.decorators.docs import apidoc, noapidoc

if TYPE_CHECKING:
    from codegen.sdk.core.dataclasses.usage import UsageKind
    from codegen.sdk.core.detached_symbols.code_block import CodeBlock
    from codegen.sdk.core.detached_symbols.function_call import FunctionCall
    from codegen.sdk.core.expressions import Expression
    from codegen.sdk.core.interfaces.has_name import HasName
    from codegen.sdk.core.interfaces.importable import Importable
    from codegen.sdk.core.statements.switch_case import SwitchCase


Parent = TypeVar("Parent", bound="CodeBlock")
TCodeBlock = TypeVar("TCodeBlock", bound="CodeBlock")
TSwitchCase = TypeVar("TSwitchCase", bound="SwitchCase")


@apidoc
class SwitchStatement(Statement[Parent], Generic[Parent, TCodeBlock, TSwitchCase]):
    """Abstract representation of the switch statement.

    Attributes:
        value: The value to switch on.
        cases: A list of switch cases.
    """

    statement_type = StatementType.SWITCH_STATEMENT
    value: Expression[Self]
    cases: list[TSwitchCase] = []

    @property
    @reader
    def function_calls(self) -> list[FunctionCall]:
        """Returns all function calls within the switch statement.

        Gets the function calls from the value expression and all switch cases.

        Returns:
            list[FunctionCall]: A list of all function calls found within the switch statement,
                including those in the value expression and all switch cases.
        """
        fcalls = self.value.function_calls
        for case in self.cases:
            fcalls.extend(case.function_calls)
        return fcalls

    @noapidoc
    @commiter
    def _compute_dependencies(self, usage_type: UsageKind | None = None, dest: HasName | None = None) -> None:
        self.value._compute_dependencies(usage_type, dest)
        for case in self.cases:
            case._compute_dependencies(usage_type, dest)

    @property
    @noapidoc
    def descendant_symbols(self) -> list[Importable]:
        symbols = self.value.descendant_symbols
        for case in self.cases:
            symbols.extend(case.descendant_symbols)
        return symbols

    @property
    @reader
    @override
    def nested_code_blocks(self) -> list[TCodeBlock]:
        """Returns all nested CodeBlocks within the switch statement.

        Gets all code blocks from the switch statement's cases. Only includes code blocks
        that are not None.

        Returns:
            list[TCodeBlock]: A list of code blocks from all cases in the switch statement.
        """
        nested_blocks = []
        for case in self.cases:
            if case.code_block:
                nested_blocks.append(case.code_block)
        return nested_blocks
