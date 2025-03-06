import os
from pathlib import Path
from typing import Self

from codegen.configs.models.base_config import BaseConfig


class RepositoryConfig(BaseConfig):
    """Configuration for the repository context to run codegen.
    To automatically populate this config, call `codegen init` from within a git repository.
    """

    path: str | None = None
    owner: str | None = None
    language: str | None = None
    user_name: str | None = None
    user_email: str | None = None
    subdirectories: list[str] | None = None
    base_path: str | None = None  # root module of the parsed codebase

    def __init__(self, prefix: str = "REPOSITORY", *args, **kwargs) -> None:
        super().__init__(prefix=prefix, *args, **kwargs)

    @classmethod
    def from_path(cls, path: str) -> Self:
        return cls(root_path=Path(path), path=str(path))

    @property
    def base_dir(self) -> str:
        return os.path.dirname(self.path)

    @property
    def name(self) -> str:
        return os.path.basename(self.path)

    @property
    def full_name(self) -> str | None:
        if self.owner is not None:
            return f"{self.owner}/{self.name}"
        return None
