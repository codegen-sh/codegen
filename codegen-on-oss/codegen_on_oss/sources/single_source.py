from collections.abc import Iterator
from typing import TYPE_CHECKING, ClassVar

from github import Github  # nosemgrep

from .base import RepoSource, SourceSettings


class SingleSettings(SourceSettings, env_prefix="SINGLE_"):
    """
    Settings for the Single source.
    """

    url: str
    commit: str | None = None


class SingleSource(RepoSource[SingleSettings]):
    """
    Source for a single repository.
    """

    if TYPE_CHECKING:
        github_client: Github
        settings: SingleSettings

    source_type: ClassVar[str] = "single"
    settings_cls: ClassVar[type[SingleSettings]] = SingleSettings

    def __iter__(self) -> Iterator[tuple[str, str | None]]:
        yield self.settings.url, self.settings.commit
