from abc import abstractmethod
from typing import TYPE_CHECKING

from codegen.sdk.core.external.external_process import ExternalProcess
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.codebase.codebase_context import CodebaseContext


class DependencyManager(ExternalProcess):
    """Manages dependencies for the given repository.

    Handles reading, installing, and managing any dependency-based operations.
    """

    @abstractmethod
    def parse_dependencies(self):
        pass

    @abstractmethod
    def install_dependencies(self):
        pass

    @abstractmethod
    def remove_dependencies(self):
        pass


def get_dependency_manager(language: ProgrammingLanguage, codebase_context: "CodebaseContext", enabled: bool = False) -> DependencyManager | None:
    from codegen.sdk.typescript.external.dependency_manager import TypescriptDependencyManager

    ts_enabled = enabled or codebase_context.config.ts_dependency_manager
    if language == ProgrammingLanguage.TYPESCRIPT:
        if ts_enabled:
            return TypescriptDependencyManager(repo_path=codebase_context.repo_path, base_path=codebase_context.projects[0].base_path)

    return None
