import os
import subprocess
from pathlib import Path


def get_git_root_path(path: Path) -> Path | None:
    """Get the closest root of the git repository containing the given path"""
    try:
        os.chdir(path)
        output = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, check=True, text=True)
        return Path(output.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
