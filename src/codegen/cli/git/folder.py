import os
from pathlib import Path


# TODO: move to codegen.git module
def get_git_folder(path: os.PathLike | None = None) -> Path | None:
    if path is None:
        path = Path.cwd()
    path = Path(path)
    while path != path.root:
        if (path / ".git").exists():
            return path
        path = path.parent
    return None
