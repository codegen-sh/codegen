import shutil
from pathlib import Path

from rich.status import Status


def populate_api_docs(dest: Path, api_docs: dict[str, str], status: Status) -> None:
    """Writes all API docs to the docs folder"""
    status.update("Populating API documentation...")
    # Remove existing docs
    shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir(parents=True, exist_ok=True)

    # Populate docs
    for file, content in api_docs.items():
        dest_file = dest / file
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        dest_file.write_text(content)
