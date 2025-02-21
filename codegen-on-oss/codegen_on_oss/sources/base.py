from collections.abc import Iterator
from typing import TYPE_CHECKING, ClassVar, Generic, TypeVar

from pydantic_settings import BaseSettings, SettingsConfigDict


class SourceSettings(BaseSettings):
    """
    SourceSettings is a class that contains the settings for a source.
    """

    model_config = SettingsConfigDict(env_prefix="SOURCE_")
    num_repos: int = 50


SettingsType = TypeVar("SettingsType", bound=SourceSettings)

all_sources: dict[str, type["RepoSource"]] = {}


class DuplicateSource(ValueError):
    """
    DuplicateSource is an error that occurs when a source type is defined twice.
    """

    def __init__(self, source_type: str) -> None:
        super().__init__(f"Source type {source_type} already exists")


class RepoSource(Generic[SettingsType]):
    """
    RepoSource is a class that contains the configuration for a source.
    """

    source_type: ClassVar[str]
    settings_cls: ClassVar[type[SourceSettings]]

    if TYPE_CHECKING:
        settings: SourceSettings

    def __init_subclass__(cls) -> None:
        if not hasattr(cls, "source_type"):
            raise NotImplementedError("source_type must be defined")

        if not hasattr(cls, "settings_cls"):
            raise NotImplementedError("settings_cls must be defined")

        if cls.source_type in all_sources:
            raise DuplicateSource(cls.source_type)
        all_sources[cls.source_type] = cls

    def __init__(self, settings: SourceSettings | None = None) -> None:
        self.settings = settings or self.settings_cls()

    @classmethod
    def from_source_type(
        cls, source_type: str, settings: SourceSettings | None = None
    ) -> "RepoSource":
        return all_sources[source_type](settings)

    def __iter__(self) -> Iterator[tuple[str, str | None]]:
        """
        Yields URL and optional commit hash of repositories.
        """
        raise NotImplementedError
