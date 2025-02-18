from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from codegen.sdk.core.interfaces.editable import Editable
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.core.codebase import Codebase


class Plugin(ABC):
    language: ProgrammingLanguage

    @abstractmethod
    def execute(self, codebase: "Codebase"): ...
    def register_api(self, method: str, label: str, node: Editable):
        pass
