from pathlib import Path

import rich
import typer

from codegen.cli.auth.session import CodegenSession
from codegen.cli.rich.codeblocks import format_command
from codegen.shared.path import get_git_root_path


def init(
    path: str | None = typer.Option(None, help="Path within a git repository. Defaults to the current directory."),
    token: str | None = typer.Option(None, help="Access token for the git repository. Required for full functionality."),
    language: str | None = typer.Option(None, help="Override automatic language detection (python or typescript)"),
    fetch_docs: bool = typer.Option(False, "--fetch-docs", help="Fetch docs and examples (requires auth)"),
):
    """Initialize or update the Codegen folder."""
    # Validate language option
    if language and language.lower() not in ["python", "typescript"]:
        rich.print(f"[bold red]Error:[/bold red] Invalid language '{language}'. Must be 'python' or 'typescript'.")
        raise typer.Exit(1)

    # Print a message if not in a git repo
    path_obj = Path.cwd() if path is None else Path(path)
    repo_path = get_git_root_path(path_obj)
    rich.print(f"Found git repository at: {repo_path}")

    if repo_path is None:
        rich.print(f"\n[bold red]Error:[/bold red] Path={path_obj} is not in a git repository")
        rich.print("[white]Please run this command from within a git repository.[/white]")
        rich.print("\n[dim]To initialize a new git repository:[/dim]")
        rich.print(format_command("git init"))
        rich.print(format_command("codegen init"))
        raise typer.Exit(1)

    # At this point, repo_path is guaranteed to be not None
    assert repo_path is not None
    session = CodegenSession(repo_path=repo_path, git_token=token)
    if language:
        session.config.repository.language = language.upper()
        session.config.save()

    action = "Updating" if session.existing else "Initializing"

    # Create the codegen directory
    codegen_dir = session.codegen_dir
    codegen_dir.mkdir(parents=True, exist_ok=True)

    # Print success message
    rich.print(f"✅ {action} complete\n")
    rich.print(f"Codegen workspace initialized at: [bold]{codegen_dir}[/bold]")

    # Print next steps
    rich.print("\n[bold]What's next?[/bold]\n")
    rich.print("1. Create a function:")
    rich.print(format_command('codegen create my-function . -d "describe what you want to do"'))
    rich.print("2. Run it:")
    rich.print(format_command("codegen run my-function --apply-local"))
