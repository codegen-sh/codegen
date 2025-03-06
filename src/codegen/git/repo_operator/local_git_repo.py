import os
from functools import cached_property
from pathlib import Path

import giturlparse
from git import Repo
from git.remote import Remote

from codegen.configs.models.repository import RepositoryConfig
from codegen.git.clients.git_repo_client import GitRepoClient
from codegen.git.utils.language import determine_project_language


# TODO: merge this with RepoOperator
class LocalGitRepo:
    repo_path: Path

    def __init__(self, repo_path: Path):
        self.repo_path = repo_path

    @cached_property
    def git_cli(self) -> Repo:
        if not os.path.exists(self.repo_path):
            os.makedirs(self.repo_path)
            return Repo.init(self.repo_path)
        else:
            return Repo(self.repo_path)

    @cached_property
    def name(self) -> str:
        return os.path.basename(self.repo_path)

    @cached_property
    def owner(self) -> str | None:
        if not self.origin_remote:
            return None

        parsed = giturlparse.parse(self.origin_remote.url)
        return parsed.owner

    @cached_property
    def full_name(self) -> str | None:
        if not self.origin_remote:
            return None

        parsed = giturlparse.parse(self.origin_remote.url)
        return f"{parsed.owner}/{parsed.name}"

    @cached_property
    def origin_remote(self) -> Remote | None:
        """Returns the url of the first remote found on the repo, or None if no remotes are set"""
        if self.has_remote():
            return self.git_cli.remote("origin")
        return None

    @cached_property
    def base_url(self) -> str | None:
        if self.origin_remote:
            return self.origin_remote.url
        return None

    @property
    def user_name(self) -> str | None:
        with self.git_cli.config_reader() as reader:
            if reader.has_option("user", "name"):
                return reader.get("user", "name")
        return None

    @property
    def user_email(self) -> str | None:
        with self.git_cli.config_reader() as reader:
            if reader.has_option("user", "email"):
                return reader.get("user", "email")
        return None

    def get_language(self, access_token: str | None = None) -> str:
        """Returns the majority language of the repository"""
        if access_token is not None:
            remote_git = GitRepoClient(repo_full_name=self.full_name, access_token=access_token)
            if (language := remote_git.repo.language) is not None:
                return language.upper()

        return str(determine_project_language(str(self.repo_path)))

    def has_remote(self) -> bool:
        return bool(self.git_cli.remotes)

    def get_repo_config(self, access_token: str | None = None, repo_config: RepositoryConfig | None = None) -> RepositoryConfig:
        config = repo_config or RepositoryConfig()
        config.path = config.path or str(self.repo_path)
        config.owner = config.owner or self.owner
        config.user_name = config.user_name or self.user_name
        config.user_email = config.user_email or self.user_email
        config.language = config.language or self.get_language(access_token=access_token).upper()
        return config
