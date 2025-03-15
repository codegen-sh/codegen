from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Generic, TypeVar, override

from codegen.sdk.core.interfaces.conditional_block import ConditionalBlock
from codegen.sdk.core.interfaces.has_block import HasBlock
from codegen.sdk.core.statements.block_statement import BlockStatement
from codegen.sdk.core.statements.statement import StatementType
from codegen.shared.decorators.docs import apidoc, noapidoc

if TYPE_CHECKING:
    from codegen.sdk.core.detached_symbols.code_block import CodeBlock


Parent = TypeVar("Parent", bound="CodeBlock")


@apidoc
class TryCatchStatement(ConditionalBlock, BlockStatement[Parent], HasBlock, ABC, Generic[Parent]):
    """Abstract representation of the try catch statement block.

    Attributes:
        code_block: The code block that may trigger an exception
        finalizer: The code block executed regardless of if an exception is thrown or not
    """

    statement_type = StatementType.TRY_CATCH_STATEMENT
    finalizer: BlockStatement | None = None

    @noapidoc
    @override
    def is_true_conditional(self, descendant) -> bool:
        if descendant.is_child_of(self.finalizer):
            return False
        return True

    @property
    @noapidoc
    def end_byte_for_condition_block(self) -> int:
        if self.code_block:
            return self.code_block.end_byte
        else:
            return self.end_byte

    @property
    @noapidoc
    def start_byte_for_condition_block(self) -> int:
        if self.code_block:
            return self.code_block.start_byte - 1
        else:
            return self.start_byte
