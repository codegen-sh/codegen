from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.codebase.codebase_context import CodebaseContext


class ConfigParser(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def parse_configs(self, codebase_context: "CodebaseContext"): ...


def get_config_parser_for_language(language: ProgrammingLanguage, codebase_context: "CodebaseContext") -> ConfigParser | None:
    from codegen.sdk.typescript.config_parser import TSConfigParser

    if language == ProgrammingLanguage.TYPESCRIPT:
        return TSConfigParser(codebase_context)

    return None
