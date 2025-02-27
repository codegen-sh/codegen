from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from codegen.sdk.codebase.io.io import IO, BadWriteError
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class FileIO(IO):
    """IO implementation that writes files to disk, and tracks pending changes."""

    files: dict[Path, bytes]

    def __init__(self):
        self.files = {}

    def write_bytes(self, path: Path, content: bytes) -> None:
        self.files[path] = content

    def read_bytes(self, path: Path) -> bytes:
        if path in self.files:
            return self.files[path]
        else:
            return path.read_bytes()

    def save_files(self, files: set[Path] | None = None) -> None:
        to_save = set(filter(lambda f: f in files, self.files)) if files is not None else self.files.keys()
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
        self.untrack_file(path)
        if path.exists():
            path.unlink()

    def untrack_file(self, path: Path) -> None:
        self.files.pop(path, None)

    def file_exists(self, path: Path) -> bool:
        return path.exists()
