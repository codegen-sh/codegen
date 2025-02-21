import os
from typing import Self

from pydantic import BaseModel
from pydantic.config import ConfigDict
from pydantic.fields import Field

from codegen.configs.models.codebase import DefaultCodebaseConfig
from codegen.git.repo_operator.repo_operator import RepoOperator
from codegen.git.schemas.repo_config import RepoConfig
from codegen.git.utils.file_utils import split_git_path
from codegen.git.utils.language import determine_project_language
from codegen.shared.enums.programming_language import ProgrammingLanguage

HARD_MAX_AI_LIMIT = 500  # Global limit for AI requests


class SessionOptions(BaseModel):
    """Options for a session. A session is a single codemod run."""

    model_config = ConfigDict(frozen=True)
    max_seconds: int | None = None
    max_transactions: int | None = None
    max_ai_requests: int = Field(default=150, le=HARD_MAX_AI_LIMIT)


TestFlags = DefaultCodebaseConfig.model_copy(update=dict(debug=True, track_graph=True, verify_graph=True, full_range_index=True, sync_enabled=True))
LintFlags = DefaultCodebaseConfig.model_copy(update=dict(method_usages=False, sync_enabled=True))
ParseTestFlags = DefaultCodebaseConfig.model_copy(update=dict(debug=False, track_graph=False, sync_enabled=True))


class ProjectConfig(BaseModel):
    """Context for a codebase. A codebase is a set of files in a directory."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)
    repo_operator: RepoOperator

    # TODO: clean up these fields. Duplicated across RepoConfig and CodebaseContext
    base_path: str | None = None
    subdirectories: list[str] | None = None
    programming_language: ProgrammingLanguage = ProgrammingLanguage.PYTHON

    @classmethod
    def from_path(cls, path: str, programming_language: ProgrammingLanguage | None = None) -> Self:
        # Split repo_path into (git_root, base_path)
        repo_path = os.path.abspath(path)
        git_root, base_path = split_git_path(repo_path)
        subdirectories = [base_path] if base_path else None
        programming_language = programming_language or determine_project_language(repo_path)
        repo_config = RepoConfig.from_repo_path(repo_path=git_root)
        repo_config.language = programming_language
        repo_config.subdirectories = subdirectories
        # Create main project
        return cls(
            repo_operator=RepoOperator(repo_config=repo_config),
            programming_language=programming_language,
            base_path=base_path,
            subdirectories=subdirectories,
        )

    @classmethod
    def from_repo_operator(cls, repo_operator: RepoOperator, programming_language: ProgrammingLanguage | None = None, base_path: str | None = None) -> Self:
        return cls(
            repo_operator=repo_operator,
            programming_language=programming_language or determine_project_language(repo_operator.repo_path),
            base_path=base_path,
            subdirectories=[base_path] if base_path else None,
        )
