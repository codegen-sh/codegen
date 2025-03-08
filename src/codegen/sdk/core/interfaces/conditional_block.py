from abc import ABC, abstractmethod
from collections.abc import Sequence

from codegen.sdk.core.statements.statement import Statement


class ConditionalBlock(Statement, ABC):
    """An interface for any code block that might not be executed in the code, e.g if block/else block/try block/catch block ect."""

    @property
    @abstractmethod
    def other_possible_blocks(self) -> Sequence["ConditionalBlock"]:
        """Should return all other "branches" that might be executed instead."""

    @property
    def end_byte_for_condition_block(self) -> int:
        return self.end_byte
