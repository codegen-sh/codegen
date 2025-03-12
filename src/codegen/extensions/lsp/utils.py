from pathlib import Path

from pygls.uris import to_fs_path


def get_path(uri: str) -> Path:
    return Path(to_fs_path(uri)).absolute()
