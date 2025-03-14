from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from codegen.sdk.codebase.io.io import IO, BadWriteError
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class FileIO(IO):
    """IO implementation that writes files to disk, and tracks pending changes."""

    files: dict[Path, bytes]
    allowed_paths: list[Path] | None

    def __init__(self, allowed_paths: list[Path] | None = None):
        self.files = {}
        self.allowed_paths = allowed_paths

    def _verify_path(self, path: Path) -> None:
        if self.allowed_paths is not None:
            if not any(path.resolve().is_relative_to(p.resolve()) for p in self.allowed_paths):
                msg = f"Path {path.resolve()} is not within allowed paths {self.allowed_paths}"
                raise BadWriteError(msg)

    def write_bytes(self, path: Path, content: bytes) -> None:
        self._verify_path(path)
        self.files[path] = content

    def read_bytes(self, path: Path) -> bytes:
        self._verify_path(path)
        if path in self.files:
            return self.files[path]
        else:
            return path.read_bytes()

    def save_files(self, files: set[Path] | None = None) -> None:
        to_save = set(filter(lambda f: f in files, self.files)) if files is not None else self.files.keys()
        for path in to_save:
            self._verify_path(path)
        with ThreadPoolExecutor() as exec:
            exec.map(lambda path: path.write_bytes(self.files[path]), to_save)
        if files is None:
            self.files.clear()
        else:
            for path in to_save:
                del self.files[path]

    def check_changes(self) -> None:
        if self.files:
            logger.error(BadWriteError("Directly called file write without calling commit_transactions"))
        self.files.clear()

    def delete_file(self, path: Path) -> None:
        self._verify_path(path)
        self.untrack_file(path)
        if path.exists():
            path.unlink()

    def untrack_file(self, path: Path) -> None:
        self._verify_path(path)
        self.files.pop(path, None)

    def file_exists(self, path: Path) -> bool:
        self._verify_path(path)
        return path.exists()
