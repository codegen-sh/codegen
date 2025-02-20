from pathlib import Path

import rich
from rich.panel import Panel
from rich.status import Status

from codegen.cli.auth.session import CodegenSession
from codegen.cli.utils.function_finder import DecoratedFunction
from codegen.sdk.core.codebase import Codebase


def parse_codebase(repo_root: Path) -> Codebase:
    """Parse the codebase at the given root.

    Args:
        repo_root: Path to the repository root

    Returns:
        Parsed Codebase object
    """
    codebase = Codebase(repo_root)
    return codebase


def run_local(
    session: CodegenSession,
    function: DecoratedFunction,
    diff_preview: int | None = None,
) -> None:
    """Run a function locally against the codebase.

    Args:
        session: The current codegen session
        function: The function to run
        diff_preview: Number of lines of diff to preview (None for all)
    """
    # Parse codebase and run
    repo_root = session.repo_path

    with Status("[bold]Parsing codebase...", spinner="dots") as status:
        codebase = parse_codebase(repo_root)
        status.update("[bold green]✓ Parsed codebase")

        status.update("[bold]Running codemod...")
        function.run(codebase)  # Run the function
        status.update("[bold green]✓ Completed codemod")

    # Get the diff from the codebase
    result = codebase.get_diff()

    # Handle no changes case
    if not result:
        rich.print("\n[yellow]No changes were produced by this codemod[/yellow]")
        return

    # Show diff preview if requested
    if diff_preview:
        rich.print("")  # Add spacing
        diff_lines = result.splitlines()
        truncated = len(diff_lines) > diff_preview
        limited_diff = "\n".join(diff_lines[:diff_preview])

        if truncated:
            limited_diff += f"\n\n...\n\n[yellow]diff truncated to {diff_preview} lines[/yellow]"

        panel = Panel(limited_diff, title="[bold]Diff Preview[/bold]", border_style="blue", padding=(1, 2), expand=False)
        rich.print(panel)

    # Apply changes
    rich.print("")
    rich.print("[green]✓ Changes have been applied to your local filesystem[/green]")
