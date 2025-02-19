import csv
from collections.abc import Iterator
from pathlib import Path

from pydantic import field_validator

from .base import RepoSource, SourceSettings


class CSVInputSettings(SourceSettings, env_prefix="CSV_"):
    """
    CSVInputSettings is a class that contains the settings for a CSVInputSource.
    """

    file_path: Path = Path("input.csv")

    @field_validator("file_path", mode="after")
    def validate_file_path(cls, v):
        if not v.exists():
            msg = f"File {v} does not exist"
            raise ValueError(msg)
        return v


class CSVInputSource(RepoSource):
    """
    CSVInputSource is a source that reads URLs from a CSV file.
    """

    source_type = "csv"
    settings_cls = CSVInputSettings

    def __iter__(self) -> Iterator[tuple[str, str | None]]:
        with open(self.settings.file_path) as f:
            reader = csv.DictReader(f, fieldnames=["url", "commit_hash"])
            next(reader)

            for row in reader:
                yield row["url"], row.get("commit_hash") or None
