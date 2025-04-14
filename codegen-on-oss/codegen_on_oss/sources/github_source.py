from collections.abc import Iterator
from typing import TYPE_CHECKING, ClassVar, Literal

from github import Auth, Github  # nosemgrep

from .base import RepoSource, SourceSettings


class GithubSettings(SourceSettings, env_prefix="GITHUB_"):
    """
    Settings for the Github source.
    """

    language: Literal["python", "typescript"] = "python"
    heuristic: Literal[
        "stars",
        "forks",
        "updated",
        # "watchers",
        # "contributors",
        # "commit_activity",
        # "issues",
        # "dependency",
    ] = "stars"
    token: str | None = None
    num_repos: int = 50


class GithubSource(RepoSource[GithubSettings]):
    """
    Source for Github repositories via Github Search API
    """

    if TYPE_CHECKING:
        github_client: Github
        settings: GithubSettings

    source_type: ClassVar[str] = "github"
    settings_cls: ClassVar[type[GithubSettings]] = GithubSettings

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if self.settings.token is None:
            self.github_client = Github()
        else:
            self.github_client = Github(auth=Auth.Token(self.settings.token))

    def __iter__(self) -> Iterator[tuple[str, str | None]]:
        repositories = self.github_client.search_repositories(
            query=f"language:{self.settings.language}",
            sort=self.settings.heuristic,
            order="desc",
        )

        for idx, repository in enumerate(repositories):
            if idx >= self.settings.num_repos:
                break
            commit = repository.get_commits()[0]
            yield repository.clone_url, commit.sha
