import rich
from pygit2 import Diff
from pygit2.repository import Repository
from rich.status import Status


def apply_patch(git_repo: Repository, patch: str):
    """Apply a git patch to the repository.

    Args:
        git_repo: The repository to apply the patch to
        patch: A string containing the git patch/diff

    """
    # Parse the entire patch into a Diff object
    diff_patch = Diff.parse_diff(patch)
    total_files = len(list(diff_patch))
    error_count = 0

    status = Status(f"[cyan]Applying patch to {total_files} files...[/cyan]", spinner="dots")
    status.start()

    # Apply each file's changes individually
    for idx, patch_file in enumerate(diff_patch, 1):
        try:
            status.update(f"[cyan]Applying patch [{idx}/{total_files}]: {patch_file.delta.new_file.path}[/cyan]")
            # Create a new diff containing just this file's changes
            file_diff = Diff.parse_diff(patch_file.data)
            # Apply the individual file changes
            git_repo.apply(file_diff)
        except Exception as e:
            error_count += 1
            rich.print(f"[red]✗[/red] Error applying patch to {patch_file.delta.new_file.path}: {e!s}")

    status.stop()

    # Display summary
    if error_count == 0:
        rich.print(f"[green]✓ Successfully applied patch to all {total_files} files[/green]")
    else:
        rich.print(f"[yellow]⚠ Applied patch with {error_count} error{'s' if error_count > 1 else ''} out of {total_files} files[/yellow]")
