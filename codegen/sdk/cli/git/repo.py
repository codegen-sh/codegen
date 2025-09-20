import os
from pathlib import Path

from pygit2.repository import Repository

from codegen.sdk.cli.git.folder import get_git_folder


# TODO: move to codegen.sdk.git module
def get_git_repo(path: os.PathLike | None = None) -> Repository | None:
    if path is None:
        path = Path.cwd()
    git_folder = get_git_folder(path)
    if git_folder is None:
        return None
    return Repository(str(git_folder))
