from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from codegen.sdk.codebase.codebase_context import CodebaseContext


class Parseable(ABC):
    @abstractmethod
    def parse(self, ctx: "CodebaseContext") -> None:
        """Adds itself and its children to the codebase graph."""
