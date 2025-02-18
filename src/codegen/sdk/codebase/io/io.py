from abc import ABC, abstractmethod
from pathlib import Path


class BadWriteError(Exception):
    pass


class IO(ABC):
    def write_file(self, path: Path, content: str | bytes | None) -> None:
        if content is None:
            self.untrack_file(path)
        elif isinstance(content, str):
            self.write_text(path, content)
        else:
            self.write_bytes(path, content)

    def write_text(self, path: Path, content: str) -> None:
        self.write_bytes(path, content.encode("utf-8"))

    @abstractmethod
    def write_bytes(self, path: Path, content: bytes) -> None:
        pass

    @abstractmethod
    def read_bytes(self, path: Path) -> bytes:
        pass

    def read_text(self, path: Path) -> str:
        return self.read_bytes(path).decode("utf-8")

    @abstractmethod
    def save_files(self, files: set[Path] | None = None) -> None:
        pass

    @abstractmethod
    def check_changes(self) -> None:
        pass

    @abstractmethod
    def delete_file(self, path: Path) -> None:
        pass

    @abstractmethod
    def file_exists(self, path: Path) -> bool:
        pass
