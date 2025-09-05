from pathlib import Path

import click
from pygit2.enums import FileStatus, ResetMode
from pygit2.repository import Repository

from codegen.sdk.cli.auth.constants import CODEGEN_DIR
from codegen.sdk.cli.git.repo import get_git_repo


def is_codegen_file(filepath: Path) -> bool:
    """Check if a file is in the .codegen directory."""
    return CODEGEN_DIR in filepath.parents


def backup_codegen_files(repo: Repository) -> dict[str, tuple[bytes | None, bool]]:
    """Backup .codegen files and track if they were staged.

    Returns:
        Dict mapping filepath to (content, was_staged) tuple.
        content is None for deleted files.
    """
    codegen_changes = {}
    for filepath, status in repo.status().items():
        if not is_codegen_file(Path(filepath)):
            continue

        was_staged = bool(status & (FileStatus.INDEX_MODIFIED | FileStatus.INDEX_NEW | FileStatus.INDEX_DELETED | FileStatus.INDEX_RENAMED))

        # Handle deleted files
        if status & (FileStatus.WT_DELETED | FileStatus.INDEX_DELETED):
            codegen_changes[filepath] = (None, was_staged)
            continue
        # Handle modified, new, or renamed files
        if status & (FileStatus.WT_MODIFIED | FileStatus.WT_NEW | FileStatus.INDEX_MODIFIED | FileStatus.INDEX_NEW | FileStatus.INDEX_RENAMED):
            file_path = Path(repo.workdir) / filepath
            if file_path.exists():  # Only read if file exists
                codegen_changes[filepath] = (file_path.read_bytes(), was_staged)

    return codegen_changes


def restore_codegen_files(repo: Repository, codegen_changes: dict[str, tuple[bytes | None, bool]]) -> None:
    """Restore backed up .codegen files and their staged status."""
    for filepath, (content, was_staged) in codegen_changes.items():
        file_path = Path(repo.workdir) / filepath

        if content is None:  # Handle deleted files
            if file_path.exists():
                file_path.unlink()
            if was_staged:
                repo.index.remove(filepath)
        else:  # Handle existing files
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(content)
            if was_staged:
                repo.index.add(filepath)

    if codegen_changes:
        repo.index.write()


def remove_untracked_files(repo: Repository) -> None:
    """Remove untracked files except those in .codegen directory."""
    for filepath, status in repo.status().items():
        if not is_codegen_file(Path(filepath)) and status & FileStatus.WT_NEW:
            file_path = Path(repo.workdir) / filepath
            if file_path.exists():  # Only try to remove if file exists
                if file_path.is_file():
                    file_path.unlink()
                elif file_path.is_dir():
                    file_path.rmdir()


@click.command(name="reset")
def reset_command() -> None:
    """Reset git repository while preserving all files in .codegen directory"""
    repo = get_git_repo()
    if not repo:
        click.echo("Not a git repository", err=True)
        return

    try:
        # Backup .codegen files and their staged status
        codegen_changes = backup_codegen_files(repo)

        # Reset everything
        repo.reset(repo.head.target, ResetMode.HARD)

        # Restore .codegen files and their staged status
        restore_codegen_files(repo, codegen_changes)

        # Remove untracked files except .codegen
        remove_untracked_files(repo)

        click.echo(f"Reset complete. Repository has been restored to HEAD (preserving {CODEGEN_DIR}) and untracked files have been removed (except {CODEGEN_DIR})")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


if __name__ == "__main__":
    reset_command()
